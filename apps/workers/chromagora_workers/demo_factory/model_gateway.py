"""Model gateway for Demo Factory agent calls."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import httpx

from chromagora_api.services.runtime_utils import stable_json_hash


class DemoModelGatewayError(RuntimeError):
    """Base model gateway error."""


class DemoModelRateLimitError(DemoModelGatewayError):
    """Raised when a model provider returns a rate limit."""


class DemoModelTransientError(DemoModelGatewayError):
    """Raised for retryable provider/network failures."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_supabase():
    from chromagora_api.db.tenant import get_backend_supabase

    return get_backend_supabase()


def _project_context(sb, project_id: UUID) -> dict[str, Any]:
    resp = sb.table("demo_site_projects").select("*").eq("id", str(project_id)).execute()
    if not resp.data:
        raise DemoModelGatewayError(f"Project not found: {project_id}")
    return resp.data[0]


def _token_estimate(value: Any) -> int:
    return max(1, len(json.dumps(value, default=str)) // 4)


def _configured_provider() -> str:
    provider = os.getenv("DEMO_FACTORY_MODEL_PROVIDER", "").strip().lower()
    if provider:
        return provider
    if os.getenv("NVIDIA_API_KEY"):
        return "nvidia"
    if os.getenv("OPENROUTER_API_KEY"):
        return "openrouter"
    return "mock"


def _default_model(provider: str) -> str:
    if provider == "nvidia":
        return "stepfun-ai/step-3.7-flash"
    return "openrouter/owl-alpha"


def _mock_enabled() -> bool:
    provider = _configured_provider()
    if provider == "mock":
        return True
    if provider == "nvidia":
        return not bool(os.getenv("NVIDIA_API_KEY"))
    if provider == "openrouter":
        return not bool(os.getenv("OPENROUTER_API_KEY"))
    return False


def call_agent_model(
    agent_name: str,
    project_id: UUID,
    stage: str,
    system_instructions: str,
    context_packet: dict,
    output_schema: dict | None,
    temperature: float,
    max_tokens: int,
    timeout_seconds: int,
) -> dict:
    """Call one isolated agent model invocation and persist telemetry."""
    sb = _get_supabase()
    project = _project_context(sb, project_id)
    tenant_id = project["tenant_id"]
    batch_id = project.get("batch_id")
    agent_run_id = uuid4()
    provider = _configured_provider()
    primary_model = os.getenv("DEMO_FACTORY_PRIMARY_MODEL") or _default_model(provider)
    fallback_model = os.getenv("DEMO_FACTORY_FALLBACK_MODEL")
    max_attempts = max(1, int(os.getenv("DEMO_FACTORY_MODEL_MAX_ATTEMPTS", "2")))
    model = primary_model
    request_payload = {
        "agent_name": agent_name,
        "stage": stage,
        "provider": provider,
        "system_instructions": system_instructions,
        "context_packet": context_packet,
        "output_schema": output_schema,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "model": primary_model,
    }
    request_hash = stable_json_hash(request_payload)
    call_id = uuid4()
    started = time.monotonic()
    sb.table("agent_runs").insert(
        {
            "id": str(agent_run_id),
            "tenant_id": tenant_id,
            "business_id": project.get("business_id"),
            "agent_type": f"demo_factory.{agent_name}",
            "trigger_type": "demo_factory_stage",
            "status": "running",
            "input_json": {
                "stage": stage,
                "project_id": str(project_id),
                "request_hash": request_hash,
            },
            "context_packet_json": _compact_context_packet(context_packet),
            "trace_id": project.get("trace_id"),
            "model_name": primary_model,
        }
    ).execute()
    sb.table("demo_model_calls").insert(
        {
            "id": str(call_id),
            "tenant_id": tenant_id,
            "project_id": str(project_id),
            "batch_id": batch_id,
            "agent_run_id": str(agent_run_id),
            "agent_name": agent_name,
            "stage": stage,
            "model": primary_model,
            "request_hash": request_hash,
            "input_token_estimate": _token_estimate(context_packet) + _token_estimate(system_instructions),
            "output_token_estimate": max_tokens,
            "status": "running",
            "attempt_number": 1,
        }
    ).execute()

    try:
        if _mock_enabled():
            result = {
                "mock": True,
                "agent_name": agent_name,
                "stage": stage,
                "request_hash": request_hash,
                "content": {},
            }
            _mark_call_complete(sb, call_id, "succeeded", started, output=result)
            _mark_agent_run_complete(sb, agent_run_id, result, primary_model)
            return result

        last_error: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            model = fallback_model if attempt > 1 and fallback_model else primary_model
            try:
                sb.table("demo_model_calls").update({"attempt_number": attempt, "model": model}).eq(
                    "id", str(call_id)
                ).execute()
                result = _call_provider(
                    provider=provider,
                    model=model,
                    system_instructions=system_instructions,
                    context_packet=context_packet,
                    output_schema=output_schema,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout_seconds=timeout_seconds,
                )
                _mark_call_complete(sb, call_id, "succeeded", started, output=result)
                _mark_agent_run_complete(sb, agent_run_id, result, model)
                return result
            except DemoModelRateLimitError:
                raise
            except DemoModelTransientError as exc:
                last_error = exc
                if attempt >= max_attempts:
                    raise
                time.sleep(min(8, 2 * attempt))
            except DemoModelGatewayError as exc:
                last_error = exc
                if attempt >= max_attempts or not fallback_model:
                    raise
                time.sleep(min(8, 2 * attempt))
        raise last_error or DemoModelGatewayError("Model call failed")
    except DemoModelRateLimitError as exc:
        _mark_call_complete(sb, call_id, "rate_limited", started, http_status=429, error_message=str(exc))
        _mark_agent_run_failed(sb, agent_run_id, str(exc))
        raise
    except Exception as exc:
        _mark_call_complete(sb, call_id, "failed", started, error_message=str(exc))
        _mark_agent_run_failed(sb, agent_run_id, str(exc))
        raise


def _call_provider(
    *,
    provider: str,
    model: str,
    system_instructions: str,
    context_packet: dict,
    output_schema: dict | None,
    temperature: float,
    max_tokens: int,
    timeout_seconds: int,
) -> dict:
    if provider == "nvidia":
        return _call_nvidia(
            model=model,
            system_instructions=system_instructions,
            context_packet=context_packet,
            output_schema=output_schema,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
        )
    if provider == "openrouter":
        return _call_openrouter(
            model=model,
            system_instructions=system_instructions,
            context_packet=context_packet,
            output_schema=output_schema,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
        )
    raise DemoModelGatewayError(f"Unsupported Demo Factory model provider: {provider}")


def _schema_hint(output_schema: dict | None) -> str:
    if not output_schema:
        return ""
    return (
        "\nReturn only JSON matching this schema. Do not include markdown fences or commentary.\n"
        + json.dumps(output_schema, sort_keys=True, default=str)[:12000]
    )


def _messages(system_instructions: str, context_packet: dict, output_schema: dict | None) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_instructions + _schema_hint(output_schema)},
        {"role": "user", "content": json.dumps(context_packet, sort_keys=True, default=str)},
    ]


def _parse_provider_response(data: dict[str, Any], output_schema: dict | None) -> dict[str, Any]:
    message = data.get("choices", [{}])[0].get("message", {})
    content = message.get("content") or ""
    if not isinstance(content, str) or not content.strip():
        reasoning = message.get("reasoning_content") or message.get("reasoning") or ""
        if isinstance(reasoning, str) and reasoning.strip():
            content = reasoning
    if not isinstance(content, str) or not content.strip():
        raise DemoModelTransientError("Model provider returned an empty model message")
    if output_schema:
        try:
            return _parse_model_json(content)
        except json.JSONDecodeError as exc:
            raise DemoModelTransientError(f"Model did not return valid JSON: {exc}") from exc
    return {"content": content}


def _call_nvidia(
    *,
    model: str,
    system_instructions: str,
    context_packet: dict,
    output_schema: dict | None,
    temperature: float,
    max_tokens: int,
    timeout_seconds: int,
) -> dict:
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise DemoModelGatewayError("NVIDIA_API_KEY is not configured")

    payload: dict[str, Any] = {
        "model": model,
        "messages": _messages(system_instructions, context_packet, output_schema),
        "temperature": temperature,
        "top_p": float(os.getenv("DEMO_FACTORY_NVIDIA_TOP_P", "0.95")),
        "max_tokens": max_tokens,
        "stream": False,
    }
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(
                os.getenv(
                    "DEMO_FACTORY_NVIDIA_BASE_URL",
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                ),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except (httpx.TimeoutException, httpx.TransportError) as exc:
        raise DemoModelTransientError(str(exc)) from exc

    if response.status_code == 429:
        raise DemoModelRateLimitError(response.text[:2000])
    if response.status_code >= 500:
        raise DemoModelTransientError(f"NVIDIA transient error {response.status_code}: {response.text[:1000]}")
    if response.status_code == 400 and "DEGRADED" in response.text.upper():
        raise DemoModelTransientError(f"NVIDIA transient error {response.status_code}: {response.text[:1000]}")
    if response.status_code >= 400:
        raise DemoModelGatewayError(f"NVIDIA error {response.status_code}: {response.text[:1000]}")

    return _parse_provider_response(response.json(), output_schema)


def _call_openrouter(
    *,
    model: str,
    system_instructions: str,
    context_packet: dict,
    output_schema: dict | None,
    temperature: float,
    max_tokens: int,
    timeout_seconds: int,
) -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise DemoModelGatewayError("OPENROUTER_API_KEY is not configured")

    payload: dict[str, Any] = {
        "model": model,
        "messages": _messages(system_instructions, context_packet, output_schema),
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if output_schema:
        payload["response_format"] = {"type": "json_object"}

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": os.getenv("DEMO_FACTORY_OPENROUTER_REFERER", "https://chromagora.com"),
                    "X-Title": "Chromagora Demo Factory",
                },
                json=payload,
            )
    except (httpx.TimeoutException, httpx.TransportError) as exc:
        raise DemoModelTransientError(str(exc)) from exc

    if response.status_code == 429:
        raise DemoModelRateLimitError(response.text[:2000])
    if response.status_code >= 500:
        raise DemoModelTransientError(f"OpenRouter transient error {response.status_code}: {response.text[:1000]}")
    if response.status_code >= 400:
        raise DemoModelGatewayError(f"OpenRouter error {response.status_code}: {response.text[:1000]}")

    return _parse_provider_response(response.json(), output_schema)


def _parse_model_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    start = text.find("{")
    if start < 0:
        raise json.JSONDecodeError("No JSON object found", text, 0)
    depth = 0
    end = -1
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end < 0:
        raise json.JSONDecodeError("Unmatched braces", text, start)
    text = text[start : end + 1]
    return json.loads(text)


def _mark_call_complete(
    sb,
    call_id: UUID,
    status: str,
    started: float,
    output: dict | None = None,
    http_status: int | None = None,
    error_message: str | None = None,
) -> None:
    latency_ms = int((time.monotonic() - started) * 1000)
    update = {
        "status": status,
        "latency_ms": latency_ms,
        "http_status": http_status,
        "error_message": error_message[:2000] if error_message else None,
        "completed_at": _now(),
    }
    if output:
        update["output_token_estimate"] = _token_estimate(output)
    sb.table("demo_model_calls").update(update).eq("id", str(call_id)).execute()


def _mark_agent_run_complete(sb, agent_run_id: UUID, output: dict[str, Any], model_name: str) -> None:
    sb.table("agent_runs").update(
        {
            "status": "completed",
            "output_json": _compact_context_packet(output),
            "completed_at": _now(),
            "model_name": model_name,
        }
    ).eq("id", str(agent_run_id)).execute()


def _mark_agent_run_failed(sb, agent_run_id: UUID, error_message: str) -> None:
    sb.table("agent_runs").update(
        {
            "status": "failed",
            "error_message": error_message[:2000],
            "completed_at": _now(),
        }
    ).eq("id", str(agent_run_id)).execute()


def _compact_context_packet(value: Any, max_chars: int = 12000) -> Any:
    encoded = json.dumps(value, sort_keys=True, default=str)
    if len(encoded) <= max_chars:
        return value
    return {
        "truncated": True,
        "sha256": stable_json_hash(value),
        "preview": encoded[:max_chars],
    }
