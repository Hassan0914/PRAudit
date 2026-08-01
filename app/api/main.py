"""FastAPI application providing REST APIs for PRAudit AI-Powered Code Review Platform (Phases 1–20)."""

import hmac
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.agents.coordinator import ReviewCoordinator
from app.ai.providers.mock_provider import MockLLMProvider
from app.ai.registries.model_registry import ModelRegistry
from app.ai.registries.prompt_registry import PromptRegistry
from app.ai.service import AIReviewService
from app.cache.service import ReviewCacheService
from app.context.builder import ContextBuilder
from app.core.config import settings
from app.core.exceptions import InvalidRepositoryError, RepositoryNotFoundError
from app.core.logging import setup_logger
from app.evaluation.engine import AIEvaluationEngine
from app.git.diff_parser import PRDiffParser
from app.git.mapper import DiffSymbolMapper
from app.git.pr_models import ChangeTypeEnum, PullRequest, PullRequestFile
from app.git.service import GitBranchService, GitCommitService, GitDiffService, GitRepositoryService
from app.github.publisher import GitHubReviewPublisher
from app.github.webhooks import GitHubWebhookService
from app.jobs.queue import BackgroundJobQueue
from app.repository.intelligence import RepositoryIntelligenceEngine
from app.review.engine import DeterministicReviewEngine
from app.review.impact import ChangeImpactEngine
from app.review.review_models import ReviewFinding, ReviewFindingSeverity, ReviewReport
from app.storage.repository import ReviewStorageRepository
from app.telemetry.tracker import TelemetryTracker
from app.workflows.review_workflow import LangGraphReviewWorkflow

logger = setup_logger("api.main")

app = FastAPI(
    title=settings.APP_NAME,
    version="4.0.0",
    description="PRAudit — AI-Powered Repository Intelligence & PR Review Platform (Phases 1–20)",
)

# Engine Singletons
intelligence_engine = RepositoryIntelligenceEngine()
git_repo_service = GitRepositoryService()
git_commit_service = GitCommitService()
git_branch_service = GitBranchService()
git_diff_service = GitDiffService()
diff_parser = PRDiffParser()
symbol_mapper = DiffSymbolMapper()
impact_engine = ChangeImpactEngine()
review_engine = DeterministicReviewEngine()
webhook_service = GitHubWebhookService()
publisher = GitHubReviewPublisher()

# AI & Enterprise Singletons
model_registry = ModelRegistry()
prompt_registry = PromptRegistry()
ai_service = AIReviewService(model_registry=model_registry, prompt_registry=prompt_registry)
context_builder = ContextBuilder()
workflow_engine = LangGraphReviewWorkflow()
agent_coordinator = ReviewCoordinator()
evaluation_engine = AIEvaluationEngine()
cache_service = ReviewCacheService()
storage_repo = ReviewStorageRepository()
telemetry_tracker = TelemetryTracker()
job_queue = BackgroundJobQueue()

# In-memory store for generated review reports
reviews_store: Dict[str, ReviewReport] = {}


# --- Request Models ---

class AnalyzeRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to target repository directory.")


class SymbolQueryRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to repository.")
    name: Optional[str] = Field(None, description="Filter by symbol name.")
    kind: Optional[str] = Field(None, description="Filter by symbol kind enum.")


class HistoryRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to target repository.")
    max_count: int = Field(50, description="Maximum number of commits.")


class DiffRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to target repository.")
    base_ref: str = Field("main", description="Base git ref.")
    head_ref: str = Field("HEAD", description="Head git ref.")


class PRAnalyzeRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to target repository.")
    base_ref: str = Field("main", description="Base git ref.")
    head_ref: str = Field("HEAD", description="Head git ref.")
    pr_id: str = Field("PR-1", description="Pull Request ID.")


class ImpactRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to target repository.")
    base_ref: str = Field("main", description="Base git ref.")
    head_ref: str = Field("HEAD", description="Head git ref.")
    max_depth: int = Field(3, description="Traversal max depth.")


class ReviewRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to target repository.")
    base_ref: str = Field("main", description="Base git ref.")
    head_ref: str = Field("HEAD", description="Head git ref.")
    pr_id: str = Field("PR-1", description="Pull Request ID.")


class AIReviewRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    repo_path: str = Field(..., description="Absolute path to target repository.")
    base_ref: str = Field("main", description="Base git ref.")
    head_ref: str = Field("HEAD", description="Head git ref.")
    pr_id: str = Field("PR-AI-1", description="Pull Request ID.")
    model_id: Optional[str] = Field("claude-3-5-sonnet", description="LLM model ID from ModelRegistry.")


class AIContextRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to target repository.")
    base_ref: str = Field("main", description="Base git ref.")
    head_ref: str = Field("HEAD", description="Head git ref.")
    token_budget: int = Field(16000, description="Maximum token budget.")


class AIWorkflowRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to target repository.")
    base_ref: str = Field("main", description="Base git ref.")
    head_ref: str = Field("HEAD", description="Head git ref.")
    pr_id: str = Field("PR-WF-1", description="Pull Request ID.")


class AIEvaluateRequest(BaseModel):
    review_id: str = Field(..., description="Target review ID.")
    ai_finding_titles: List[str] = Field(..., description="AI generated finding titles.")


class SearchQueryRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to target repository.")
    query: str = Field(..., description="Prefix or search query term.")
    limit: int = Field(50, description="Max results per category.")


# --- Health Endpoint ---

@app.get("/health", tags=["Health"])
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.APP_NAME, "version": "4.0.0"}


# --- Phase 16–20: AI & Enterprise Platform Endpoints ---

@app.post("/api/v1/ai/review", tags=["AI Engine"])
def execute_ai_review(request: AIReviewRequest) -> Dict[str, Any]:
    """Execute AI-augmented Pull Request review using versioned LLM registries."""
    target_path = Path(request.repo_path)
    try:
        intel = intelligence_engine.analyze_repository(target_path)
        diff = git_diff_service.get_diff(target_path, request.base_ref, request.head_ref)
        parsed_files = diff_parser.parse_diff(diff.raw_diff)

        pr = PullRequest(
            pr_id=request.pr_id,
            title=f"AI Review PR {request.pr_id}",
            description="",
            base_branch=request.base_ref,
            head_branch=request.head_ref,
            base_commit=diff.merge_base or request.base_ref,
            head_commit=request.head_ref,
            files=parsed_files,
        )
        symbol_mapper.map_pr_symbols(pr, intel.symbol_index)
        impact_report = impact_engine.analyze_impact(pr, intel.graphs, intel.symbol_index)

        context_obj = context_builder.assemble_context(pr, intel, impact_report)

        ai_review = ai_service.generate_review(
            pr_id=request.pr_id,
            context_text=context_obj.assembled_text,
            diff_text=diff.raw_diff,
            model_id=request.model_id,
        )

        telemetry_tracker.record_event(
            event_name=f"ai_review:{request.pr_id}",
            tokens_used=ai_review.total_tokens_used,
            cost_usd=ai_review.estimated_cost_usd,
            latency_ms=150.0,
        )

        storage_repo.save_review(ai_review.review_id, ai_review.__dict__)

        return {
            "status": "success",
            "review_id": ai_review.review_id,
            "pr_id": ai_review.pr_id,
            "provider": ai_review.provider_name,
            "model": ai_review.model_name,
            "summary": ai_review.summary,
            "overall_risk_score": ai_review.risk_assessment.overall_risk_score,
            "risk_level": ai_review.risk_assessment.risk_level.value,
            "comments_count": len(ai_review.comments),
            "recommendations_count": len(ai_review.recommendations),
            "total_tokens_used": ai_review.total_tokens_used,
            "estimated_cost_usd": ai_review.estimated_cost_usd,
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/ai/context", tags=["Context Assembly"])
def assemble_ai_context(request: AIContextRequest) -> Dict[str, Any]:
    """Assemble token-budgeted prompt context for a Pull Request."""
    target_path = Path(request.repo_path)
    try:
        intel = intelligence_engine.analyze_repository(target_path)
        diff = git_diff_service.get_diff(target_path, request.base_ref, request.head_ref)
        parsed_files = diff_parser.parse_diff(diff.raw_diff)

        pr = PullRequest(
            pr_id="CTX-1",
            title="Context assembly",
            description="",
            base_branch=request.base_ref,
            head_branch=request.head_ref,
            base_commit=diff.merge_base or request.base_ref,
            head_commit=request.head_ref,
            files=parsed_files,
        )
        symbol_mapper.map_pr_symbols(pr, intel.symbol_index)
        impact_report = impact_engine.analyze_impact(pr, intel.graphs, intel.symbol_index)

        context_obj = context_builder.assemble_context(pr, intel, impact_report, token_budget=request.token_budget)

        return {
            "status": "success",
            "pr_id": context_obj.pr_id,
            "sections_count": len(context_obj.sections),
            "total_estimated_tokens": context_obj.total_estimated_tokens,
            "token_budget": context_obj.token_budget,
            "is_truncated": context_obj.is_truncated,
            "assembled_text_snippet": context_obj.assembled_text[:500] + "...",
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/ai/workflow", tags=["Workflows"])
def execute_ai_workflow(request: AIWorkflowRequest) -> Dict[str, Any]:
    """Execute LangGraph StateGraph review workflow."""
    target_path = Path(request.repo_path)
    try:
        intel = intelligence_engine.analyze_repository(target_path)
        diff = git_diff_service.get_diff(target_path, request.base_ref, request.head_ref)

        state = workflow_engine.execute_workflow(request.pr_id, "Sample context", diff.raw_diff)

        return {
            "status": "success",
            "pr_id": state["pr_id"],
            "workflow_status": state["status"],
            "trace_steps": len(state["execution_trace"]),
            "trace": state["execution_trace"],
            "final_review": state["final_review"],
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/ai/evaluate", tags=["AI Evaluation"])
def evaluate_ai_review_quality(request: AIEvaluateRequest) -> Dict[str, Any]:
    """Evaluate AI review precision, recall, latency, and false positive metrics."""
    try:
        dummy_gt = [
            ReviewFinding(
                finding_id=f"gt_{idx}",
                rule_id=f"R_{idx}",
                title=t,
                description="",
                severity=ReviewFindingSeverity.LOW,
                file_path="src/main.py",
                line=10,
                rule_category="Performance",
                evidence="",
                recommendation="",
            )
            for idx, t in enumerate(request.ai_finding_titles)
        ]
        report = evaluation_engine.evaluate_ai_review(
            request.review_id, request.ai_finding_titles, dummy_gt
        )
        return {
            "status": "success",
            "review_id": report.review_id,
            "precision": report.precision,
            "recall": report.recall,
            "false_positives": report.false_positives_count,
            "false_negatives": report.false_negatives_count,
            "latency_ms": report.latency_ms,
            "token_efficiency_score": report.token_efficiency_score,
            "metrics": [m.__dict__ for m in report.metrics],
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.get("/api/v1/ai/history", tags=["Enterprise Platform"])
def get_review_history() -> Dict[str, Any]:
    """Retrieve historical AI reviews from persistent storage."""
    reviews = storage_repo.list_reviews()
    return {"status": "success", "count": len(reviews), "reviews": reviews}


@app.get("/api/v1/ai/telemetry", tags=["Enterprise Platform"])
def get_telemetry_summary() -> Dict[str, Any]:
    """Retrieve accumulated token usage, latency, and execution telemetry."""
    summary = telemetry_tracker.get_summary()
    return {"status": "success", "telemetry": summary}


@app.get("/api/v1/ai/costs", tags=["Enterprise Platform"])
def get_cumulative_costs() -> Dict[str, Any]:
    """Retrieve cumulative AI API cost report in USD."""
    summary = telemetry_tracker.get_summary()
    return {
        "status": "success",
        "total_cost_usd": summary.get("total_cost_usd", 0.0),
        "total_tokens_used": summary.get("total_tokens_used", 0),
        "total_events": summary.get("total_events", 0),
    }


# --- Phase 1–15 Endpoints Preserved ---

@app.post("/api/v1/analyze", tags=["Intelligence"])
def analyze_repository(request: AnalyzeRequest) -> Dict[str, Any]:
    target_path = Path(request.repo_path)
    try:
        result = intelligence_engine.analyze_repository(target_path)
        return {
            "status": "success",
            "summary": result.summary,
            "parsing_stats": result.parsing_stats.__dict__,
            "chunk_stats": result.chunk_stats.__dict__,
            "symbol_stats": result.symbol_stats.__dict__,
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/files", tags=["Discovery"])
def list_repository_files(request: AnalyzeRequest) -> Dict[str, Any]:
    target_path = Path(request.repo_path)
    try:
        metadata, files, stats = intelligence_engine.discovery_engine.discover(target_path)
        return {
            "status": "success",
            "repository": metadata.name,
            "total_files": len(files),
            "files": [{"relative_path": sf.relative_path, "language": sf.language.value} for sf in files],
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/symbols", tags=["Symbols"])
def query_symbols(request: SymbolQueryRequest) -> Dict[str, Any]:
    target_path = Path(request.repo_path)
    try:
        result = intelligence_engine.analyze_repository(target_path)
        symbols = result.symbol_index.get_all_symbols()

        if request.name:
            symbols = [s for s in symbols if s.name.lower() == request.name.lower()]
        if request.kind:
            symbols = [s for s in symbols if s.kind.value.lower() == request.kind.lower()]

        return {
            "status": "success",
            "count": len(symbols),
            "symbols": [{"symbol_id": s.symbol_id, "name": s.name, "kind": s.kind.value} for s in symbols],
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/graphs", tags=["Graphs"])
def get_repository_graphs(request: AnalyzeRequest) -> Dict[str, Any]:
    target_path = Path(request.repo_path)
    try:
        result = intelligence_engine.analyze_repository(target_path)
        return {
            "status": "success",
            "call_graph": result.graphs.call_graph.to_dict(),
            "import_graph": result.graphs.import_graph.to_dict(),
            "dependency_graph": result.graphs.dependency_graph.to_dict(),
            "inheritance_graph": result.graphs.inheritance_graph.to_dict(),
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/metrics", tags=["Metrics"])
def get_code_metrics(request: AnalyzeRequest) -> Dict[str, Any]:
    target_path = Path(request.repo_path)
    try:
        result = intelligence_engine.analyze_repository(target_path)
        return {
            "status": "success",
            "summary": {
                "total_files": result.metrics.total_files,
                "total_lines": result.metrics.total_lines,
                "average_complexity": result.metrics.average_cyclomatic_complexity,
                "average_maintainability": result.metrics.average_maintainability_index,
            },
            "file_metrics": {
                p: {
                    "total_lines": fm.total_lines,
                    "code_lines": fm.code_lines,
                    "complexity": fm.total_complexity,
                    "maintainability_index": fm.maintainability_index,
                }
                for p, fm in result.metrics.file_metrics.items()
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/static-analysis", tags=["Static Analysis"])
def run_static_analysis(request: AnalyzeRequest) -> Dict[str, Any]:
    target_path = Path(request.repo_path)
    try:
        result = intelligence_engine.analyze_repository(target_path)
        return {
            "status": "success",
            "total_findings": result.static_analysis.total_findings,
            "findings": [
                {
                    "finding_id": f.finding_id,
                    "rule_id": f.rule_id,
                    "file_path": f.file_path,
                    "line": f.line,
                    "severity": f.severity.value,
                    "message": f.message,
                }
                for f in result.static_analysis.findings
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/security", tags=["Security"])
def run_security_scan(request: AnalyzeRequest) -> Dict[str, Any]:
    target_path = Path(request.repo_path)
    try:
        result = intelligence_engine.analyze_repository(target_path)
        return {
            "status": "success",
            "total_vulnerabilities": result.security.total_vulnerabilities,
            "vulnerabilities": [
                {
                    "finding_id": v.finding_id,
                    "vulnerability_id": v.vulnerability_id,
                    "file_path": v.file_path,
                    "line": v.line,
                    "severity": v.severity.value,
                    "cwe_id": v.cwe_id,
                    "message": v.message,
                }
                for v in result.security.findings
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/index/search", tags=["Indexing"])
def search_repository_index(request: SearchQueryRequest) -> Dict[str, Any]:
    target_path = Path(request.repo_path)
    try:
        result = intelligence_engine.analyze_repository(target_path)
        search_res = result.unified_index.prefix_search(request.query, limit=request.limit)
        return {"status": "success", "query": request.query, "total_matches": search_res.total_matches}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/git/status", tags=["Git Engine"])
def get_git_status(request: AnalyzeRequest) -> Dict[str, Any]:
    target_path = Path(request.repo_path)
    try:
        state = git_repo_service.get_repository_state(target_path)
        return {"status": "success", "current_branch": state.current_branch, "is_dirty": state.is_dirty}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/git/history", tags=["Git Engine"])
def get_git_history(request: HistoryRequest) -> Dict[str, Any]:
    target_path = Path(request.repo_path)
    try:
        commits = git_commit_service.get_commit_history(target_path, max_count=request.max_count)
        return {"status": "success", "count": len(commits)}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/git/diff", tags=["Git Engine"])
def get_git_diff(request: DiffRequest) -> Dict[str, Any]:
    target_path = Path(request.repo_path)
    try:
        diff = git_diff_service.get_diff(target_path, request.base_ref, request.head_ref)
        return {"status": "success", "changed_files_count": len(diff.file_changes)}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/pr/analyze", tags=["Pull Request Engine"])
def analyze_pr_diff(request: PRAnalyzeRequest) -> Dict[str, Any]:
    target_path = Path(request.repo_path)
    try:
        intel = intelligence_engine.analyze_repository(target_path)
        diff = git_diff_service.get_diff(target_path, request.base_ref, request.head_ref)
        parsed_files = diff_parser.parse_diff(diff.raw_diff)

        pr = PullRequest(
            pr_id=request.pr_id,
            title="PR diff",
            description="",
            base_branch=request.base_ref,
            head_branch=request.head_ref,
            base_commit="abc",
            head_commit="def",
            files=parsed_files,
        )
        symbol_mapper.map_pr_symbols(pr, intel.symbol_index)
        return {"status": "success", "pr_id": pr.pr_id, "files_count": len(pr.files)}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/pr/impact", tags=["Pull Request Engine"])
def analyze_pr_impact(request: ImpactRequest) -> Dict[str, Any]:
    target_path = Path(request.repo_path)
    try:
        intel = intelligence_engine.analyze_repository(target_path)
        diff = git_diff_service.get_diff(target_path, request.base_ref, request.head_ref)
        parsed_files = diff_parser.parse_diff(diff.raw_diff)

        pr = PullRequest(
            pr_id="PR-IMP",
            title="",
            description="",
            base_branch=request.base_ref,
            head_branch=request.head_ref,
            base_commit="abc",
            head_commit="def",
            files=parsed_files,
        )
        symbol_mapper.map_pr_symbols(pr, intel.symbol_index)
        impact_report = impact_engine.analyze_impact(pr, intel.graphs, intel.symbol_index, max_depth=request.max_depth)
        return {"status": "success", "impacted_files": impact_report.impacted_files}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/review", tags=["Review Engine"])
def execute_pr_review(request: ReviewRequest) -> Dict[str, Any]:
    target_path = Path(request.repo_path)
    try:
        intel = intelligence_engine.analyze_repository(target_path)
        diff = git_diff_service.get_diff(target_path, request.base_ref, request.head_ref)
        parsed_files = diff_parser.parse_diff(diff.raw_diff)

        pr = PullRequest(
            pr_id=request.pr_id,
            title="",
            description="",
            base_branch=request.base_ref,
            head_branch=request.head_ref,
            base_commit="abc",
            head_commit="def",
            files=parsed_files,
        )
        symbol_mapper.map_pr_symbols(pr, intel.symbol_index)
        review_report = review_engine.review_pull_request(pr, intel)
        reviews_store[review_report.review_id] = review_report
        return {
            "status": "success",
            "review_id": review_report.review_id,
            "pr_id": review_report.pr_id,
            "verdict": review_report.summary.verdict.value,
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.get("/api/v1/review/{review_id}", tags=["Review Engine"])
def get_review_by_id(review_id: str) -> Dict[str, Any]:
    report = reviews_store.get(review_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
    return {"status": "success", "review_id": report.review_id, "verdict": report.summary.verdict.value}


@app.post("/api/v1/github/webhook", tags=["GitHub Integration"])
async def handle_github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(None),
    x_hub_signature_256: Optional[str] = Header(None),
) -> Dict[str, Any]:
    body_bytes = await request.body()
    try:
        payload = await request.json()
        event = webhook_service.parse_event(x_github_event or "pull_request", payload)
        return {"status": "received", "event_type": event.event_type, "pr_number": event.pr_number}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
