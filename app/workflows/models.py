"""Data models and state structures for LangGraph review workflows with state reducers."""

import operator
from typing import Any, Dict, List, Optional
from typing_extensions import Annotated, TypedDict


class WorkflowState(TypedDict):
    """Shared state passed between LangGraph workflow nodes with Annotated reducers."""

    pr_id: str
    context_text: str
    diff_text: str
    architecture_findings: Annotated[List[Dict[str, Any]], operator.add]
    performance_findings: Annotated[List[Dict[str, Any]], operator.add]
    security_findings: Annotated[List[Dict[str, Any]], operator.add]
    maintainability_findings: Annotated[List[Dict[str, Any]], operator.add]
    aggregated_findings: Annotated[List[Dict[str, Any]], operator.add]
    final_review: Optional[Dict[str, Any]]
    execution_trace: Annotated[List[str], operator.add]
    status: str
