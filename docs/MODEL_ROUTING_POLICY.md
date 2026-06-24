# Model Routing Policy

## Tier Assignments

| Tier | Model | Use Case | Cost |
|------|-------|----------|------|
| 0 | None | Deterministic code, no LLM | Free |
| 1 | gemma-4-26b-a4b-it:free | Classification, extraction, simple tasks | Free |
| 2 | qwen3-coder:free | Code generation, drafts, summaries | Free |
| 3 | nemotron-3-super-120b:free | Complex analysis, compliance, procurement | Free |
| 4 | Human | Binding decisions, level 6 actions | N/A |

## Escalation Rules

- **Low confidence** (< 0.5): Escalate one tier
- **Missing evidence**: Escalate one tier
- **High risk**: Escalate to tier 3 minimum
- **Compliance sensitive**: Minimum tier 3, escalate to human if binding
- **Dollar exposure > $5,000**: Escalate one tier
- **Dollar exposure > $10,000**: Escalate to tier 3

## Downgrade Rules

- **Deterministic tasks**: Always tier 0 (no model)
- **Simple classification**: Tier 1 maximum
- **Customer-facing drafts**: Tier 2 minimum
- **Never downgrade compliance-sensitive tasks**

## Free Models Only

All models use the `:free` suffix on OpenRouter. Never pay for models.
If a free model is unavailable, escalate to human rather than pay.

## Code Constants

```python
MODEL_TIER_MAP = {
    1: "openrouter/google/gemma-4-26b-a4b-it:free",
    2: "openrouter/qwen/qwen3-coder:free",
    3: "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
}

LOW_CONFIDENCE_THRESHOLD = 0.5
PROCUREMENT_DOLLAR_THRESHOLD = 5000
NEGOTIATION_DOLLAR_THRESHOLD = 10000
COMPLIANCE_DOLLAR_THRESHOLD = 1000
```
