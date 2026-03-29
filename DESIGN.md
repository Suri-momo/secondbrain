# 🎨 StudySync — System Design Document

> **Last Updated:** 2024-03-29
> **Status:** 📝 Planning Phase
> **Version:** 1.0

---

## 📋 Table of Contents

1. [Overview](#-overview)
2. [System Architecture](#-system-architecture)
3. [Data Models](#-data-models)
4. [API Design](#-api-design)
5. [Frontend Architecture](#-frontend-architecture)
6. [Backend Architecture](#-backend-architecture)
7. [Data Flow](#-data-flow)
8. [Security & Performance](#-security--performance)
9. [Technology Stack](#-technology-stack)
10. [Deployment Architecture](#-deployment-architecture)

---

## 🎯 Overview

### What is StudySync?

StudySync is a **conversational AI study assistant** that helps students learn from multiple content sources (PDFs, audio, URLs) through natural dialogue with Claude AI.

### Core Value Proposition

> 💡 **Replace 5 tools with 1 interface**
> Upload documents → Ask questions → Get AI-powered answers → Generate summaries → Listen to audio

### Key Metrics

| Metric | Target |
|--------|--------|
| 🚀 First token latency | < 2 seconds |
| 📄 File processing time | < 10 seconds (50MB) |
| 💾 Context window | 4,000 characters |
| 📊 Test coverage | ≥ 80% |
| 🔄 Conversation history | Last 20 messages |

---

## 🏗️ System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Next.js 14 Frontend (Port 3000)             │   │
│  │                                                          │   │
│  │  • React Components (UI)                                │   │
│  │  • TanStack Query (Server State)                        │   │
│  │  • Zustand (Client State)                               │   │
│  │  • SSE Client (Streaming)                               │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/HTTPS
                             │ SSE Streaming
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API Gateway                           │   │
│  │  • CORS Middleware                                       │   │
│  │  • Request Validation (Pydantic)                         │   │
│  │  • Error Handling                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             │                                   │
│  ┌──────────────────────────┼────────────────────────────────┐  │
│  │         Routers          │                                │  │
│  │  • conversations.py      │                                │  │
│  │  • messages.py           │                                │  │
│  │  • documents.py          │                                │  │
│  │  • summaries.py          │                                │  │
│  └──────────────────────────┼────────────────────────────────┘  │
│                             │                                   │
│  ┌──────────────────────────┼────────────────────────────────┐  │
│  │         Services         │                                │  │
│  │  • claude_service.py ────┼───► Anthropic API              │  │
│  │  • document_service.py   │                                │  │
│  │  • audio_service.py ─────┼───► OpenAI Whisper API         │  │
│  │  • tts_service.py ───────┼───► OpenAI TTS API             │  │
│  │  • search_service.py ────┼───► Tavily Search API          │  │
│  │  • url_service.py ───────┼───► httpx + BeautifulSoup      │  │
│  │  • summary_service.py    │                                │  │
│  └──────────────────────────┼────────────────────────────────┘  │
│                             │                                   │
│  ┌──────────────────────────▼────────────────────────────────┐  │
│  │              SQLAlchemy ORM                              │  │
│  └──────────────────────────┬────────────────────────────────┘  │
└────────────────────────────┬┬────────────────────────────────────┘
                             ││
                             ▼▼
┌─────────────────────────────────────────────────────────────────┐
│                    SQLite Database                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Tables:                                                 │   │
│  │  • conversations (id, title, created_at, updated_at)     │   │
│  │  • messages (id, conversation_id, role, content, ...)    │   │
│  │  • documents (id, conversation_id, filename, text, ...)  │   │
│  │  • summaries (id, conversation_id, text, audio_url, ...) │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

External APIs:
  🤖 Anthropic Claude API (streaming chat)
  🎙️ OpenAI Whisper API (audio transcription)
  🔊 OpenAI TTS API (text-to-speech)
  🔍 Tavily Search API (web search)
```

### Architecture Principles

> ✅ **Monorepo**: Frontend + Backend in one repository
> ✅ **API-First**: Backend exposes RESTful API + SSE streaming
> ✅ **State Separation**: Server state (TanStack Query) vs Client state (Zustand)
> ✅ **Streaming-First**: SSE for real-time token-by-token responses
> ✅ **Simple MVP**: SQLite, no vector DB, naive context truncation

---

## 🗄️ Data Models

### Entity Relationship Diagram

```
┌─────────────────────┐
│   Conversation      │
│─────────────────────│
│ • id (PK)           │
│ • title             │
│ • created_at        │
│ • updated_at        │
└──────────┬──────────┘
           │ 1
           │
           │ has many
           │
           ├─────────────────┬─────────────────┐
           │                 │                 │
           │ *               │ *               │ *
┌──────────▼──────────┐ ┌────▼─────────────┐ ┌▼─────────────────┐
│   Message           │ │   Document       │ │   Summary        │
│─────────────────────│ │──────────────────│ │──────────────────│
│ • id (PK)           │ │ • id (PK)        │ │ • id (PK)        │
│ • conversation_id   │ │ • conversation_id│ │ • conversation_id│
│ • role (enum)       │ │ • filename       │ │ • summary_text   │
│ • content (text)    │ │ • file_type      │ │ • audio_url      │
│ • sources (JSON)    │ │ • extracted_text │ │ • audio_duration │
│ • created_at        │ │ • created_at     │ │ • voice          │
└─────────────────────┘ └──────────────────┘ │ • created_at     │
                                             └──────────────────┘
```

### Detailed Schema

#### 📝 Conversation

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier |
| `title` | String(255) | NOT NULL | Auto-generated from first message |
| `created_at` | DateTime | NOT NULL, DEFAULT NOW | When conversation was created |
| `updated_at` | DateTime | NOT NULL, ON UPDATE | Last message timestamp |

**Indexes:**
- `idx_conversations_updated_at` on `updated_at DESC` (for sidebar sorting)

---

#### 💬 Message

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier |
| `conversation_id` | UUID | FOREIGN KEY, NOT NULL | References conversations(id) ON DELETE CASCADE |
| `role` | Enum | NOT NULL | 'user' or 'assistant' |
| `content` | Text | NOT NULL | Message content (markdown for assistant) |
| `sources` | JSON | NULLABLE | Web search results: `[{title, url, snippet}]` |
| `created_at` | DateTime | NOT NULL, DEFAULT NOW | Message timestamp |

**Indexes:**
- `idx_messages_conversation_created` on `(conversation_id, created_at DESC)` (for history fetching)

---

#### 📄 Document

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier |
| `conversation_id` | UUID | FOREIGN KEY, NOT NULL | References conversations(id) ON DELETE CASCADE |
| `filename` | String(255) | NOT NULL | Original filename |
| `file_type` | Enum | NOT NULL | 'pdf', 'txt', 'audio', 'url' |
| `extracted_text` | Text | NOT NULL | Parsed/transcribed text |
| `created_at` | DateTime | NOT NULL, DEFAULT NOW | Upload timestamp |

**Indexes:**
- `idx_documents_conversation` on `conversation_id` (for context fetching)

---

#### 📊 Summary

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier |
| `conversation_id` | UUID | FOREIGN KEY, NOT NULL | References conversations(id) ON DELETE CASCADE |
| `summary_text` | Text | NOT NULL | 2-5 min summary (300-750 words) |
| `audio_url` | String(500) | NULLABLE | Path to generated MP3 file |
| `audio_duration` | Integer | NULLABLE | Duration in seconds |
| `voice` | String(50) | DEFAULT 'alloy' | OpenAI TTS voice |
| `created_at` | DateTime | NOT NULL, DEFAULT NOW | Generation timestamp |

**Indexes:**
- `idx_summaries_conversation` on `conversation_id` (one summary per conversation)

---

## 🔌 API Design

### REST Endpoints Overview

| Method | Endpoint | Purpose | Response |
|--------|----------|---------|----------|
| GET | `/api/conversations` | List all conversations | JSON array |
| POST | `/api/conversations` | Create new conversation | JSON object (201) |
| PATCH | `/api/conversations/{id}` | Rename conversation | JSON object (200) |
| DELETE | `/api/conversations/{id}` | Delete conversation | 204 No Content |
| GET | `/api/conversations/{id}/messages` | Get message history | JSON array |
| POST | `/api/conversations/{id}/chat` | Send message (streaming) | **SSE stream** |
| POST | `/api/conversations/{id}/upload` | Upload file | JSON object (201) |
| POST | `/api/conversations/{id}/url` | Ingest URL | JSON object (201) |
| POST | `/api/conversations/{id}/summary` | Generate summary | JSON object (201) |
| POST | `/api/conversations/{id}/summary/audio` | Generate TTS audio | JSON object (201) |
| GET | `/api/conversations/{id}/summary/audio/{audio_id}` | Download MP3 | Binary (MP3) |
| POST | `/api/search` | Standalone web search | JSON array |
| GET | `/api/health` | Health check | JSON object |

---

### Detailed Endpoint Specifications

#### 📝 Create Conversation

```http
POST /api/conversations
Content-Type: application/json

{
  "title": "Biology Midterm Study"  // Optional, auto-generated if omitted
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Biology Midterm Study",
  "created_at": "2024-03-29T12:00:00Z",
  "updated_at": "2024-03-29T12:00:00Z"
}
```

---

#### 💬 Send Chat Message (Streaming)

```http
POST /api/conversations/{id}/chat
Content-Type: application/json

{
  "content": "What is photosynthesis?",
  "use_search": false  // Optional, default false
}
```

**Response (200 OK):**
```http
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"type": "token", "content": "Photo"}
data: {"type": "token", "content": "synthesis"}
data: {"type": "token", "content": " is"}
data: {"type": "token", "content": " the"}
data: {"type": "token", "content": " process"}
...
data: {"type": "done", "message_id": "msg-123"}
```

> ⚠️ **Note:** This is a Server-Sent Events (SSE) stream, not regular JSON

---

#### 📄 Upload File

```http
POST /api/conversations/{id}/upload
Content-Type: multipart/form-data

file: <binary file data>
```

**Response (201 Created):**
```json
{
  "id": "doc-123",
  "conversation_id": "conv-456",
  "filename": "chapter5.pdf",
  "file_type": "pdf",
  "extracted_text": "Chapter 5: Photosynthesis...",
  "created_at": "2024-03-29T12:05:00Z"
}
```

**Supported File Types:**
- 📕 PDF (`.pdf`)
- 📄 Text (`.txt`)
- 🎵 Audio (`.mp3`, `.wav`, `.m4a`)

**Validation:**
- Max file size: 50MB
- Returns `413 Payload Too Large` if exceeded
- Returns `422 Unprocessable Entity` for unsupported types

---

#### 🔍 Web Search

```http
POST /api/search
Content-Type: application/json

{
  "query": "latest photosynthesis research 2024"
}
```

**Response (200 OK):**
```json
[
  {
    "title": "New Photosynthesis Mechanism Discovered",
    "url": "https://science.org/article/123",
    "snippet": "Researchers have identified a previously unknown pathway..."
  },
  {
    "title": "Advances in Artificial Photosynthesis",
    "url": "https://nature.com/article/456",
    "snippet": "Scientists achieve breakthrough in mimicking plant..."
  }
]
```

---

#### 📊 Generate Summary

```http
POST /api/conversations/{id}/summary
Content-Type: application/json

{
  "max_length": 750  // Optional, default 750 words (2-5 min read)
}
```

**Response (201 Created):**
```json
{
  "id": "summary-789",
  "conversation_id": "conv-456",
  "summary_text": "## Key Points\n\n- Photosynthesis converts light...",
  "audio_url": null,
  "audio_duration": null,
  "created_at": "2024-03-29T12:10:00Z"
}
```

---

#### 🔊 Generate TTS Audio

```http
POST /api/conversations/{id}/summary/audio
Content-Type: application/json

{
  "voice": "alloy"  // Optional: alloy, echo, fable, onyx, nova, shimmer
}
```

**Response (201 Created):**
```json
{
  "id": "summary-789",
  "audio_url": "/api/conversations/conv-456/summary/audio/summary-789.mp3",
  "audio_duration": 180,  // seconds
  "voice": "alloy"
}
```

---

### Error Responses

All errors follow this format:

```json
{
  "detail": "Human-readable error message",
  "status_code": 422,
  "error_type": "ValidationError"
}
```

**Common Status Codes:**
- `400` Bad Request - Invalid request body
- `404` Not Found - Resource doesn't exist
- `413` Payload Too Large - File exceeds 50MB
- `422` Unprocessable Entity - Validation failed
- `500` Internal Server Error - Unexpected error

---

## 🎨 Frontend Architecture

### Component Hierarchy

```
App (layout.tsx)
│
├─ Sidebar
│  ├─ SidebarItem (conversation)
│  │  └─ DeleteButton
│  └─ NewChatButton
│
└─ ChatPage ([conversationId]/page.tsx)
   │
   ├─ ChatWindow
   │  │
   │  ├─ ChatHeader
   │  │  └─ SummaryButton
   │  │
   │  ├─ MessageList
   │  │  └─ MessageBubble
   │  │     ├─ MessageContent (react-markdown)
   │  │     ├─ SourceCard (if sources exist)
   │  │     └─ TypingIndicator (if streaming)
   │  │
   │  ├─ SummaryDisplay (if summary exists)
   │  │  ├─ SummaryText (markdown)
   │  │  └─ AudioPlayer
   │  │     ├─ PlayPauseButton
   │  │     ├─ SeekBar
   │  │     ├─ PlaybackSpeedSelector
   │  │     └─ DownloadButton
   │  │
   │  └─ ChatInput
   │     ├─ Textarea
   │     ├─ UploadButton → UploadZone (modal)
   │     ├─ UrlButton → UrlInput (modal)
   │     ├─ SearchToggle
   │     └─ SendButton
   │
   └─ UploadZone (drag & drop overlay)
      └─ UploadProgress
```

### State Management Strategy

#### Server State (TanStack Query)

> 🔄 **Handles all API data fetching and caching**

```typescript
// Conversations list
useQuery({
  queryKey: ['conversations'],
  queryFn: fetchConversations,
  staleTime: 5 * 60 * 1000, // 5 minutes
})

// Message history
useQuery({
  queryKey: ['messages', conversationId],
  queryFn: () => fetchMessages(conversationId),
  staleTime: 30 * 1000, // 30 seconds
})

// Create conversation mutation
useMutation({
  mutationFn: createConversation,
  onSuccess: () => {
    queryClient.invalidateQueries(['conversations'])
  }
})
```

**Key Patterns:**
- Query keys: `['resource', id?]`
- Automatic refetching on window focus
- Cache invalidation on mutations
- Optimistic updates for create/delete

---

#### Client State (Zustand)

> 📦 **Handles UI-only state (streaming, input, modals)**

```typescript
interface ChatStore {
  // Streaming state
  isStreaming: boolean
  streamingMessageId: string | null
  currentToken: string

  // Input state
  inputValue: string
  isSearchEnabled: boolean

  // Upload state
  uploadProgress: number
  isUploadModalOpen: boolean

  // Actions
  setIsStreaming: (value: boolean) => void
  appendToken: (token: string) => void
  setInputValue: (value: string) => void
  // ...
}
```

**Why This Split?**

| State Type | Manager | Reason |
|------------|---------|--------|
| Conversations list | TanStack Query | Fetched from API, cacheable |
| Message history | TanStack Query | Fetched from API, cacheable |
| Streaming tokens | Zustand | Ephemeral, not persisted |
| Text input value | Zustand | Local UI state |
| Modal open/close | Zustand | Local UI state |

---

### Routing Structure

```
app/
├─ layout.tsx              → Root layout with sidebar
├─ page.tsx                → Redirects to /chat
└─ chat/
   ├─ page.tsx             → Empty state "New Chat"
   └─ [conversationId]/
      └─ page.tsx          → Active conversation
```

**Route Behavior:**
- `/` → Redirect to `/chat`
- `/chat` → Empty state with "Start a new conversation"
- `/chat/abc-123` → Load conversation `abc-123` with history

---

## ⚙️ Backend Architecture

### Service Layer Pattern

Each service is **stateless** and **mockable** for testing:

```python
# services/claude_service.py
async def stream_response(
    conversation_id: UUID,
    user_message: str,
    use_search: bool = False
) -> AsyncGenerator[str, None]:
    """
    Streams Claude's response token-by-token.

    Steps:
    1. Fetch documents for context
    2. Fetch last 20 messages for history
    3. Optionally fetch web search results
    4. Build system prompt
    5. Stream response from Claude API
    6. Yield tokens as they arrive
    """
    context = await document_service.get_context(conversation_id)
    history = await get_message_history(conversation_id, limit=20)

    if use_search:
        search_results = await search_service.search(user_message)

    system_prompt = build_prompt(context, history, search_results)

    async with anthropic.messages.stream(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": user_message}],
        system=system_prompt,
        max_tokens=4096
    ) as stream:
        async for text in stream.text_stream:
            yield text
```

---

### Router Layer Pattern

Routers handle HTTP concerns (request/response, validation):

```python
# routers/messages.py
@router.post("/conversations/{id}/chat")
async def send_chat_message(
    id: UUID,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Streams Claude's response via SSE.

    Returns:
        SSE stream (text/event-stream)
    """
    # Save user message to DB
    user_msg = Message(
        conversation_id=id,
        role="user",
        content=request.content
    )
    db.add(user_msg)
    db.commit()

    # Stream response
    async def event_generator():
        full_response = ""

        async for token in claude_service.stream_response(
            conversation_id=id,
            user_message=request.content,
            use_search=request.use_search
        ):
            full_response += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        # Save assistant message to DB
        assistant_msg = Message(
            conversation_id=id,
            role="assistant",
            content=full_response
        )
        db.add(assistant_msg)
        db.commit()

        yield f"data: {json.dumps({'type': 'done', 'message_id': str(assistant_msg.id)})}\n\n"

    return EventSourceResponse(event_generator())
```

---

### Dependency Injection

```python
# database.py
def get_db():
    """Provides database session to routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Usage in routes
@router.get("/conversations")
def list_conversations(db: Session = Depends(get_db)):
    return db.query(Conversation).order_by(Conversation.updated_at.desc()).all()
```

---

## 🔄 Data Flow

### Complete User Journey

#### 1️⃣ Upload PDF → Chat → Response

```
┌─────────┐                              ┌─────────┐
│ Browser │                              │ Backend │
└────┬────┘                              └────┬────┘
     │                                        │
     │ 1. POST /conversations                 │
     │───────────────────────────────────────>│
     │                                        │
     │ 201 {"id": "conv-123"}                 │
     │<───────────────────────────────────────│
     │                                        │
     │ 2. POST /conversations/conv-123/upload │
     │    (multipart: chapter5.pdf)           │
     │───────────────────────────────────────>│
     │                                        │ 3. Parse PDF
     │                                        │    (pypdf)
     │                                        │
     │ 201 {"extracted_text": "..."}          │
     │<───────────────────────────────────────│
     │                                        │
     │ 4. POST /conversations/conv-123/chat   │
     │    {"content": "What is photosynthesis?"}
     │───────────────────────────────────────>│
     │                                        │ 5. Fetch documents
     │                                        │    (get context)
     │                                        │
     │                                        │ 6. Fetch history
     │                                        │    (last 20 msgs)
     │                                        │
     │                                        │ 7. Call Claude API
     │                                        │    (with context)
     │                                        │
     │ SSE: data: {"type": "token", ...}      │
     │<───────────────────────────────────────│ 8. Stream tokens
     │ SSE: data: {"type": "token", ...}      │
     │<───────────────────────────────────────│
     │ ...                                    │
     │ SSE: data: {"type": "done"}            │
     │<───────────────────────────────────────│
     │                                        │ 9. Save messages
     │                                        │    to DB
```

---

#### 2️⃣ Generate Summary → TTS → Play Audio

```
┌─────────┐                              ┌─────────┐
│ Browser │                              │ Backend │
└────┬────┘                              └────┬────┘
     │                                        │
     │ 1. POST /conversations/conv-123/summary│
     │───────────────────────────────────────>│
     │                                        │ 2. Fetch documents
     │                                        │    + messages
     │                                        │
     │                                        │ 3. Call Claude API
     │                                        │    (summarize)
     │                                        │
     │ 201 {"summary_text": "...", ...}       │
     │<───────────────────────────────────────│
     │                                        │
     │ 2. POST .../summary/audio              │
     │    {"voice": "alloy"}                  │
     │───────────────────────────────────────>│
     │                                        │ 4. Call OpenAI TTS
     │                                        │    (text → MP3)
     │                                        │
     │                                        │ 5. Save MP3 file
     │                                        │    to uploads/
     │                                        │
     │ 201 {"audio_url": "/api/.../audio.mp3"}│
     │<───────────────────────────────────────│
     │                                        │
     │ 3. GET .../audio/summary-789.mp3       │
     │───────────────────────────────────────>│
     │                                        │ 6. Stream MP3
     │ 200 <binary MP3 data>                  │    file
     │<───────────────────────────────────────│
     │                                        │
     │ 4. <audio> element plays in browser    │
```

---

## 🔒 Security & Performance

### Security Considerations

> 🔐 **API Keys**

- ✅ All API keys stored in `.env` (never committed)
- ✅ Backend-only access (never exposed to frontend)
- ✅ `NEXT_PUBLIC_*` variables contain NO secrets

> 🛡️ **Input Validation**

- ✅ Pydantic schemas validate all request bodies
- ✅ File type validation (PDF, TXT, audio only)
- ✅ File size limits (50MB max)
- ✅ SQL injection prevented (SQLAlchemy ORM)

> 🌐 **CORS**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)
```

> 🚫 **No Authentication in MVP**

- Single-user local application
- No user accounts or login system
- All conversations belong to one implicit user

---

### Performance Optimizations

#### Backend

| Optimization | Implementation | Impact |
|--------------|----------------|--------|
| **Context Truncation** | Limit to 4,000 chars | Reduces API costs + latency |
| **History Windowing** | Last 20 messages only | Faster queries, smaller payloads |
| **Database Indexes** | On conversation_id, created_at | 10x faster queries |
| **Async I/O** | FastAPI + async/await | Non-blocking API calls |

#### Frontend

| Optimization | Implementation | Impact |
|--------------|----------------|--------|
| **Code Splitting** | `next/dynamic` for heavy components | 40% smaller initial bundle |
| **Optimistic UI** | User messages appear instantly | Perceived 0ms latency |
| **Query Caching** | TanStack Query with staleTime | Reduces redundant API calls |
| **Streaming** | SSE token-by-token | Faster perceived response time |

---

## 💻 Technology Stack

### Frontend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 14.x | React framework (App Router) |
| **React** | 18.x | UI library |
| **TypeScript** | 5.x | Type safety |
| **Tailwind CSS** | 3.x | Styling |
| **TanStack Query** | 5.x | Server state management |
| **Zustand** | 4.x | Client state management |
| **react-markdown** | 9.x | Markdown rendering |
| **lucide-react** | Latest | Icon library |

**Dev Dependencies:**
- Jest + React Testing Library (unit tests)
- Playwright (E2E tests)
- ESLint + Prettier (linting/formatting)

---

### Backend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Language |
| **FastAPI** | 0.104+ | Web framework |
| **SQLAlchemy** | 2.0+ | ORM |
| **Alembic** | 1.12+ | Database migrations |
| **Pydantic** | 2.x | Data validation |
| **anthropic** | Latest | Claude API client |
| **openai** | Latest | Whisper + TTS APIs |
| **tavily-python** | Latest | Web search |
| **httpx** | Latest | HTTP client |
| **beautifulsoup4** | Latest | HTML parsing |
| **pypdf** | Latest | PDF parsing |

**Dev Dependencies:**
- pytest + pytest-asyncio (testing)
- ruff (linting/formatting)
- mypy (type checking)

---

### External APIs

| Service | Purpose | Cost |
|---------|---------|------|
| **Anthropic Claude** | Conversational AI | ~$15/1M tokens |
| **OpenAI Whisper** | Audio transcription | ~$0.006/minute |
| **OpenAI TTS** | Text-to-speech | ~$15/1M chars |
| **Tavily Search** | Web search | ~$0.001/search |

---

## 🚀 Deployment Architecture

### Production Deployment (Vercel)

```
┌─────────────────────────────────────────────────────────────┐
│                     Vercel Edge Network                     │
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Next.js 14 Frontend (SSG + SSR)            │    │
│  │  • Static pages pre-rendered                       │    │
│  │  • API routes proxied to backend                   │    │
│  │  • CDN caching for assets                          │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                  │
│                          │ Proxied                          │
│                          ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │    FastAPI Backend (Serverless Function)           │    │
│  │  • Auto-scaling                                     │    │
│  │  • 10s execution limit (sufficient for SSE)        │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Vercel Postgres (Production)               │
│  • Managed PostgreSQL                                       │
│  • Automatic backups                                        │
│  • Connection pooling                                       │
└─────────────────────────────────────────────────────────────┘
```

### Environment Variables

**Production:**
```bash
# .env.production
DATABASE_URL=postgresql://vercel:***@***
ANTHROPIC_API_KEY=sk-ant-***
OPENAI_API_KEY=sk-***
TAVILY_API_KEY=tvly-***
NEXT_PUBLIC_API_URL=https://studysync.vercel.app
```

**Development:**
```bash
# .env.local
DATABASE_URL=sqlite:///./studysync.db
ANTHROPIC_API_KEY=sk-ant-test-***
OPENAI_API_KEY=sk-test-***
TAVILY_API_KEY=tvly-test-***
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

### CI/CD Pipeline

```
GitHub Push → GitHub Actions → Run Tests → Deploy to Vercel
                                  ↓
                        ┌─────────┴─────────┐
                        │                   │
                   Backend Tests      Frontend Tests
                        │                   │
                        ├─ Unit Tests       ├─ Unit Tests
                        ├─ Integration      ├─ Component Tests
                        └─ E2E Tests ←──────┴─ E2E Tests
                                  │
                                  ↓
                            All Green? → Deploy
                            All Red?   → Block PR
```

---

## 📚 References & Resources

### Documentation Links
- [Next.js 14 Docs](https://nextjs.org/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Anthropic API Docs](https://docs.anthropic.com/)
- [TanStack Query Docs](https://tanstack.com/query/latest)

### Design Inspiration
- ChatGPT interface patterns
- Notion's clean documentation style
- Linear's minimal UI aesthetic

---

**Last Updated:** 2024-03-29 12:30 UTC
**Next Review:** After Milestone 1.2 (Database Foundation)
