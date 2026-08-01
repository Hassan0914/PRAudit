"""FastAPI application providing REST APIs for PRAudit Pull Request Review Platform (Phases 1–15)."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.exceptions import InvalidRepositoryError, RepositoryNotFoundError
from app.core.logging import setup_logger
from app.git.diff_parser import PRDiffParser
from app.git.mapper import DiffSymbolMapper
from app.git.pr_models import ChangeTypeEnum, PullRequest, PullRequestFile
from app.git.service import GitBranchService, GitCommitService, GitDiffService, GitRepositoryService
from app.github.publisher import GitHubReviewPublisher
from app.github.webhooks import GitHubWebhookService
from app.repository.intelligence import RepositoryIntelligenceEngine
from app.review.engine import DeterministicReviewEngine
from app.review.impact import ChangeImpactEngine
from app.review.review_models import ReviewReport

logger = setup_logger("api.main")

app = FastAPI(
    title=settings.APP_NAME,
    version="3.0.0",
    description="PRAudit — Pull Request Review Platform (Phases 1–15)",
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


class SearchQueryRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to target repository.")
    query: str = Field(..., description="Prefix or search query term.")
    limit: int = Field(50, description="Max results per category.")


# --- Health Endpoint ---

@app.get("/health", tags=["Health"])
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.APP_NAME, "version": "3.0.0"}


# --- Phase 1–10 Intelligence, Graphs, Metrics, Static Analysis, Security & Search Endpoints ---

@app.post("/api/v1/analyze", tags=["Intelligence"])
def analyze_repository(request: AnalyzeRequest) -> Dict[str, Any]:
    """Perform complete intelligence and relationship analysis on a repository."""
    target_path = Path(request.repo_path)
    try:
        result = intelligence_engine.analyze_repository(target_path)
        return {
            "status": "success",
            "summary": result.summary,
            "parsing_stats": {
                "total_files_parsed": result.parsing_stats.total_files_parsed,
                "successful_parses": result.parsing_stats.successful_parses,
                "failed_parses": result.parsing_stats.failed_parses,
                "files_with_syntax_errors": result.parsing_stats.files_with_syntax_errors,
                "total_parse_duration_ms": result.parsing_stats.total_parse_duration_ms,
                "average_parse_duration_ms": result.parsing_stats.average_parse_duration_ms,
            },
            "chunk_stats": {
                "total_chunks": result.chunk_stats.total_chunks,
                "function_count": result.chunk_stats.function_count,
                "class_count": result.chunk_stats.class_count,
                "method_count": result.chunk_stats.method_count,
                "average_lines_per_chunk": result.chunk_stats.average_lines_per_chunk,
            },
            "symbol_stats": {
                "total_symbols": result.symbol_stats.total_symbols,
                "function_count": result.symbol_stats.function_count,
                "class_count": result.symbol_stats.class_count,
                "method_count": result.symbol_stats.method_count,
                "import_count": result.symbol_stats.import_count,
            },
            "metrics": {
                "total_lines": result.metrics.total_lines,
                "total_code_lines": result.metrics.total_code_lines,
                "average_cyclomatic_complexity": result.metrics.average_cyclomatic_complexity,
                "average_maintainability_index": result.metrics.average_maintainability_index,
            },
            "static_analysis_summary": {
                "total_findings": result.static_analysis.total_findings,
                "high": result.static_analysis.high_severity_count,
                "medium": result.static_analysis.medium_severity_count,
                "low": result.static_analysis.low_severity_count,
            },
            "security_summary": {
                "total_vulnerabilities": result.security.total_vulnerabilities,
                "critical": result.security.critical_count,
                "high": result.security.high_count,
                "medium": result.security.medium_count,
                "low": result.security.low_count,
            },
        }
    except (RepositoryNotFoundError, InvalidRepositoryError) as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/files", tags=["Discovery"])
def list_repository_files(request: AnalyzeRequest) -> Dict[str, Any]:
    """Discover and list source files."""
    target_path = Path(request.repo_path)
    try:
        metadata, files, stats = intelligence_engine.discovery_engine.discover(target_path)
        return {
            "status": "success",
            "repository": metadata.name,
            "total_files": len(files),
            "files": [
                {"relative_path": sf.relative_path, "language": sf.language.value, "size_bytes": sf.size_bytes}
                for sf in files
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/symbols", tags=["Symbols"])
def query_symbols(request: SymbolQueryRequest) -> Dict[str, Any]:
    """Query indexed symbols."""
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
            "symbols": [
                {
                    "symbol_id": s.symbol_id,
                    "name": s.name,
                    "kind": s.kind.value,
                    "file_path": s.file_path,
                    "language": s.language.value,
                    "start_line": s.location.start_line,
                    "end_line": s.location.end_line,
                }
                for s in symbols
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/graphs", tags=["Graphs"])
def get_repository_graphs(request: AnalyzeRequest) -> Dict[str, Any]:
    """Retrieve Call, Import, Dependency, and Inheritance Graphs for a repository."""
    target_path = Path(request.repo_path)
    try:
        result = intelligence_engine.analyze_repository(target_path)
        return {
            "status": "success",
            "repository": result.metadata.name,
            "call_graph": result.graphs.call_graph.to_dict(),
            "import_graph": result.graphs.import_graph.to_dict(),
            "dependency_graph": result.graphs.dependency_graph.to_dict(),
            "inheritance_graph": result.graphs.inheritance_graph.to_dict(),
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/metrics", tags=["Metrics"])
def get_code_metrics(request: AnalyzeRequest) -> Dict[str, Any]:
    """Retrieve detailed quality and complexity metrics for a repository."""
    target_path = Path(request.repo_path)
    try:
        result = intelligence_engine.analyze_repository(target_path)
        return {
            "status": "success",
            "repository": result.metadata.name,
            "summary": {
                "total_files": result.metrics.total_files,
                "total_lines": result.metrics.total_lines,
                "total_code_lines": result.metrics.total_code_lines,
                "average_complexity": result.metrics.average_cyclomatic_complexity,
                "average_maintainability": result.metrics.average_maintainability_index,
            },
            "file_metrics": {
                p: {
                    "total_lines": fm.total_lines,
                    "code_lines": fm.code_lines,
                    "complexity": fm.total_complexity,
                    "avg_function_complexity": fm.average_function_complexity,
                    "maintainability_index": fm.maintainability_index,
                    "functions_count": len(fm.functions),
                    "classes_count": len(fm.classes),
                }
                for p, fm in result.metrics.file_metrics.items()
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/static-analysis", tags=["Static Analysis"])
def run_static_analysis(request: AnalyzeRequest) -> Dict[str, Any]:
    """Run static analysis and return findings report."""
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
                    "analyzer": f.analyzer_name,
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
    """Run security scanners and return vulnerability report."""
    target_path = Path(request.repo_path)
    try:
        result = intelligence_engine.analyze_repository(target_path)
        return {
            "status": "success",
            "total_vulnerabilities": result.security.total_vulnerabilities,
            "critical_count": result.security.critical_count,
            "high_count": result.security.high_count,
            "medium_count": result.security.medium_count,
            "low_count": result.security.low_count,
            "vulnerabilities": [
                {
                    "finding_id": v.finding_id,
                    "vulnerability_id": v.vulnerability_id,
                    "scanner": v.scanner_name,
                    "file_path": v.file_path,
                    "line": v.line,
                    "severity": v.severity.value,
                    "confidence": v.confidence.value,
                    "cwe_id": v.cwe_id,
                    "message": v.message,
                    "recommendation": v.recommendation,
                }
                for v in result.security.findings
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/index/search", tags=["Indexing"])
def search_repository_index(request: SearchQueryRequest) -> Dict[str, Any]:
    """Search repository multi-index across files, symbols, and chunks."""
    target_path = Path(request.repo_path)
    try:
        result = intelligence_engine.analyze_repository(target_path)
        search_res = result.unified_index.prefix_search(request.query, limit=request.limit)
        return {
            "status": "success",
            "query": request.query,
            "total_matches": search_res.total_matches,
            "files": [f.relative_path for f in search_res.files],
            "symbols": [
                {"name": s.name, "kind": s.kind.value, "file": s.file_path, "line": s.location.start_line}
                for s in search_res.symbols
            ],
            "chunks": [
                {"symbol": c.symbol_name, "type": c.chunk_type.value, "file": c.file_path, "lines": f"{c.start_line}-{c.end_line}"}
                for c in search_res.chunks
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


# --- Phase 11: Git Endpoints ---

@app.post("/api/v1/git/status", tags=["Git Engine"])
def get_git_status(request: AnalyzeRequest) -> Dict[str, Any]:
    """Retrieve Git working tree status."""
    target_path = Path(request.repo_path)
    try:
        state = git_repo_service.get_repository_state(target_path)
        return {
            "status": "success",
            "current_branch": state.current_branch,
            "head_commit": state.head_commit.hash if state.head_commit else None,
            "is_dirty": state.is_dirty,
            "staged_files": state.staged_files,
            "unstaged_files": state.unstaged_files,
            "untracked_files": state.untracked_files,
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/git/history", tags=["Git Engine"])
def get_git_history(request: HistoryRequest) -> Dict[str, Any]:
    """Retrieve Git commit history."""
    target_path = Path(request.repo_path)
    try:
        commits = git_commit_service.get_commit_history(target_path, max_count=request.max_count)
        return {
            "status": "success",
            "count": len(commits),
            "commits": [
                {
                    "hash": c.hash,
                    "short_hash": c.short_hash,
                    "author": c.author_name,
                    "email": c.author_email,
                    "committed_at": c.committed_at,
                    "message": c.message,
                }
                for c in commits
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/git/diff", tags=["Git Engine"])
def get_git_diff(request: DiffRequest) -> Dict[str, Any]:
    """Retrieve Git diff between base_ref and head_ref."""
    target_path = Path(request.repo_path)
    try:
        diff = git_diff_service.get_diff(target_path, request.base_ref, request.head_ref)
        return {
            "status": "success",
            "base_ref": diff.base_ref,
            "head_ref": diff.head_ref,
            "merge_base": diff.merge_base,
            "changed_files_count": len(diff.file_changes),
            "file_changes": [
                {
                    "path": fc.relative_path,
                    "change_type": fc.change_type.value,
                    "lines_added": fc.lines_added,
                    "lines_deleted": fc.lines_deleted,
                }
                for fc in diff.file_changes
            ],
            "raw_diff": diff.raw_diff,
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


# --- Phase 12 & 13: PR & Impact Analysis Endpoints ---

@app.post("/api/v1/pr/analyze", tags=["Pull Request Engine"])
def analyze_pr_diff(request: PRAnalyzeRequest) -> Dict[str, Any]:
    """Parse PR diff and map changed lines to enclosing symbols."""
    target_path = Path(request.repo_path)
    try:
        intel = intelligence_engine.analyze_repository(target_path)
        diff = git_diff_service.get_diff(target_path, request.base_ref, request.head_ref)
        parsed_files = diff_parser.parse_diff(diff.raw_diff)

        pr = PullRequest(
            pr_id=request.pr_id,
            title=f"PR diff {request.base_ref}..{request.head_ref}",
            description="Automated PR diff analysis",
            base_branch=request.base_ref,
            head_branch=request.head_ref,
            base_commit=diff.merge_base or request.base_ref,
            head_commit=request.head_ref,
            files=parsed_files,
        )

        mapped_pr = symbol_mapper.map_pr_symbols(pr, intel.symbol_index)

        return {
            "status": "success",
            "pr_id": mapped_pr.pr_id,
            "files_count": len(mapped_pr.files),
            "files": [
                {
                    "file_path": pf.file_path,
                    "change_type": pf.change_type.value,
                    "hunks_count": len(pf.hunks),
                    "added_lines": pf.added_lines_count,
                    "deleted_lines": pf.deleted_lines_count,
                }
                for pf in mapped_pr.files
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/v1/pr/impact", tags=["Pull Request Engine"])
def analyze_pr_impact(request: ImpactRequest) -> Dict[str, Any]:
    """Perform change impact analysis for a Pull Request."""
    target_path = Path(request.repo_path)
    try:
        intel = intelligence_engine.analyze_repository(target_path)
        diff = git_diff_service.get_diff(target_path, request.base_ref, request.head_ref)
        parsed_files = diff_parser.parse_diff(diff.raw_diff)

        pr = PullRequest(
            pr_id="PR-IMPACT",
            title="Impact analysis",
            description="",
            base_branch=request.base_ref,
            head_branch=request.head_ref,
            base_commit=diff.merge_base or request.base_ref,
            head_commit=request.head_ref,
            files=parsed_files,
        )
        symbol_mapper.map_pr_symbols(pr, intel.symbol_index)

        impact_report = impact_engine.analyze_impact(
            pr, intel.graphs, intel.symbol_index, max_depth=request.max_depth
        )

        return {
            "status": "success",
            "pr_id": impact_report.pr_id,
            "traversal_depth": impact_report.traversal_depth,
            "impacted_files": impact_report.impacted_files,
            "statistics": impact_report.statistics.__dict__,
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


# --- Phase 14 & 15: Review & GitHub Endpoints ---

@app.post("/api/v1/review", tags=["Review Engine"])
def execute_pr_review(request: ReviewRequest) -> Dict[str, Any]:
    """Execute deterministic PR review and return structured review report."""
    target_path = Path(request.repo_path)
    try:
        intel = intelligence_engine.analyze_repository(target_path)
        diff = git_diff_service.get_diff(target_path, request.base_ref, request.head_ref)
        parsed_files = diff_parser.parse_diff(diff.raw_diff)

        pr = PullRequest(
            pr_id=request.pr_id,
            title=f"Review PR {request.pr_id}",
            description="Deterministic PR Review",
            base_branch=request.base_ref,
            head_branch=request.head_ref,
            base_commit=diff.merge_base or request.base_ref,
            head_commit=request.head_ref,
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
            "findings_count": review_report.summary.total_findings,
            "comments_count": len(review_report.comments),
            "summary": review_report.summary.summary_text,
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.get("/api/v1/review/{review_id}", tags=["Review Engine"])
def get_review_by_id(review_id: str) -> Dict[str, Any]:
    """Retrieve a previously generated review report by review_id."""
    report = reviews_store.get(review_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Review with ID '{review_id}' not found."
        )

    return {
        "status": "success",
        "review_id": report.review_id,
        "pr_id": report.pr_id,
        "verdict": report.summary.verdict.value,
        "summary": report.summary.__dict__,
        "findings": [
            {
                "id": f.finding_id,
                "rule_id": f.rule_id,
                "title": f.title,
                "severity": f.severity.value,
                "file": f.file_path,
                "line": f.line,
                "evidence": f.evidence,
                "recommendation": f.recommendation,
            }
            for f in report.findings
        ],
        "comments": [
            {"path": c.file_path, "line": c.line, "body": c.body} for c in report.comments
        ],
    }


@app.post("/api/v1/github/webhook", tags=["GitHub Integration"])
async def handle_github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(None),
    x_hub_signature_256: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """Process incoming GitHub Webhook events."""
    body_bytes = await request.body()
    if not webhook_service.verify_signature(body_bytes, x_hub_signature_256):
        logger.debug("Webhook signature check skipped or invalid")

    try:
        payload = await request.json()
        event = webhook_service.parse_event(x_github_event or "pull_request", payload)

        return {
            "status": "received",
            "event_type": event.event_type,
            "action": event.action,
            "repository": event.repository_name,
            "pr_number": event.pr_number,
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
