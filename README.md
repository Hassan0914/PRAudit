# PRAudit — AI-Powered Repository Intelligence & Pull Request Review Platform

**PRAudit** is a production-grade Repository Intelligence and AI-Augmented Pull Request Review Platform built in Python 3.11+.

It combines **deterministic repository intelligence** (AST parsing, call/import/inheritance graphs, metrics, static analysis, security scanning, change impact graph analysis) with **AI reasoning** (LLM Provider Abstraction, LangGraph workflows, Specialized Reviewer Agents, Token Budgeting, Cost Tracking, and Evaluation Benchmarking).

---

## Key Features & Architecture (Phases 1–20)

### 1. Repository Discovery & AST Parsing (Phases 1–2)
* **Smart Discovery**: Detects Git metadata, parses `.gitignore` wildcards via `pathspec`, and skips build directories and virtual environments.
* **Tree-Sitter Concrete Syntax Tree Parsing**: Fault-tolerant AST parsing for Python and JavaScript/TypeScript with error recovery.

### 2. Semantic Chunking & Symbol Indexing (Phases 3–4, 7)
* **AST-Based Semantic Chunking**: Splits code along function, class, and method AST nodes with exact line bounds.
* **Unified Multi-Index (`UnifiedRepositoryIndex`)**: In-memory multi-index and Trie prefix search for $O(1)$ lookups across files, symbols, chunks, and imports.

### 3. Repository Relationship Graphs & Metrics (Phases 6, 8)
* **Call, Import, Dependency, and Inheritance Graphs**: Tracks callers, dependencies, and class hierarchies with DFS cycle detection.
* **Code Metrics**: Computes Lines of Code, Cyclomatic Complexity, Max Nesting Depth, and Maintainability Index ($0.0 - 100.0$).

### 4. Static & Security Analysis Engines (Phases 9–10)
* **Static Analysis**: Plugin framework integrating **Ruff**, **MyPy**, and **ESLint**.
* **Security Scanning**: **Bandit** dangerous call inspector (`eval`, `exec`, `pickle`) and secret pattern scanner mapped to **CWE Standards** (`CWE-798`, `CWE-95`, `CWE-312`).

### 5. Git Engine, PR Diffs & Impact Analysis (Phases 11–13)
* **Git Engine & PR Diff Engine**: Parses Git diffs and maps every changed line to its enclosing function, class, and symbol.
* **Change Impact Analysis Engine**: Traverses repository graphs to calculate downstream caller impact and affected files.

### 6. Deterministic Review Engine (Phase 14)
* **Deterministic Rule Set**: Flags complexity, length, security, and architecture breaches, generating structured findings, inline comments, and review verdicts (`APPROVE`, `REQUEST_CHANGES`, `COMMENT`) without AI.

### 7. GitHub Integration & Webhooks (Phase 15)
* **GitHub Webhooks & App Auth**: HMAC SHA-256 webhook signature verification (`X-Hub-Signature-256`), PR event parsing (`pull_request`, `synchronize`, `reopened`), and Markdown review publishing.

### 8. AI Review Engine with Provider Abstraction (Phase 16)
* **`LLMProvider` Abstraction**: Pluggable interface supporting **Anthropic Claude**, **OpenAI GPT-4o**, **Google Gemini**, **Ollama**, and **MockLLMProvider** interchangeably.
* **Model & Prompt Registries**: `ModelRegistry` (versioned model specs and USD token pricing) and `PromptRegistry` (versioned prompt templates).

### 9. Context Assembly & Retrieval (Phase 17)
* **`ContextBuilder`**: Assembles targeted prompt sections for modified symbols, dependencies, metrics, security findings, and PR diffs within a configurable token budget (e.g. 16k token limit) without vector DBs.

### 10. LangGraph Review Workflow (Phase 18)
* **`LangGraphReviewWorkflow`**: Coordinates review steps using `langgraph` StateGraph with parallel fan-out nodes (`BuildContext`, `AnalyzeArchitecture`, `AnalyzePerformance`, `AnalyzeSecurity`, `AnalyzeMaintainability`) and reducer state.

### 11. Multi-Agent Review System (Phase 19)
* **Specialized AI Reviewers**: Domain-focused agents (**Architecture**, **Security**, **Performance**, **Maintainability**, **Testing**, **Documentation**).
* **`ReviewCoordinator`**: Concurrent agent execution, finding aggregation, deduplication, and severity ranking.

### 12. Enterprise Platform & AI Evaluation Layer (Phase 20)
* **`AIEvaluationEngine`**: Evaluates AI review precision, recall, latency, token efficiency, and false positive/negative rates against ground truth.
* **Enterprise Infrastructure**: `ReviewCacheService`, `ReviewStorageRepository`, `TelemetryTracker` (cost and token usage tracking), and `BackgroundJobQueue`.

---

## Installation & Setup

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Environment Configuration
Copy `.env.example` to `.env` and supply your optional LLM API keys:

```bash
# Add optional LLM provider API keys:
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

---

## Running Tests

Execute the complete 66-case automated test suite:

```bash
python -m pytest -v
```

---

## Running the API Server

Start the FastAPI application:

```bash
uvicorn app.api.main:app --reload --port 8000
```

Access Interactive API Documentation at `http://localhost:8000/docs`.

---

## License

MIT License.
