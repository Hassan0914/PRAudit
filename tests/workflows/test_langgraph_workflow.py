"""Unit tests for Phase 18: LangGraph Review Workflow."""

from app.workflows.review_workflow import LangGraphReviewWorkflow


def test_langgraph_review_workflow_execution() -> None:
    """Test executing LangGraph StateGraph workflow."""
    workflow = LangGraphReviewWorkflow()
    state = workflow.execute_workflow("PR-WF-TEST", "Sample context text", "Sample diff text")

    assert state["pr_id"] == "PR-WF-TEST"
    assert state["status"] == "completed"
    assert len(state["execution_trace"]) > 0
    assert "build_context_node" in state["execution_trace"]
    assert "produce_review_node" in state["execution_trace"]
    assert state["final_review"] is not None
