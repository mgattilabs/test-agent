# Clean Architecture Implementation

This document explains the clean architecture refactor applied to the codebase, following clean code principles and Python philosophy.

## Architecture Overview

The codebase is organized in layers, each with a single responsibility and clear dependencies:

```
┌─────────────────────────────────────┐
│         API Layer (FastAPI)          │  ← Presentation/Interface
├─────────────────────────────────────┤
│        Use Cases (Business Logic)    │  ← Application Layer
├─────────────────────────────────────┤
│    Domain (Entities, Interfaces)     │  ← Core Business Rules
├─────────────────────────────────────┤
│  Infrastructure (External Services)  │  ← Frameworks & Drivers
└─────────────────────────────────────┘
```

## Layer Structure

### 1. Domain Layer (`src/domain/`)

**Purpose**: Core business logic and rules, framework-independent.

**Contents**:
- `entities.py`: Business entities (ChatSession, PBI, ChatMessage)
- `repositories.py`: Repository interfaces (ports)
- `services.py`: Service interfaces (ports)

**Principles**:
- ✅ No dependencies on external frameworks
- ✅ Pure business logic
- ✅ Defines interfaces (ports) that infrastructure implements
- ✅ Entities with behavior (not anemic models)

**Example**:
```python
@dataclass
class ChatSession:
    """Aggregate root with business logic."""
    
    def add_message(self, role: MessageRole, content: str) -> ChatMessage:
        """Business logic for adding messages."""
        message = ChatMessage(role=role, content=content)
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message
    
    def is_complete(self) -> bool:
        """Business rule: session is complete when it has project and PBIs."""
        return self.project is not None and len(self.pbis) > 0
```

### 2. Use Cases Layer (`src/use_cases/`)

**Purpose**: Application-specific business logic, orchestration.

**Contents**:
- `chat_session_use_cases.py`: Use cases for chat operations

**Principles**:
- ✅ Orchestrates domain entities
- ✅ Independent of delivery mechanism (API, CLI, etc.)
- ✅ Uses dependency injection
- ✅ Single responsibility per use case

**Example**:
```python
@dataclass
class AddMessageUseCase:
    """Single responsibility: add message and analyze."""
    
    repository: ChatSessionRepository
    pbi_extraction: PBIExtractionService
    project_extraction: ProjectExtractionService
    
    def execute(self, chat_id: UUID, role: MessageRole, content: str):
        session = self.repository.get_by_id(chat_id)
        session.add_message(role, content)
        # ... orchestration logic ...
        self.repository.save(session)
```

### 3. Infrastructure Layer (`src/infrastructure/`)

**Purpose**: Implementation of external services and repositories.

**Contents**:
- `repositories/in_memory_chat_repository.py`: In-memory storage
- `services/dspy_extraction_service.py`: DSPy extraction implementation
- `services/azdo_service.py`: Azure DevOps client

**Principles**:
- ✅ Implements domain interfaces (adapters)
- ✅ Contains framework-specific code
- ✅ Can be replaced without affecting domain/use cases

**Example**:
```python
class InMemoryChatRepository(ChatSessionRepository):
    """Adapter implementing domain interface."""
    
    def save(self, session: ChatSession) -> None:
        self._sessions[session.chat_id] = session
```

### 4. API Layer (`src/api/`)

**Purpose**: FastAPI controllers and request/response models.

**Contents**:
- `routes.py`: FastAPI endpoints
- `dtos.py`: Request/Response models (Pydantic)
- `mappers.py`: Convert between domain and DTOs
- `dependencies.py`: Dependency injection container

**Principles**:
- ✅ Thin controllers (delegate to use cases)
- ✅ DTOs separate from domain entities
- ✅ Explicit dependency injection
- ✅ Framework-specific concerns only

**Example**:
```python
@router.post("/{chat_id}/messages")
async def add_message(
    chat_id: UUID,
    request: AddMessageRequest,
    use_case: AddMessageUseCase = Depends(get_add_message_use_case),
):
    """Thin controller - delegates to use case."""
    session, response = use_case.execute(chat_id, role, content)
    return map_to_dto(session, response)
```

## Dependency Flow

```
API → Use Cases → Domain ← Infrastructure
    ↑                            ↓
    └────────────────────────────┘
       (Dependency Inversion)
```

**Key Principle**: Dependencies point inward. The domain has no dependencies on outer layers.

## Python Philosophy Applied

### 1. "Explicit is better than implicit"
- ✅ Clear dependency injection (no hidden globals)
- ✅ Explicit error handling
- ✅ Type hints everywhere

```python
# Bad (implicit)
session = chat_manager.get_session(id)  # Where does chat_manager come from?

# Good (explicit)
@dataclass
class GetSessionUseCase:
    repository: ChatSessionRepository  # Dependency is explicit
    
    def execute(self, chat_id: UUID):
        return self.repository.get_by_id(chat_id)
```

### 2. "Simple is better than complex"
- ✅ Small, focused classes (Single Responsibility)
- ✅ Clear method names
- ✅ Minimal inheritance

```python
# Each use case has one clear responsibility
CreateChatSessionUseCase
AddMessageUseCase
ConfirmPBICreationUseCase
```

### 3. "Readability counts"
- ✅ Descriptive names
- ✅ Docstrings
- ✅ Type annotations

```python
def execute(self, chat_id: UUID, role: MessageRole, content: str) -> tuple[ChatSession, str | None]:
    """
    Execute the use case.
    
    Returns:
        tuple: (updated_session, assistant_response)
    """
```

### 4. "Errors should never pass silently"
- ✅ Proper exception handling
- ✅ Logging
- ✅ Meaningful error messages

```python
try:
    self.azdo_service.create_pbis(...)
except Exception as e:
    logger.error(f"Error creating PBIs: {e}", exc_info=True)
    session.update_status(SessionStatus.ERROR)
    raise
```

## Benefits of This Architecture

### 1. Testability
Each layer can be tested independently:
- Domain: Pure unit tests (no mocks needed)
- Use Cases: Test with mock repositories
- Infrastructure: Integration tests
- API: E2E tests

### 2. Maintainability
- Changes in one layer don't affect others
- Easy to locate and fix bugs
- Clear responsibility boundaries

### 3. Flexibility
- Can replace infrastructure (e.g., swap in-memory for database)
- Can add new interfaces (CLI, gRPC) without changing business logic
- Can change frameworks without affecting domain

### 4. Team Scalability
- Teams can work on different layers independently
- Clear contracts (interfaces) between layers
- Easier onboarding (each layer is understandable in isolation)

## Migration Strategy

The new architecture coexists with the old code:

1. **New API**: `server_api_v2.py` (clean architecture)
2. **Old API**: `server_api.py` (legacy, can be gradually migrated)

### Running the Clean Architecture Version

```bash
# Start the new clean architecture API
uvicorn src.server_api_v2:app --reload --host 0.0.0.0 --port 8000
```

### Gradual Migration

1. New features → implement in clean architecture
2. Bug fixes → refactor to clean architecture if practical
3. Eventually deprecate old API

## Directory Structure

```
src/
├── domain/                    # Core business layer
│   ├── __init__.py
│   ├── entities.py           # Business entities
│   ├── repositories.py       # Repository interfaces
│   └── services.py           # Service interfaces
│
├── use_cases/                 # Application layer
│   ├── __init__.py
│   └── chat_session_use_cases.py
│
├── infrastructure/            # External services layer
│   ├── __init__.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── in_memory_chat_repository.py
│   └── services/
│       ├── __init__.py
│       ├── dspy_extraction_service.py
│       └── azdo_service.py
│
├── api/                       # Presentation layer
│   ├── __init__.py
│   ├── routes.py             # FastAPI routes
│   ├── dtos.py               # Request/Response models
│   ├── mappers.py            # Domain ↔ DTO conversion
│   └── dependencies.py       # DI container
│
├── server_api_v2.py          # Clean architecture app
└── server_api.py             # Legacy app (to be migrated)
```

## Key Design Patterns Used

### 1. Repository Pattern
Abstracts data persistence:
```python
class ChatSessionRepository(ABC):
    @abstractmethod
    def save(self, session: ChatSession) -> None: ...
```

### 2. Dependency Injection
Explicit dependencies:
```python
@dataclass
class AddMessageUseCase:
    repository: ChatSessionRepository
    pbi_extraction: PBIExtractionService
    # Dependencies are injected, not created
```

### 3. Data Transfer Objects (DTOs)
Separate API models from domain:
```python
# API Layer
class ChatSessionDetailResponse(BaseModel): ...

# Domain Layer
@dataclass
class ChatSession: ...
```

### 4. Adapter Pattern
Infrastructure adapts to domain interfaces:
```python
class DSPyPBIExtractionService(PBIExtractionService):
    # Adapts DSPy to domain interface
```

## Further Reading

- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design](https://en.wikipedia.org/wiki/Domain-driven_design)
- [The Zen of Python](https://www.python.org/dev/peps/pep-0020/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
