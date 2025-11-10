# AI Coding Agent Instructions for dspy-test

## Project Overview
**dspy-test** is an AI-powered system that extracts Product Backlog Items (PBIs) from natural language summaries and automatically creates them in Azure DevOps. It combines DSPy (a framework for composing language models) with the Model Context Protocol (MCP) to enable AI-driven project management automation.

### Architecture
The system has two entry points:
- **MCP Server** (`src/server_mcp.py`): FastMCP-based service exposing `process_azdo_summary()` tool for AI integration
- **REST API** (`src/server_api.py`): FastAPI endpoint for HTTP access

Both use the same extraction pipeline via DSPy modules.

## Critical Data Flow

1. **Input**: Natural language summary (meeting notes, specifications)
2. **LLM Processing**: 
   - `GeminiService` (Google Gemini API) configured with DSPy to use `gemini/gemini-2.5-flash`
   - Two DSPy modules run in parallel:
     - `ExtractPBIModule`: Extracts structured PBIs (title + description) with ChainOfThought reasoning
     - `ExtractAzdoModule`: Identifies the target Azure DevOps project
3. **Azure DevOps Integration**: `azdo_client.add_pbi()` creates work items via Azure SDK
4. **Logging**: Request tracking with UUIDs, timestamps, and status tracking in `request_log` list

## Key Components & Patterns

### DSPy Modules (`src/extractors/`)
- **Base Pattern**: `dspy.Module` subclass with `forward()` method calling `dspy.ChainOfThought()`
- **Configuration**: Modules receive LLM via `.set_lm(gemini_service.lm)` after instantiation
- **Prompts**: Signatures contain system prompts in Italian (production language) defining extraction rules
  - PBI extraction requires breaking down overly generic items into specific, measurable sub-items
  - Signatures define `InputField` and `OutputField` with descriptions

### Settings & Environment
- **Config**: `src/config/settings.py` uses Pydantic `BaseSettings` with `.env` file support
- **Required Variables**: `GEMINI_API_KEY`, `AZDO_PERSONAL_ACCESS_TOKEN`, `AZDO_ORGANIZATION`
- **Pattern**: Load once at startup; pass to services (avoid repeated env reads)

### Azure DevOps Integration
- **Client**: `src/azdo_client.py` uses `azure-devops` SDK with `BasicAuthentication`
- **Pattern**: Each PBI creates separate work items with `JsonPatchOperation` for PATCH-based creation
- **Credentials**: Organization URL = `https://dev.azure.com/{organization}`

### Pydantic Models (`src/models.py`)
- Minimal, focused schemas: `PBI` (title/description), `Azdo` (project), `AgentResponse`
- Used for type safety across LLM outputs and API responses

## Developer Workflows

### Setup & Running
```bash
# Install dependencies (uses uv package manager)
uv sync

# Run MCP server (primary deployment)
fastmcp run src/server_mcp.py:mcp --transport http --host 0.0.0.0 --port 8000

# Docker deployment
docker build -t dspy-test .
docker run -e GEMINI_API_KEY=... -e AZDO_PERSONAL_ACCESS_TOKEN=... -e AZDO_ORGANIZATION=... -p 8000:8000 dspy-test
```

### Testing DSPy Modules Locally
- See `src/extractors/azdo.py` `if __name__ == "__main__"` block as example
- Create test summaries and call module directly: `azdo_module.forward(summary=test_text)`
- Verify LLM responses without full pipeline

### Adding New Extractors
1. Create `src/extractors/new_feature.py`
2. Define `dspy.Signature` subclass with Italian system prompt
3. Create extractor module with `.forward()` method
4. Import and configure in `server_mcp.py` and set LLM
5. Chain results in `process_azdo_summary()`

## Critical Conventions & Anti-Patterns

### ✓ Do
- Use DSPy `ChainOfThought` for multi-step reasoning (visible in LLM traces)
- Keep Italian prompts for Italian-language processing consistency
- Include request IDs (UUID) in logs for tracing end-to-end flows
- Load environment once at request start, pass through call stack
- **Place all imports at the top of each module** - organize as: stdlib → third-party → local imports

### ✗ Don't
- Don't create new `LM` instances per request (heavy initialization)
- Don't hardcode Azure organization/project in code (use settings)
- Don't modify `request_log` directly for persistence (it's in-memory only)
- Don't run extractors without `.set_lm()` - they'll fail silently
- **Don't scatter imports throughout module code** - keep them at module start for clarity and PEP 8 compliance

## Important Dependencies
- **dspy** (3.0.3): Language model framework with ChainOfThought reasoning
- **fastmcp** (2.13.0.2): Model Context Protocol server implementation
- **pydantic** (2.12.3): Data validation with BaseSettings for env support
- **azure-devops** (7.1.0b4): Azure DevOps API client
- **fastapi**: (Optional, for REST endpoint; not in pyproject but used in `server_api.py`)

## Cross-File Dependencies
```
server_mcp.py (entry point)
├── llm_client.py → GeminiService (initializes DSPy LM)
├── extractors/pbi.py → ExtractPBIModule
├── extractors/azdo.py → ExtractAzdoModule
├── azdo_client.py → add_pbi() (creates work items)
├── models.py → PBI, Azdo types
└── config/settings.py → EnvironmentSettings
```

## Known Quirks & Gotchas
1. **Import Path Inconsistency**: `server_mcp.py` imports `from src import azdo_client` but also `from extractors.pbi import ExtractPBIModule` (mixed relative/absolute) - maintain this pattern for compatibility
2. **In-Memory Request Log**: `request_log` list in `server_mcp.py` not persisted; only tracks current session
3. **Error Handling**: Exceptions in extraction propagate up (no graceful degradation) - callers must handle
4. **Gemini Model Hardcoded**: Default model is `gemini/gemini-2.5-flash` but configurable per `GeminiService` init
