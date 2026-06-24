"""Tests for Tactical Subagent v0."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from chromagora_api.services.tactical_subagent import (
    run_tactical_subagent,
    register_subagent_type,
    _default_handler,
)
from chromagora_schemas.spawn import SpawnContractCreate


class TestSpawnContractCreate:
    def test_defaults(self):
        contract = SpawnContractCreate(
            parent_agent_run_id=uuid4(),
            business_id=uuid4(),
            subagent_type="test",
            objective="Do something",
        )
        assert contract.max_side_effects == "none"
        assert contract.ttl_seconds == 300
        assert contract.authority_level == 1
        assert contract.memory_write_policy == "no_durable_write"
        assert contract.input_refs == []
        assert contract.allowed_tools == []

    def test_custom_values(self):
        contract = SpawnContractCreate(
            parent_agent_run_id=uuid4(),
            business_id=uuid4(),
            subagent_type="test",
            objective="Do something",
            max_side_effects="internal_only",
            ttl_seconds=600,
            authority_level=2,
            memory_write_policy="write_to_business_twin",
        )
        assert contract.max_side_effects == "internal_only"
        assert contract.ttl_seconds == 600
        assert contract.authority_level == 2


class TestRunTacticalSubagent:
    @patch("chromagora_api.services.tactical_subagent.start_agent_run")
    @patch("chromagora_api.services.tactical_subagent.build_context_packet", new_callable=AsyncMock)
    @patch("chromagora_api.services.tactical_subagent.complete_agent_run")
    def test_successful_run(
        self, mock_complete, mock_context, mock_start
    ):
        mock_start.return_value = MagicMock(id=uuid4())
        mock_context.return_value = MagicMock(packet_id=uuid4())
        mock_complete.return_value = MagicMock()

        contract = SpawnContractCreate(
            parent_agent_run_id=uuid4(),
            business_id=uuid4(),
            subagent_type="seo_gap_scout_mock",
            objective="Find SEO gaps",
        )

        result = run_tactical_subagent(
            tenant_id=uuid4(),
            contract=contract,
        )

        assert result["status"] == "completed"
        assert result["subagent_type"] == "seo_gap_scout_mock"
        mock_complete.assert_called_once()

    def test_missing_objective(self):
        contract = SpawnContractCreate(
            parent_agent_run_id=uuid4(),
            business_id=uuid4(),
            subagent_type="test",
            objective="",
        )

        result = run_tactical_subagent(
            tenant_id=uuid4(),
            contract=contract,
        )

        assert result["status"] == "failed"
        assert "objective" in result["error"]

    @patch("chromagora_api.services.tactical_subagent.start_agent_run")
    def test_agent_run_failure(self, mock_start):
        mock_start.return_value = None

        contract = SpawnContractCreate(
            parent_agent_run_id=uuid4(),
            business_id=uuid4(),
            subagent_type="test",
            objective="Test",
        )

        result = run_tactical_subagent(
            tenant_id=uuid4(),
            contract=contract,
        )

        assert result["status"] == "failed"

    @patch("chromagora_api.services.tactical_subagent.start_agent_run")
    @patch("chromagora_api.services.tactical_subagent.build_context_packet", new_callable=AsyncMock)
    @patch("chromagora_api.services.tactical_subagent.complete_agent_run")
    def test_none_side_effects_blocks_tools(
        self, mock_complete, mock_context, mock_start
    ):
        mock_start.return_value = MagicMock(id=uuid4())
        mock_context.return_value = MagicMock(packet_id=uuid4())
        mock_complete.return_value = MagicMock()

        contract = SpawnContractCreate(
            parent_agent_run_id=uuid4(),
            business_id=uuid4(),
            subagent_type="seo_gap_scout_mock",
            objective="Find gaps",
            max_side_effects="none",
        )

        result = run_tactical_subagent(
            tenant_id=uuid4(),
            contract=contract,
        )

        assert result["status"] == "completed"
        # When max_side_effects is "none", all tools should be forbidden
        assert "*" in contract.forbidden_tools


class TestDefaultHandler:
    def test_returns_message(self):
        contract = SpawnContractCreate(
            parent_agent_run_id=uuid4(),
            business_id=uuid4(),
            subagent_type="unknown_type",
            objective="Test",
        )
        result = _default_handler(contract, None)
        assert "No handler" in result["message"]
        assert result["objective"] == "Test"


class TestRegisterSubagentType:
    def test_register_and_use(self):
        handler = MagicMock(return_value={"result": "ok"})
        register_subagent_type("test_type", handler)

        contract = SpawnContractCreate(
            parent_agent_run_id=uuid4(),
            business_id=uuid4(),
            subagent_type="test_type",
            objective="Test",
        )

        with patch("chromagora_api.services.tactical_subagent.start_agent_run") as mock_start, \
             patch("chromagora_api.services.tactical_subagent.build_context_packet", new_callable=AsyncMock) as mock_ctx, \
             patch("chromagora_api.services.tactical_subagent.complete_agent_run"):
            mock_start.return_value = MagicMock(id=uuid4())
            mock_ctx.return_value = MagicMock(packet_id=uuid4())

            result = run_tactical_subagent(
                tenant_id=uuid4(),
                contract=contract,
            )

            handler.assert_called_once()
            assert result["status"] == "completed"
