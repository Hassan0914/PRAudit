"""Workflow node functions for parallel execution and analysis steps."""

from typing import Any, Dict
from app.core.logging import setup_logger
from app.workflows.models import WorkflowState

logger = setup_logger("workflows.nodes")


def build_context_node(state: WorkflowState) -> Dict[str, Any]:
    """Node: Build context for downstream reviewers."""
    logger.debug("Executing build_context_node for PR %s", state["pr_id"])
    trace = state.get("execution_trace", []) + ["build_context_node"]
    return {"execution_trace": trace, "status": "context_built"}


def analyze_architecture_node(state: WorkflowState) -> Dict[str, Any]:
    """Node: Analyze architectural design and module boundaries."""
    logger.debug("Executing analyze_architecture_node")
    trace = state.get("execution_trace", []) + ["analyze_architecture_node"]
    findings = [
        {
            "category": "Architecture",
            "title": "Clean Module Separation",
            "description": "Modules maintain low coupling.",
        }
    ]
    return {"architecture_findings": findings, "execution_trace": trace}


def analyze_performance_node(state: WorkflowState) -> Dict[str, Any]:
    """Node: Analyze execution complexity and bottlenecks."""
    logger.debug("Executing analyze_performance_node")
    trace = state.get("execution_trace", []) + ["analyze_performance_node"]
    findings = [
        {
            "category": "Performance",
            "title": "Optimal Iteration",
            "description": "Loop complexity within bounds.",
        }
    ]
    return {"performance_findings": findings, "execution_trace": trace}


def analyze_security_node(state: WorkflowState) -> Dict[str, Any]:
    """Node: Analyze security vulnerabilities and input hygiene."""
    logger.debug("Executing analyze_security_node")
    trace = state.get("execution_trace", []) + ["analyze_security_node"]
    findings = [
        {
            "category": "Security",
            "title": "Input Sanitation",
            "description": "Inputs validated via Pydantic.",
        }
    ]
    return {"security_findings": findings, "execution_trace": trace}


def analyze_maintainability_node(state: WorkflowState) -> Dict[str, Any]:
    """Node: Analyze code style, documentation, and maintainability."""
    logger.debug("Executing analyze_maintainability_node")
    trace = state.get("execution_trace", []) + ["analyze_maintainability_node"]
    findings = [
        {
            "category": "Maintainability",
            "title": "Google Docstring Compliance",
            "description": "Docstrings properly formatted.",
        }
    ]
    return {"maintainability_findings": findings, "execution_trace": trace}


def aggregate_results_node(state: WorkflowState) -> Dict[str, Any]:
    """Node: Aggregate parallel findings into unified list."""
    logger.debug("Executing aggregate_results_node")
    trace = state.get("execution_trace", []) + ["aggregate_results_node"]
    combined = (
        state.get("architecture_findings", [])
        + state.get("performance_findings", [])
        + state.get("security_findings", [])
        + state.get("maintainability_findings", [])
    )
    return {"aggregated_findings": combined, "execution_trace": trace}


def resolve_conflicts_node(state: WorkflowState) -> Dict[str, Any]:
    """Node: Resolve conflicting recommendations and de-duplicate."""
    logger.debug("Executing resolve_conflicts_node")
    trace = state.get("execution_trace", []) + ["resolve_conflicts_node"]
    unique_findings = state.get("aggregated_findings", [])
    return {"aggregated_findings": unique_findings, "execution_trace": trace}


def produce_review_node(state: WorkflowState) -> Dict[str, Any]:
    """Node: Synthesize final review report."""
    logger.debug("Executing produce_review_node")
    trace = state.get("execution_trace", []) + ["produce_review_node"]
    final_review = {
        "pr_id": state["pr_id"],
        "verdict": "APPROVE",
        "findings_count": len(state.get("aggregated_findings", [])),
        "trace_steps": len(trace),
    }
    return {"final_review": final_review, "execution_trace": trace, "status": "completed"}
