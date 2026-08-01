"""LangGraph workflow orchestrator constructing fan-out StateGraph workflows."""

from typing import Any, Dict
from langgraph.graph import END, START, StateGraph

from app.core.logging import setup_logger
from app.workflows.models import WorkflowState
from app.workflows.nodes import (
    aggregate_results_node,
    analyze_architecture_node,
    analyze_maintainability_node,
    analyze_performance_node,
    analyze_security_node,
    build_context_node,
    produce_review_node,
    resolve_conflicts_node,
)

logger = setup_logger("workflows.review_workflow")


class LangGraphReviewWorkflow:
    """LangGraph review workflow coordinator."""

    def __init__(self) -> None:
        """Initialize and compile the LangGraph StateGraph."""
        self.app = self._build_graph()

    def _build_graph(self) -> Any:
        """Construct StateGraph with parallel analysis nodes."""
        builder = StateGraph(WorkflowState)

        builder.add_node("BuildContext", build_context_node)
        builder.add_node("AnalyzeArchitecture", analyze_architecture_node)
        builder.add_node("AnalyzePerformance", analyze_performance_node)
        builder.add_node("AnalyzeSecurity", analyze_security_node)
        builder.add_node("AnalyzeMaintainability", analyze_maintainability_node)
        builder.add_node("AggregateResults", aggregate_results_node)
        builder.add_node("ResolveConflicts", resolve_conflicts_node)
        builder.add_node("ProduceReview", produce_review_node)

        # Entry edge
        builder.add_edge(START, "BuildContext")

        # Parallel fan-out from BuildContext to domain nodes
        builder.add_edge("BuildContext", "AnalyzeArchitecture")
        builder.add_edge("BuildContext", "AnalyzePerformance")
        builder.add_edge("BuildContext", "AnalyzeSecurity")
        builder.add_edge("BuildContext", "AnalyzeMaintainability")

        # Fan-in from domain nodes to AggregateResults
        builder.add_edge("AnalyzeArchitecture", "AggregateResults")
        builder.add_edge("AnalyzePerformance", "AggregateResults")
        builder.add_edge("AnalyzeSecurity", "AggregateResults")
        builder.add_edge("AnalyzeMaintainability", "AggregateResults")

        builder.add_edge("AggregateResults", "ResolveConflicts")
        builder.add_edge("ResolveConflicts", "ProduceReview")
        builder.add_edge("ProduceReview", END)

        return builder.compile()

    def execute_workflow(self, pr_id: str, context_text: str, diff_text: str) -> WorkflowState:
        """Execute the state graph workflow.

        Args:
            pr_id: Target PR ID string.
            context_text: Assembled context text.
            diff_text: Pull Request diff text.

        Returns:
            Final WorkflowState dictionary.
        """
        logger.info("Executing LangGraph review workflow for PR %s", pr_id)
        initial_state: WorkflowState = {
            "pr_id": pr_id,
            "context_text": context_text,
            "diff_text": diff_text,
            "architecture_findings": [],
            "performance_findings": [],
            "security_findings": [],
            "maintainability_findings": [],
            "aggregated_findings": [],
            "final_review": None,
            "execution_trace": [],
            "status": "initialized",
        }

        final_state = self.app.invoke(initial_state)
        logger.info("LangGraph workflow completed for PR %s (Steps: %d)", pr_id, len(final_state.get("execution_trace", [])))
        return final_state
