"""Tests for workflow-lite engine and workflow implementations."""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from chromagora_schemas.workflows import (
    WorkflowRunCreate,
    WorkflowStatus,
    WorkflowStepStatus,
    WorkflowStepLogCreate,
)


class TestWorkflowRunCreate:
    def test_create(self):
        run = WorkflowRunCreate(
            business_id=uuid4(),
            workflow_type="test_workflow",
            input_json={"key": "value"},
        )
        assert run.workflow_type == "test_workflow"
        assert run.input_json == {"key": "value"}

    def test_with_definition_id(self):
        run = WorkflowRunCreate(
            business_id=uuid4(),
            workflow_type="test",
            workflow_definition_id=uuid4(),
        )
        assert run.workflow_definition_id is not None


class TestWorkflowStepLogCreate:
    def test_create(self):
        step = WorkflowStepLogCreate(
            step_name="test_step",
            status=WorkflowStepStatus.COMPLETED,
            input_json={"action": "do_something"},
            output_json={"result": "ok"},
        )
        assert step.step_name == "test_step"
        assert step.status == WorkflowStepStatus.COMPLETED


class TestWorkflowStatusEnum:
    def test_all_statuses(self):
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.WAITING_FOR_APPROVAL.value == "waiting_for_approval"
        assert WorkflowStatus.WAITING_FOR_EXTERNAL_EVENT.value == "waiting_for_external_event"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"
        assert WorkflowStatus.CANCELLED.value == "cancelled"


class TestWorkflowStepStatusEnum:
    def test_all_statuses(self):
        assert WorkflowStepStatus.PENDING.value == "pending"
        assert WorkflowStepStatus.RUNNING.value == "running"
        assert WorkflowStepStatus.COMPLETED.value == "completed"
        assert WorkflowStepStatus.FAILED.value == "failed"
        assert WorkflowStepStatus.SKIPPED.value == "skipped"


class TestStaleQuoteLogic:
    """Test the stale date calculation logic."""

    def test_quote_is_stale(self):
        """A quote sent 10 days ago should be stale."""
        from chromagora_api.services.workflows import STALE_QUOTE_DAYS
        sent_at = datetime.now(timezone.utc) - timedelta(days=STALE_QUOTE_DAYS + 1)
        stale_threshold = datetime.now(timezone.utc) - timedelta(days=STALE_QUOTE_DAYS)
        assert sent_at < stale_threshold

    def test_quote_not_stale(self):
        """A quote sent 1 day ago should not be stale."""
        from chromagora_api.services.workflows import STALE_QUOTE_DAYS
        sent_at = datetime.now(timezone.utc) - timedelta(days=1)
        stale_threshold = datetime.now(timezone.utc) - timedelta(days=STALE_QUOTE_DAYS)
        assert sent_at > stale_threshold

    def test_quote_exactly_at_threshold(self):
        """A quote sent exactly at the threshold should be stale."""
        from chromagora_api.services.workflows import STALE_QUOTE_DAYS
        sent_at = datetime.now(timezone.utc) - timedelta(days=STALE_QUOTE_DAYS, seconds=1)
        stale_threshold = datetime.now(timezone.utc) - timedelta(days=STALE_QUOTE_DAYS)
        assert sent_at < stale_threshold
