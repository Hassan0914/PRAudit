"""Targeted context providers extracting symbol, dependency, metrics, security, and diff context."""

from typing import List, Optional
from app.context.models import ContextSection
from app.git.pr_models import PullRequest
from app.repository.intelligence import RepositoryIntelligenceResult
from app.review.impact_models import ImpactAnalysisReport


class SymbolContextProvider:
    """Extracts symbol definition context for modified PR symbols."""

    def get_section(self, pr: PullRequest, intelligence: RepositoryIntelligenceResult) -> ContextSection:
        lines: List[str] = []
        for pr_file in pr.files:
            symbols = intelligence.symbol_index.lookup_by_file(pr_file.file_path)
            for sym in symbols:
                lines.append(f"Symbol '{sym.name}' ({sym.kind.value}) in {sym.file_path}: lines {sym.location.start_line}-{sym.location.end_line}")

        text = "\n".join(lines) if lines else "No modified symbols identified."
        est_tokens = len(text.split())
        return ContextSection(title="Changed Symbols Context", content=text, estimated_tokens=est_tokens, priority=1)


class DependencyContextProvider:
    """Extracts downstream call graph and import dependency context."""

    def get_section(self, impact_report: ImpactAnalysisReport) -> ContextSection:
        lines = [
            f"Impacted Files: {', '.join(impact_report.impacted_files)}",
            f"Downstream Callers Count: {impact_report.statistics.downstream_callers_count}",
            f"Upstream Dependencies Count: {impact_report.statistics.upstream_dependencies_count}",
        ]
        text = "\n".join(lines)
        est_tokens = len(text.split())
        return ContextSection(title="Graph Dependency Context", content=text, estimated_tokens=est_tokens, priority=2)


class DiffContextProvider:
    """Extracts concise Git diff context."""

    def get_section(self, pr: PullRequest) -> ContextSection:
        lines: List[str] = []
        for f in pr.files:
            lines.append(f"File: {f.file_path} ({f.change_type.value}, +{f.added_lines_count}, -{f.deleted_lines_count})")
            for hunk in f.hunks:
                lines.append(f"  Hunk: {hunk.header}")
                for lc in hunk.line_changes[:10]:
                    lines.append(f"    Line {lc.line_number} [{lc.change_type.value}]: {lc.content.strip()}")

        text = "\n".join(lines)
        est_tokens = len(text.split())
        return ContextSection(title="Pull Request Diff Context", content=text, estimated_tokens=est_tokens, priority=1)


class MetricsContextProvider:
    """Extracts code quality and complexity metrics context."""

    def get_section(self, pr: PullRequest, intelligence: RepositoryIntelligenceResult) -> ContextSection:
        lines: List[str] = []
        for f in pr.files:
            fm = intelligence.metrics.file_metrics.get(f.file_path)
            if fm:
                lines.append(
                    f"File '{f.file_path}': Maintainability={fm.maintainability_index:.1f}/100, "
                    f"Avg Complexity={fm.average_function_complexity:.1f}, LOC={fm.code_lines}"
                )

        text = "\n".join(lines) if lines else "No metric anomalies detected."
        est_tokens = len(text.split())
        return ContextSection(title="Code Quality Metrics Context", content=text, estimated_tokens=est_tokens, priority=3)


class SecurityContextProvider:
    """Extracts security vulnerabilities and static analysis findings context."""

    def get_section(self, intelligence: RepositoryIntelligenceResult) -> ContextSection:
        lines: List[str] = []
        for sec in intelligence.security.findings:
            lines.append(f"Security [{sec.severity.value}] {sec.file_path}:{sec.line} - {sec.message} (CWE: {sec.cwe_id or 'N/A'})")

        for st in intelligence.static_analysis.findings:
            lines.append(f"Static [{st.severity.value}] {st.file_path}:{st.line} - {st.message}")

        text = "\n".join(lines) if lines else "No security vulnerabilities or static findings."
        est_tokens = len(text.split())
        return ContextSection(title="Security & Static Findings Context", content=text, estimated_tokens=est_tokens, priority=1)
