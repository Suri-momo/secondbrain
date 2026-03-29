# SecondBrain: Implementation Plan

## Overview

SecondBrain is a full-stack conversational study assistant that ingests documents, audio, and URLs, then lets users chat about that content using Claude as the reasoning engine, with optional Tavily-powered web search and persistent multi-turn history stored in SQLite.

---

## 1. Full Project Directory Structure

```
secondbrain/
├── .github/
│   └── workflows/
│       └── ci.yml                          # GitHub Actions CI pipeline
├── .husky/
│   ├── pre-commit                          # Runs lint-staged before commit
│   └── pre-push                            # Runs tests before push
├── frontend/                               # Next.js 14 App Router
│   ├── .env.local.example
│   ├── .eslintrc.json
│   ├── .prettierrc
│   ├── jest.config.ts
│   ├── jest.setup.ts
│   ├── next.config.ts
│   ├── package.json
│   ├── playwright.config.ts
│   ├── postcss.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── public/
│   │   └── favicon.ico
│   ├── e2e/                                # Playwright end-to-end tests
│   │   ├── chat.spec.ts
│   │   ├── file-upload.spec.ts
│   │   └── sidebar.spec.ts
│   └── src/
│       ├── app/
│       │   ├── layout.tsx                  # Root layout (sidebar + main)
│       │   ├── page.tsx                    # Home: redirects to /chat
│       │   ├── globals.css
│       │   └── chat/
│       │       ├── page.tsx                # New chat page
│       │       └── [conversationId]/
│       │           └── page.tsx            # Existing conversation page
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Sidebar.tsx
│       │   │   ├── SidebarItem.tsx
│       │   │   └── Header.tsx
│       │   ├── chat/
│       │   │   ├── ChatWindow.tsx
│       │   │   ├── MessageList.tsx
│       │   │   ├── MessageBubble.tsx
│       │   │   ├── ChatInput.tsx
│       │   │   ├── SourceCard.tsx
│       │   │   └── TypingIndicator.tsx
│       │   ├── upload/
│       │   │   ├── UploadZone.tsx
│       │   │   ├── UrlInput.tsx
│       │   │   └── UploadProgress.tsx
│       │   ├── summary/
│       │   │   ├── SummaryButton.tsx
│       │   │   ├── SummaryDisplay.tsx
│       │   │   └── AudioPlayer.tsx
│       │   └── shared/
│       │       ├── Button.tsx
│       │       ├── Modal.tsx
│       │       └── Spinner.tsx
│       ├── hooks/
│       │   ├── useConversations.ts
│       │   ├── useMessages.ts
│       │   ├── useChat.ts
│       │   └── useUpload.ts
│       ├── lib/
│       │   ├── api.ts
│       │   └── stream.ts
│       ├── store/
│       │   └── chatStore.ts
│       └── types/
│           └── index.ts
├── backend/                                # Python FastAPI
│   ├── .env.example
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── uploads/
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 0001_initial.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── conversation.py
│   │   │   ├── message.py
│   │   │   ├── document.py
│   │   │   └── summary.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── conversation.py
│   │   │   ├── message.py
│   │   │   ├── document.py
│   │   │   └── summary.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── conversations.py
│   │   │   ├── messages.py
│   │   │   ├── documents.py
│   │   │   ├── search.py
│   │   │   └── summaries.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── claude_service.py
│   │       ├── document_service.py
│   │       ├── audio_service.py
│   │       ├── search_service.py
│   │       ├── url_service.py
│   │       ├── summary_service.py
│   │       └── tts_service.py
│   └── tests/
│       ├── conftest.py
│       ├── unit/
│       │   ├── test_document_service.py
│       │   ├── test_audio_service.py
│       │   ├── test_search_service.py
│       │   └── test_claude_service.py
│       └── integration/
│           ├── test_conversations_api.py
│           ├── test_messages_api.py
│           ├── test_documents_api.py
│           └── test_search_api.py
├── .gitignore
├── package.json                            # Root package.json for Husky
└── README.md
```

**Root `.gitignore`:**
```
# Environment
.env
.env.local
*.env

# Python
__pycache__/
*.py[cod]
*.so
.pytest_cache/
.mypy_cache/
.ruff_cache/
*.egg-info/

# Node
node_modules/
.next/
dist/
build/

# Databases & Uploads
*.db
*.sqlite
*.sqlite3
uploads/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

**Root `package.json`** (for Husky):
```json
{
  "name": "studysync-monorepo",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "prepare": "husky install",
    "lint": "npm run lint --workspace=frontend",
    "test": "npm run test --workspace=frontend && cd backend && pytest"
  },
  "workspaces": [
    "frontend"
  ],
  "devDependencies": {
    "husky": "^8.0.0",
    "lint-staged": "^15.0.0"
  }
}
```

---

## 2. Key Services and Responsibilities

### Backend Services

| File | Purpose |
|---|---|
| `app/main.py` | FastAPI app factory, CORS middleware, router registration |
| `app/config.py` | Pydantic Settings — all env vars validated at startup |
| `app/database.py` | SQLAlchemy engine, `SessionLocal`, `get_db` dependency |
| `app/services/claude_service.py` | Builds system prompt with document context + history, calls `anthropic.messages.stream()`, yields SSE chunks |
| `app/services/document_service.py` | PDF/TXT parsing via `pypdf`, chunking (512 tokens), context assembly (4000 chars max) |
| `app/services/audio_service.py` | Saves audio, calls OpenAI Whisper `/v1/audio/transcriptions`, returns transcript |
| `app/services/search_service.py` | Wraps `tavily-python` client, returns `[{title, url, snippet}]` |
| `app/services/url_service.py` | `httpx` + `beautifulsoup4` scrape & strip HTML to plain text (8000 char limit) |
| `app/routers/messages.py` | `POST /api/conversations/{id}/chat` — orchestrates context + search + streaming + persistence |
| `app/routers/documents.py` | `POST /api/conversations/{id}/upload` (multipart), `POST /{id}/url` |
| `app/routers/conversations.py` | CRUD: list, create, rename, delete conversations |
| `app/routers/search.py` | `POST /api/search` standalone Tavily wrapper |
| `app/routers/summaries.py` | `POST /api/conversations/{id}/summary`, `POST /{id}/summary/audio`, `GET /{id}/summary/audio/{audio_id}` |
| `app/services/summary_service.py` | Generates 2-5 min summary using Claude with document context + conversation history |
| `app/services/tts_service.py` | Converts summary text to speech using OpenAI TTS API (MP3 format) |

### Frontend Hooks

| File | Purpose |
|---|---|
| `hooks/useChat.ts` | POST chat, read SSE ReadableStream, `appendToken()` per chunk, finalize on close |
| `hooks/useUpload.ts` | FormData multipart POST for files; JSON POST for URLs |
| `hooks/useConversations.ts` | TanStack Query CRUD for conversation list |
| `hooks/useMessages.ts` | TanStack Query for message history |
| `store/chatStore.ts` | Zustand: `activeConversationId`, `messages[]`, `isStreaming`, `uploadStatus` |

---

## 3. Implementation Phases

### Phase 1 — Scaffold (Day 1)
- Monorepo root: `.gitignore`, `README.md`
- `/backend`: `pyproject.toml` (ruff + mypy config), `requirements.txt`, `requirements-dev.txt`, stub `app/main.py` returning `{"status":"ok"}`
- `/frontend`: `create-next-app@14` with TypeScript, Tailwind, ESLint, App Router; add `zustand`, `@tanstack/react-query`, `lucide-react`, `react-markdown`; add dev deps `jest`, `@testing-library/react`, `@playwright/test`
- **Git Hooks**: Install Husky + lint-staged for pre-commit linting and pre-push testing
- Verify both apps start without errors

### Phase 2 — Backend Core (Days 2–4)
1. **Database**: SQLAlchemy models (`Conversation`, `Message`, `Document`), Alembic migration `0001_initial.py`
2. **Schemas**: Pydantic v2 with `from_attributes=True`; `ChatRequest(content, use_search)`
3. **document_service**: PDF + TXT parsers, `chunk_text(512)`, `assemble_context(4000 chars)`
4. **audio_service**: save to `uploads/`, call Whisper, return transcript
5. **url_service**: `httpx.get` + BeautifulSoup, extract plain text, truncate 8000 chars
6. **claude_service**: system prompt template + `anthropic.messages.stream()` + SSE yield
7. **search_service**: Tavily client wrapper
8. **Routers**: all four routers wired into `main.py` under `/api` prefix

### Phase 3 — Frontend (Days 5–7)
1. **Layout**: Sidebar (260px fixed) + main area, dark/light theme
2. **Sidebar**: conversation list via `useConversations`, "New Chat", delete on hover
3. **ChatWindow**: history load on mount, `<MessageList>` + `<ChatInput>`
4. **MessageBubble**: user (right, blue) / assistant (left, white, markdown via `react-markdown`)
5. **SourceCard**: renders `{title, url, snippet}` below assistant bubbles
6. **ChatInput**: Enter to send, Shift+Enter newline, paperclip for file, link icon for URL, "Web Search" toggle
7. **UploadZone**: drag-over overlay, `onDrop` calls `useUpload`
8. **Hooks + Store**: full Zustand + TanStack Query wiring

### Phase 3.1 — Performance Optimization (During Frontend Development)

Apply these optimizations during Phase 3 to avoid technical debt:

#### A. Bundle Size Optimization (CRITICAL - 200-800ms improvement)

**next.config.ts configuration:**
```typescript
const config: NextConfig = {
  experimental: {
    optimizePackageImports: ['lucide-react', 'react-markdown'],
  },
}
```
**Impact**: 15-70% faster dev boot, 28% faster builds, 40% faster cold starts
**Rule**: bundle-barrel-imports

**Dynamic Imports for Heavy Components:**
```typescript
// src/components/upload/UploadZone.tsx - lazy load
const UploadZone = dynamic(() => import('@/components/upload/UploadZone'), {
  ssr: false,
  loading: () => <UploadSkeleton />
})

// Markdown renderer - defer until needed
const MarkdownRenderer = dynamic(() => import('react-markdown'), {
  ssr: false,
  loading: () => <div className="animate-pulse">Loading...</div>
})
```

#### B. Suspense Boundaries for SSE Streaming (CRITICAL)

**Pattern**: Stream UI structure immediately, lazy-load data

```typescript
// app/chat/[conversationId]/page.tsx
export default function ChatPage({ params }: { params: { conversationId: string } }) {
  return (
    <div className="flex h-screen">
      {/* Sidebar loads in parallel */}
      <Suspense fallback={<SidebarSkeleton />}>
        <ConversationSidebar />
      </Suspense>

      {/* Chat loads independently */}
      <Suspense fallback={<ChatSkeleton />}>
        <ChatWindow conversationId={params.conversationId} />
      </Suspense>
    </div>
  )
}
```

**Rule**: async-suspense-boundaries
**Impact**: Faster initial paint, improved perceived performance

#### C. Parallel Data Fetching in RSC (CRITICAL - 2-10x improvement)

```typescript
// ❌ BAD: Sequential waterfalls
async function ChatLayout() {
  const conversations = await fetchConversations()
  const currentChat = await fetchChat(conversations[0].id)
  return <Layout conversations={conversations} chat={currentChat} />
}

// ✅ GOOD: Parallel fetching
async function ChatLayout() {
  const [conversations, currentChat] = await Promise.all([
    fetchConversations(),
    fetchChat(params.id)
  ])
  return <Layout conversations={conversations} chat={currentChat} />
}
```

**Rule**: server-parallel-fetching

#### D. Re-render Optimization (MEDIUM)

**Message List Memoization:**
```typescript
// Extract expensive rendering into memo'd component
const MessageItem = memo(function MessageItem({ message }: { message: Message }) {
  const formattedContent = useMemo(() =>
    formatMarkdown(message.content),
    [message.content]
  )

  return <div>{formattedContent}</div>
})

function MessageList({ messages }: { messages: Message[] }) {
  return (
    <div>
      {messages.map(msg => (
        <MessageItem key={msg.id} message={msg} />
      ))}
    </div>
  )
}
```

**Rule**: rerender-memo

**Defer State Reads in Event Handlers:**
```typescript
// ❌ BAD: Subscribes on every progress update
function UploadButton() {
  const uploadProgress = useUploadStore(state => state.progress)

  const handleRetry = () => {
    if (uploadProgress < 100) {
      retry()
    }
  }

  return <button onClick={handleRetry}>Retry</button>
}

// ✅ GOOD: Read state only when needed
function UploadButton() {
  const handleRetry = () => {
    const progress = useUploadStore.getState().progress
    if (progress < 100) {
      retry()
    }
  }

  return <button onClick={handleRetry}>Retry</button>
}
```

**Rule**: rerender-defer-reads

#### E. TanStack Query + SSE Integration (MEDIUM-HIGH)

**Proper Cache Management with Streaming:**
```typescript
const useConversationWithSSE = (conversationId: string) => {
  const queryClient = useQueryClient()

  useEffect(() => {
    const eventSource = new EventSource(
      `/api/conversations/${conversationId}/stream`
    )

    eventSource.onmessage = (event) => {
      const newMessage = JSON.parse(event.data)

      // Update cache without refetch
      queryClient.setQueryData(
        ['conversation', conversationId],
        (old: Conversation) => ({
          ...old,
          messages: [...old.messages, newMessage]
        })
      )
    }

    return () => eventSource.close()
  }, [conversationId, queryClient])

  return useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => fetchConversation(conversationId),
    staleTime: 30 * 1000, // 30s stale time for active chat
  })
}
```

**Rule**: client-swr-dedup

#### F. Minimize RSC Serialization (HIGH)

```typescript
// ❌ BAD: Serializes entire conversation object
async function ChatPage() {
  const conversation = await fetchFullConversation(id)
  return <ChatDisplay conversation={conversation} />
}

// ✅ GOOD: Only pass needed fields
async function ChatPage() {
  const conversation = await fetchFullConversation(id)
  return (
    <ChatDisplay
      conversationId={conversation.id}
      title={conversation.title}
      messageCount={conversation.messages.length}
      // Fetch messages separately in client component with Suspense
    />
  )
}
```

**Rule**: server-serialization

### Phase 3.2 — Component Architecture Patterns

Apply composition patterns from Vercel guidelines to build maintainable, scalable components.

#### A. Compound Components Pattern (CRITICAL)

**Problem**: Boolean prop proliferation creates exponential state complexity

```typescript
// ❌ BAD: 2^6 = 64 possible component states
function ChatMessage({
  message,
  isLoading,
  isStreaming,
  isEditing,
  hasError,
  canDelete,
  canEdit
}: ChatMessageProps) {
  if (isLoading && !isStreaming) return <LoadingState />
  if (isStreaming && !hasError) return <StreamingState />
  if (hasError && canDelete) return <ErrorState />
  // Nested conditional nightmare...
}
```

**Solution**: Explicit variant components with shared context

```typescript
// ✅ GOOD: Explicit component per state, shared context
const Message = {
  Provider: MessageProvider,
  Container: MessageContainer,
  Content: MessageContent,
  Actions: MessageActions,
  LoadingIndicator: LoadingIndicator,
  ErrorIndicator: ErrorIndicator,
}

// Usage - explicit about what renders
function StreamingMessage({ message }: { message: Message }) {
  return (
    <Message.Provider state={{ message, status: 'streaming' }}>
      <Message.Container>
        <Message.Content />
        <Message.LoadingIndicator />
      </Message.Container>
    </Message.Provider>
  )
}

function EditingMessage({ message, onSave }: EditingMessageProps) {
  return (
    <Message.Provider state={{ message, status: 'editing' }}>
      <Message.Container>
        <Message.EditInput onSave={onSave} />
        <Message.Actions.Save />
        <Message.Actions.Cancel />
      </Message.Container>
    </Message.Provider>
  )
}

function ErrorMessage({ message, error }: ErrorMessageProps) {
  return (
    <Message.Provider state={{ message, status: 'error', error }}>
      <Message.Container>
        <Message.Content />
        <Message.ErrorIndicator />
        <Message.Actions.Retry />
      </Message.Container>
    </Message.Provider>
  )
}
```

**Rule**: architecture-avoid-boolean-props, architecture-compound-components
**Benefits**:
- No hidden conditionals
- Each variant is explicit
- Easier to test and maintain
- Scales naturally with new states

#### B. Chat Interface Compound Component (HIGH)

**Structure**: Build chat as a compound component system

```typescript
// src/components/chat/Chat.tsx
const Chat = {
  Provider: ChatProvider,       // State management
  Container: ChatContainer,     // Layout wrapper
  Header: ChatHeader,          // Title, info
  MessageList: MessageList,    // Scrollable messages
  Input: ChatInput,            // Message composer
  FileUpload: FileUploadZone,  // Drag & drop
  SendButton: SendButton,      // Submit action
  SearchToggle: SearchToggle,  // Web search toggle
}

// Usage in page
function ChatPage({ conversationId }: { conversationId: string }) {
  return (
    <Chat.Provider conversationId={conversationId}>
      <Chat.Container>
        <Chat.Header />
        <Chat.MessageList />
        <div className="flex gap-2">
          <Chat.Input />
          <Chat.FileUpload />
          <Chat.SearchToggle />
          <Chat.SendButton />
        </div>
      </Chat.Container>
    </Chat.Provider>
  )
}
```

**Rule**: architecture-compound-components

#### C. Decouple State from UI (MEDIUM)

**Pattern**: Provider is the only component knowing about state implementation

```typescript
// ❌ BAD: UI directly coupled to Zustand
function ChatInput() {
  const sendMessage = useChatStore(state => state.sendMessage)
  const isStreaming = useChatStore(state => state.isStreaming)
  // ...
}

// ✅ GOOD: Provider abstracts state management
function ChatProvider({ conversationId, children }: ChatProviderProps) {
  const { messages, updateMessage } = useChatStore(conversationId)
  const sendMutation = useMutation(sendMessageAPI)

  const contextValue = {
    state: {
      messages,
      isStreaming: sendMutation.isPending,
    },
    actions: {
      send: (content: string) => sendMutation.mutate({ content }),
      update: (id: string, content: string) => updateMessage(id, content),
    },
  }

  return <ChatContext.Provider value={contextValue}>{children}</ChatContext.Provider>
}

// ✅ GOOD: UI only knows context interface
function ChatInput() {
  const { state, actions } = useChat()

  return (
    <input
      disabled={state.isStreaming}
      onSubmit={(e) => actions.send(e.currentTarget.value)}
    />
  )
}
```

**Rule**: state-decouple-implementation
**Benefits**:
- Swap Zustand → useState → server state without touching UI
- Easier testing
- Clear separation of concerns

#### D. Lift State to Composition (MEDIUM)

**Pattern**: Move local state to parent when composition changes

```typescript
// ❌ BAD: State trapped in child component
function UploadModal() {
  const [files, setFiles] = useState<File[]>([])
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <button onClick={() => setIsOpen(true)}>Upload</button>
      <Modal isOpen={isOpen}>
        <FileList files={files} />
      </Modal>
    </>
  )
}

// ✅ GOOD: State lifted for composition flexibility
function UploadManager() {
  const [files, setFiles] = useState<File[]>([])

  return (
    <Upload.Provider files={files} onFilesChange={setFiles}>
      <Upload.Trigger />
      <Upload.Modal>
        <Upload.FileList />
        <Upload.ProgressBar />
      </Upload.Modal>
    </Upload.Provider>
  )
}
```

**Rule**: state-lift-state

### Phase 3.3 — Accessibility & UI/UX Guidelines

Apply Web Interface Guidelines for WCAG compliance and better UX.

#### A. Form & Input Accessibility (HIGH)

**Chat Input Requirements:**
```typescript
<textarea
  aria-label="Type your message"
  aria-describedby="char-count"
  autoComplete="off"  // Don't suggest past messages
  placeholder="Ask a question about your documents..."
  onKeyDown={handleKeyDown}  // Enter to send, Shift+Enter for newline
/>
<span id="char-count" className="sr-only">
  {charCount} characters
</span>
```

**Button States:**
```typescript
// Send button with proper loading state
<button
  type="submit"
  disabled={isStreaming || !content.trim()}
  aria-busy={isStreaming}
  aria-label={isStreaming ? "Sending message..." : "Send message"}
>
  {isStreaming ? <Spinner /> : <SendIcon />}
</button>
```

**Error Messages:**
```typescript
{error && (
  <div role="alert" className="text-red-600 mt-2">
    <AlertIcon aria-hidden="true" />
    {error.message}
  </div>
)}
```

#### B. Keyboard Navigation (HIGH)

**Conversation Sidebar:**
```typescript
<nav aria-label="Conversations">
  <ul role="list">
    {conversations.map(conv => (
      <li key={conv.id}>
        <Link
          href={`/chat/${conv.id}`}
          className="focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
          aria-current={activeId === conv.id ? 'page' : undefined}
        >
          {conv.title}
        </Link>
        <button
          aria-label={`Delete conversation: ${conv.title}`}
          className="focus-visible:ring-2"
          onClick={() => handleDelete(conv.id)}
        >
          <TrashIcon aria-hidden="true" />
        </button>
      </li>
    ))}
  </ul>
</nav>
```

**Never remove focus outlines:**
```css
/* ❌ BAD */
button:focus {
  outline: none;
}

/* ✅ GOOD */
button:focus-visible {
  outline: 2px solid theme('colors.blue.500');
  outline-offset: 2px;
}
```

#### C. Live Regions for Dynamic Content (HIGH)

**Upload Progress:**
```typescript
<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
  className="sr-only"  // Screen reader only
>
  Uploading: {progress}% complete
</div>
```

**Error Notifications:**
```typescript
<div
  role="alert"
  aria-live="assertive"  // Interrupt screen reader
  className="fixed top-4 right-4 bg-red-50 border-red-500"
>
  <AlertIcon />
  {errorMessage}
</div>
```

**New Message Announcement:**
```typescript
<div aria-live="polite" className="sr-only">
  New message from assistant
</div>
```

#### D. Motion & Animation (MEDIUM)

**Respect reduced motion preference:**
```typescript
const prefersReducedMotion = window.matchMedia(
  '(prefers-reduced-motion: reduce)'
).matches

// Conditional animation
<motion.div
  initial={prefersReducedMotion ? false : { opacity: 0, y: 10 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: prefersReducedMotion ? 0 : 0.2 }}
>
  {message.content}
</motion.div>
```

**Only animate transform and opacity:**
```css
/* ✅ GOOD - GPU accelerated */
.message-enter {
  transform: translateY(10px);
  opacity: 0;
  transition: transform 200ms, opacity 200ms;
}

/* ❌ BAD - Forces layout reflow */
.message-enter {
  height: 0;
  margin-top: 10px;
}
```

#### E. Internationalization (MEDIUM)

**Date/Time Formatting:**
```typescript
const dateFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

const timestamp = dateFormatter.format(new Date(message.created_at))
```

**File Size Formatting:**
```typescript
const sizeFormatter = new Intl.NumberFormat('en-US', {
  style: 'unit',
  unit: 'byte',
  notation: 'compact',  // "1.2 MB" instead of "1,200,000 bytes"
})

const fileSize = sizeFormatter.format(bytes)
```

**Typography:**
```typescript
// Use proper unicode characters
const ellipsis = '…'  // not '...'
const quote = '"text"'  // not "text"
const nbspBetween = 'Fig.\u00A0A'  // non-breaking space
```

#### F. Performance & Virtualization (MEDIUM)

**Message List Virtualization (>50 items):**
```typescript
import { useVirtualizer } from '@tanstack/react-virtual'

function MessageList({ messages }: { messages: Message[] }) {
  const parentRef = useRef<HTMLDivElement>(null)

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100,  // Estimated message height
    overscan: 5,
  })

  return (
    <div ref={parentRef} className="h-full overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            <MessageItem message={messages[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  )
}
```

**Image Loading (prevent layout shift):**
```typescript
<Image
  src={avatarUrl}
  alt="User avatar"
  width={40}
  height={40}
  className="rounded-full"
  loading="lazy"
/>
```

### Phase 3.4 — AI Summary + TTS Feature

**New Feature**: AI-generated summaries with text-to-speech audio playback (2-5 minute duration).

#### Backend Implementation

**New Services:**
- `app/services/summary_service.py` — Generate concise summary using Claude
- `app/services/tts_service.py` — Convert summary text to speech using OpenAI TTS

**New Router:**
- `app/routers/summaries.py` — Summary generation and TTS endpoints

**Endpoints:**
- `POST /api/conversations/{id}/summary` — Generate text summary
- `POST /api/conversations/{id}/summary/audio` — Generate TTS audio from summary
- `GET /api/conversations/{id}/summary/audio/{audio_id}` — Stream or download MP3

**Implementation:**
```python
# app/services/summary_service.py
async def generate_summary(
    conversation_id: UUID,
    documents: list[Document],
    messages: list[Message],
    max_length: int = 750  # words
) -> str:
    context = assemble_context(documents, max_chars=8000)
    history = get_recent_messages(messages, limit=20)

    system_prompt = f'''Generate a concise 2-5 minute summary of the following:

Documents: {context}
Conversation: {history}

Requirements:
- 300-750 words (2-5 minutes when read aloud)
- Key points in bullet format
- Clear, engaging language suitable for audio
- No complex jargon
'''

    response = await anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=[{"role": "user", "content": system_prompt}]
    )

    return response.content[0].text

# app/services/tts_service.py
async def generate_audio(
    text: str,
    voice: str = "alloy"  # OpenAI TTS voices: alloy, echo, fable, onyx, nova, shimmer
) -> bytes:
    response = await openai_client.audio.speech.create(
        model="tts-1",  # or "tts-1-hd" for higher quality
        voice=voice,
        input=text,
        response_format="mp3"
    )

    return response.content
```

**Database Model:**
```python
# app/models/summary.py
class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id"))
    summary_text: Mapped[str] = mapped_column(Text)
    audio_url: Mapped[str | None] = mapped_column(String, nullable=True)
    audio_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)  # seconds
    voice: Mapped[str] = mapped_column(String, default="alloy")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

#### Frontend Implementation

**New Components:**
- `components/summary/SummaryButton.tsx` — Trigger summary generation
- `components/summary/SummaryDisplay.tsx` — Display summary text + audio player
- `components/summary/AudioPlayer.tsx` — Custom audio player with controls

**Implementation:**
```typescript
// components/summary/SummaryDisplay.tsx
function SummaryDisplay({ conversationId }: { conversationId: string }) {
  const { data: summary, isLoading } = useQuery({
    queryKey: ['summary', conversationId],
    queryFn: () => fetchSummary(conversationId),
    enabled: false,  // Manual trigger only
  })

  const generateAudio = useMutation({
    mutationFn: () => generateTTS(conversationId, summary.id),
    onSuccess: () => queryClient.invalidateQueries(['summary', conversationId])
  })

  if (!summary) return null

  return (
    <div className="border rounded-lg p-4 bg-blue-50">
      <h3 className="font-semibold mb-2">Summary</h3>
      <div className="prose">
        <ReactMarkdown>{summary.text}</ReactMarkdown>
      </div>

      {summary.audio_url ? (
        <AudioPlayer
          src={summary.audio_url}
          duration={summary.audio_duration}
        />
      ) : (
        <button
          onClick={() => generateAudio.mutate()}
          disabled={generateAudio.isPending}
        >
          {generateAudio.isPending ? 'Generating audio...' : 'Generate Audio'}
        </button>
      )}
    </div>
  )
}

// components/summary/AudioPlayer.tsx
function AudioPlayer({ src, duration }: { src: string; duration: number }) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [playbackRate, setPlaybackRate] = useState(1)

  return (
    <div className="mt-4 p-3 border rounded bg-white">
      <audio
        ref={audioRef}
        src={src}
        onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
        onEnded={() => setIsPlaying(false)}
      />

      <div className="flex items-center gap-4">
        <button
          onClick={() => {
            if (isPlaying) {
              audioRef.current?.pause()
            } else {
              audioRef.current?.play()
            }
            setIsPlaying(!isPlaying)
          }}
          className="p-2 rounded-full bg-blue-500 text-white"
          aria-label={isPlaying ? "Pause" : "Play"}
        >
          {isPlaying ? <PauseIcon /> : <PlayIcon />}
        </button>

        <input
          type="range"
          min={0}
          max={duration}
          value={currentTime}
          onChange={(e) => {
            const time = Number(e.target.value)
            if (audioRef.current) {
              audioRef.current.currentTime = time
            }
            setCurrentTime(time)
          }}
          className="flex-1"
          aria-label="Seek"
        />

        <span className="text-sm text-gray-600">
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>

        <select
          value={playbackRate}
          onChange={(e) => {
            const rate = Number(e.target.value)
            if (audioRef.current) {
              audioRef.current.playbackRate = rate
            }
            setPlaybackRate(rate)
          }}
          className="text-sm"
          aria-label="Playback speed"
        >
          <option value={0.5}>0.5x</option>
          <option value={1}>1x</option>
          <option value={1.5}>1.5x</option>
          <option value={2}>2x</option>
        </select>

        <a
          href={src}
          download="summary.mp3"
          className="p-2 text-blue-600 hover:text-blue-800"
          aria-label="Download audio"
        >
          <DownloadIcon />
        </a>
      </div>
    </div>
  )
}
```

**Additional Environment Variables:**
```bash
# backend/.env (OpenAI already configured for Whisper)
TTS_MODEL=tts-1  # or tts-1-hd for higher quality
TTS_VOICE=alloy  # default voice
```

**Testing Requirements:**

Unit Tests:
- `test_summary_service.py` — Test summary generation with mocked Claude
- `test_tts_service.py` — Test TTS generation with mocked OpenAI

Integration Tests:
- `test_summaries_api.py` — Test summary endpoints
- `test_audio_generation.py` — Test TTS audio generation flow

E2E Tests:
- `summary.spec.ts` — Test summary button, text display, audio player

**Estimated Effort**: +2 days to Phase 2 and Phase 3

### Phase 4 — Integration (Day 8)
- Set env vars, verify all flows end-to-end
- Fix CORS (`http://localhost:3000` allowed)
- Handle edge cases: empty conversation, long PDF truncation, network errors

### Phase 5 — Testing (Days 9–10)
- Write all unit + integration + component + E2E tests
- Verify CI pipeline passes end-to-end

---

## 3.1 Detailed Milestone Plan

This section breaks down each phase into specific milestones with clear acceptance criteria, test requirements, and definition of done.

### Milestone 1.1 — Project Structure & Tooling Setup

**Duration:** 2-3 hours

**Goal:** Both backend and frontend servers start without errors, and git hooks enforce code quality on every commit.

**Prerequisites:** None (starting fresh)

**Implementation Steps:**
1. Create monorepo root directory structure
2. Initialize Git repository with `.gitignore`
3. Create `backend/` with Python project structure
4. Create `frontend/` with Next.js 14 App Router
5. Install and configure Husky + lint-staged
6. Configure linting tools (Ruff, ESLint, Prettier)
7. Create root `package.json` for monorepo
8. Write basic `README.md` with setup instructions

**Acceptance Criteria:**
- ✅ `cd backend && python -m app.main` returns no import errors
- ✅ `cd frontend && npm run dev` starts Next.js on `localhost:3000`
- ✅ `git commit` triggers pre-commit hook and checks staged files
- ✅ `ruff check backend/` returns 0 errors
- ✅ `eslint frontend/src` returns 0 errors
- ✅ Both apps have proper TypeScript/Python configs

**Files Created:**
```
secondbrain/
├── .gitignore
├── .husky/pre-commit
├── .husky/pre-push
├── package.json (root)
├── README.md
├── backend/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── app/
│       ├── __init__.py
│       └── main.py (stub returning {"status": "ok"})
└── frontend/
    ├── package.json
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    └── src/app/
        ├── layout.tsx
        └── page.tsx
```

**Tests Required:**
- Manual: Verify both servers start
- Manual: Verify git hooks trigger

**Definition of Done:**
- [ ] Both `backend` and `frontend` directories exist with proper structure
- [ ] `python app/main.py` runs without errors
- [ ] `npm run dev` shows Next.js welcome page
- [ ] Git hooks execute on commit/push
- [ ] All linters configured and passing
- [ ] README.md documents setup steps
- [ ] `.env.example` files present in both directories

---

### Milestone 1.2 — Database Foundation

**Duration:** 2-3 hours

**Goal:** You can create conversations, messages, and documents in SQLite and query them back using SQLAlchemy models.

**Prerequisites:** Milestone 1.1 complete

**Implementation Steps:**
1. Create SQLAlchemy models: `Conversation`, `Message`, `Document`, `Summary`
2. Create Pydantic schemas for all models
3. Set up database connection in `database.py`
4. Initialize Alembic for migrations
5. Create initial migration `0001_initial.py`
6. Write `get_db()` dependency injection function
7. Test database connection with a simple query

**Acceptance Criteria:**
- ✅ `alembic upgrade head` creates all tables without errors
- ✅ `secondbrain.db` file created in backend directory
- ✅ All four tables exist: `conversations`, `messages`, `documents`, `summaries`
- ✅ Foreign key relationships work correctly
- ✅ `get_db()` dependency provides working session

**Files Created:**
```
backend/
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 0001_initial.py
├── app/
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   ├── document.py
│   │   └── summary.py
│   └── schemas/
│       ├── __init__.py
│       ├── conversation.py
│       ├── message.py
│       ├── document.py
│       └── summary.py
```

**Tests Required:**
- `test_models.py`: Test model creation, relationships
- `test_database.py`: Test database connection, session management

**Definition of Done:**
- [ ] All SQLAlchemy models defined with proper types
- [ ] Pydantic schemas have `from_attributes=True`
- [ ] Alembic migration runs successfully
- [ ] Database file created and tables exist
- [ ] Foreign keys properly configured
- [ ] Unit tests for models pass
- [ ] `DATABASE_URL` in `.env.example`

---

### Milestone 2.1 — Document Processing Services

**Duration:** 4-5 hours

**Goal:** You can parse a PDF, transcribe an MP3, and scrape a URL to extract plain text for AI context.

**Prerequisites:** Milestone 1.2 complete

**Implementation Steps:**
1. Implement `document_service.py`:
   - PDF parsing with `pypdf`
   - TXT file reading
   - Text chunking (512 tokens per chunk)
   - Context assembly (max 4000 chars)
2. Implement `audio_service.py`:
   - Save audio file to `uploads/`
   - Call OpenAI Whisper API
   - Return transcript text
3. Implement `url_service.py`:
   - HTTP GET with `httpx`
   - BeautifulSoup HTML parsing
   - Plain text extraction (max 8000 chars)
4. Create `uploads/` directory with proper permissions

**Acceptance Criteria:**
- ✅ `parse_pdf()` extracts text from a sample PDF
- ✅ `chunk_text()` returns chunks ≤512 tokens each
- ✅ `assemble_context()` returns text ≤4000 characters
- ✅ `transcribe_audio()` calls Whisper and returns transcript
- ✅ `scrape_url()` extracts plain text from a URL
- ✅ All services handle errors gracefully (404, invalid file, etc.)

**Files Created:**
```
backend/
├── uploads/.gitkeep
└── app/
    └── services/
        ├── __init__.py
        ├── document_service.py
        ├── audio_service.py
        └── url_service.py
```

**Tests Required:**
- `test_document_service.py`:
  - `test_parse_pdf_returns_text`
  - `test_parse_txt_returns_text`
  - `test_chunk_text_respects_size`
  - `test_assemble_context_respects_max_chars`
- `test_audio_service.py`:
  - `test_transcribe_returns_string` (mock Whisper)
  - `test_transcribe_saves_file_to_uploads`
- `test_url_service.py`:
  - `test_scrape_url_returns_text` (mock httpx)
  - `test_scrape_handles_404`

**Definition of Done:**
- [ ] All three services implemented
- [ ] PDF parsing works with test PDF
- [ ] Audio transcription mocked and tested
- [ ] URL scraping handles errors
- [ ] Text chunking respects token limits
- [ ] Context assembly truncates properly
- [ ] All unit tests pass (≥80% coverage)
- [ ] `OPENAI_API_KEY` in `.env.example`

---

### Milestone 2.2 — Claude Integration & Streaming

**Duration:** 3-4 hours

**Goal:** You can send a message to Claude with document context and get a streaming response back token-by-token.

**Prerequisites:** Milestone 2.1 complete

**Implementation Steps:**
1. Implement `claude_service.py`:
   - Build system prompt with document context
   - Include conversation history (last 20 messages)
   - Call `anthropic.messages.stream()`
   - Yield SSE chunks as they arrive
2. Implement `search_service.py`:
   - Wrap Tavily Python client
   - Return `[{title, url, snippet}]` format
3. Integrate search results into Claude context

**Acceptance Criteria:**
- ✅ `stream_response()` yields text chunks via async generator
- ✅ System prompt includes document context
- ✅ Last 20 messages included in request
- ✅ Search results integrated into context when `use_search=True`
- ✅ Streaming continues until complete or error

**Files Created:**
```
backend/app/services/
├── claude_service.py
└── search_service.py
```

**Tests Required:**
- `test_claude_service.py`:
  - `test_stream_yields_text_chunks` (mock Anthropic)
  - `test_system_prompt_includes_context`
  - `test_history_included_in_request`
  - `test_search_results_in_prompt`
- `test_search_service.py`:
  - `test_search_returns_list` (mock Tavily)
  - `test_search_handles_empty_results`

**Definition of Done:**
- [ ] Claude service streams responses
- [ ] System prompt includes document context
- [ ] Conversation history properly formatted
- [ ] Search integration works
- [ ] All unit tests pass with mocked APIs
- [ ] `ANTHROPIC_API_KEY` and `TAVILY_API_KEY` in `.env.example`

---

### Milestone 2.3 — API Routes & Routers

**Duration:** 4-5 hours

**Goal:** You can test all API endpoints with Postman/curl (create conversations, upload files, send chat messages, get streaming responses).

**Prerequisites:** Milestone 2.2 complete

**Implementation Steps:**
1. Implement `routers/conversations.py`:
   - `GET /api/conversations` - List all
   - `POST /api/conversations` - Create new
   - `PATCH /api/conversations/{id}` - Rename
   - `DELETE /api/conversations/{id}` - Delete
2. Implement `routers/messages.py`:
   - `GET /api/conversations/{id}/messages` - Get history
   - `POST /api/conversations/{id}/chat` - Send message (SSE)
3. Implement `routers/documents.py`:
   - `POST /api/conversations/{id}/upload` - File upload
   - `POST /api/conversations/{id}/url` - URL ingest
4. Implement `routers/search.py`:
   - `POST /api/search` - Standalone search
5. Implement `routers/summaries.py`:
   - `POST /api/conversations/{id}/summary` - Generate summary
   - `POST /api/conversations/{id}/summary/audio` - Generate TTS
   - `GET /api/conversations/{id}/summary/audio/{audio_id}` - Download MP3
6. Wire all routers into `main.py`
7. Configure CORS middleware

**Acceptance Criteria:**
- ✅ All endpoints return proper status codes (200, 201, 404, 422)
- ✅ POST /chat streams SSE with `text/event-stream` content-type
- ✅ File upload accepts multipart/form-data
- ✅ CORS allows `http://localhost:3000`
- ✅ All endpoints validate request bodies with Pydantic
- ✅ Foreign key constraints enforced (deleting conversation deletes messages)

**Files Created:**
```
backend/app/
├── main.py (updated with routers)
├── config.py (Pydantic Settings)
└── routers/
    ├── __init__.py
    ├── conversations.py
    ├── messages.py
    ├── documents.py
    ├── search.py
    └── summaries.py
```

**Tests Required:**
- `test_conversations_api.py`:
  - `test_create_conversation` (201 with id/title)
  - `test_list_conversations`
  - `test_delete_conversation` (204, then 404)
  - `test_rename_conversation`
- `test_messages_api.py`:
  - `test_get_empty_history`
  - `test_chat_streams_response` (SSE content-type)
  - `test_chat_persists_messages`
  - `test_chat_with_search_calls_tavily`
- `test_documents_api.py`:
  - `test_upload_pdf` (201)
  - `test_upload_unsupported_type` (422)
  - `test_upload_url` (mock httpx)
- `test_summaries_api.py`:
  - `test_generate_summary`
  - `test_generate_audio`
  - `test_download_audio`

**Definition of Done:**
- [ ] All routers registered in `main.py`
- [ ] CORS middleware configured
- [ ] All integration tests pass
- [ ] TestClient can hit all endpoints
- [ ] SSE streaming works in tests
- [ ] File upload flow tested
- [ ] Error responses have proper format
- [ ] OpenAPI docs available at `/docs`

---

### Milestone 3.1 — Layout & Sidebar

**Duration:** 3-4 hours

**Goal:** You can create, rename, delete, and navigate between conversations in the browser sidebar.

**Prerequisites:** Milestone 1.1 complete (frontend scaffold)

**Implementation Steps:**
1. Create root layout with sidebar + main area
2. Implement `Sidebar.tsx`:
   - Conversation list
   - "New Chat" button
   - Delete button on hover
3. Implement `useConversations.ts` hook with TanStack Query:
   - Fetch conversations
   - Create conversation mutation
   - Delete conversation mutation
   - Rename conversation mutation
4. Set up Zustand store for global state
5. Add Tailwind styling

**Acceptance Criteria:**
- ✅ Sidebar visible on all `/chat/*` routes
- ✅ "New Chat" creates conversation and navigates to `/chat/{id}`
- ✅ Clicking conversation navigates to `/chat/{id}`
- ✅ Delete button removes conversation from list
- ✅ Active conversation highlighted in sidebar
- ✅ Layout responsive (sidebar 260px fixed width)

**Files Created:**
```
frontend/src/
├── app/
│   ├── layout.tsx (updated with sidebar)
│   ├── chat/
│   │   ├── page.tsx
│   │   └── [conversationId]/
│   │       └── page.tsx
├── components/
│   └── layout/
│       ├── Sidebar.tsx
│       ├── SidebarItem.tsx
│       └── Header.tsx
├── hooks/
│   └── useConversations.ts
├── store/
│   └── chatStore.ts
└── lib/
    └── api.ts
```

**Tests Required:**
- `Sidebar.test.tsx`:
  - Renders conversation list from mocked API
  - "New Chat" fires POST /api/conversations
  - Clicking item navigates to /chat/{id}
  - Delete fires DELETE and removes from list
- `useConversations.test.ts`:
  - Mock TanStack Query responses
  - Test mutation success/error states

**Definition of Done:**
- [ ] Sidebar renders with conversation list
- [ ] Create, delete, rename operations work
- [ ] Navigation between conversations works
- [ ] TanStack Query cache invalidation works
- [ ] Component tests pass
- [ ] Styling matches design (fixed width sidebar)
- [ ] Active conversation highlighted

---

### Milestone 3.2 — Chat Interface & Streaming

**Duration:** 5-6 hours

**Goal:** You can type a message in the browser and see Claude's response stream in real-time, with markdown rendering and source cards.

**Prerequisites:** Milestone 3.1 complete, Milestone 2.3 complete (backend API)

**Implementation Steps:**
1. Implement `ChatWindow.tsx` container
2. Implement `MessageList.tsx` with auto-scroll
3. Implement `MessageBubble.tsx`:
   - User messages (right, blue)
   - Assistant messages (left, white, markdown)
   - Source cards for search results
4. Implement `ChatInput.tsx`:
   - Textarea with Enter/Shift+Enter
   - Web search toggle
   - File upload button
   - Send button
5. Implement `useChat.ts` hook:
   - POST /chat with SSE streaming
   - ReadableStream parsing
   - Token-by-token append to Zustand
   - Optimistic user message
6. Integrate `react-markdown` for assistant responses
7. Add typing indicator during streaming

**Acceptance Criteria:**
- ✅ User message appears immediately (optimistic UI)
- ✅ Assistant response streams token-by-token
- ✅ Markdown renders correctly (bold, code, lists)
- ✅ Source cards display when web search enabled
- ✅ Message list auto-scrolls to bottom
- ✅ Enter sends, Shift+Enter adds newline
- ✅ History loads when navigating to existing conversation

**Files Created:**
```
frontend/src/
├── components/
│   └── chat/
│       ├── ChatWindow.tsx
│       ├── MessageList.tsx
│       ├── MessageBubble.tsx
│       ├── ChatInput.tsx
│       ├── SourceCard.tsx
│       └── TypingIndicator.tsx
├── hooks/
│   ├── useChat.ts
│   └── useMessages.ts
└── lib/
    └── stream.ts
```

**Tests Required:**
- `MessageBubble.test.tsx`:
  - User message has correct styling
  - Assistant message renders markdown
  - Message with sources renders SourceCard
- `ChatInput.test.tsx`:
  - Enter calls onSend
  - Shift+Enter inserts newline
  - Web Search toggle changes state
- `useChat.test.ts`:
  - Mock fetch with SSE ReadableStream
  - appendToken called per chunk
  - isStreaming transitions true → false

**Definition of Done:**
- [ ] Chat interface fully functional
- [ ] SSE streaming works end-to-end
- [ ] Markdown rendering works
- [ ] Source cards display search results
- [ ] Optimistic UI for user messages
- [ ] Auto-scroll to latest message
- [ ] Component tests pass
- [ ] Web search toggle works

---

### Milestone 3.3 — File Upload & Document Management

**Duration:** 3-4 hours

**Goal:** You can drag & drop a PDF or paste a URL, watch it upload/process, then ask questions about it in chat.

**Prerequisites:** Milestone 3.2 complete

**Implementation Steps:**
1. Implement `UploadZone.tsx`:
   - Drag & drop overlay
   - File input button
   - Progress indicator
2. Implement `UrlInput.tsx`:
   - URL input field
   - Validation
   - Submit button
3. Implement `useUpload.ts` hook:
   - FormData multipart POST for files
   - JSON POST for URLs
   - Progress tracking
   - Error handling
4. Add upload UI to ChatWindow
5. Display uploaded documents in sidebar or header

**Acceptance Criteria:**
- ✅ Drag & drop shows overlay
- ✅ File upload shows progress indicator
- ✅ PDF uploads and processes successfully
- ✅ Audio files upload and transcribe
- ✅ URL paste extracts text
- ✅ Unsupported file types show error
- ✅ Files >50MB rejected

**Files Created:**
```
frontend/src/
├── components/
│   └── upload/
│       ├── UploadZone.tsx
│       ├── UrlInput.tsx
│       └── UploadProgress.tsx
└── hooks/
    └── useUpload.ts
```

**Tests Required:**
- `UploadZone.test.tsx`:
  - Drag-over shows overlay
  - Drop calls onDrop with file
- `useUpload.test.ts`:
  - Mock FormData POST
  - Progress updates tracked
  - Error states handled

**Definition of Done:**
- [ ] File upload fully functional
- [ ] URL input works
- [ ] Progress indicators display
- [ ] Error messages clear
- [ ] All file types handled (PDF, TXT, audio)
- [ ] Component tests pass
- [ ] Upload integrated into chat flow

---

### Milestone 3.4 — Twitter Bookmarks Import (Knowledge Base)

**Duration:** 3-4 hours

**Goal:** You can import your 100 saved Twitter bookmarks, search them with AI, and add personal learning notes — solving the "I saved it but can't find it" problem.

**Prerequisites:** Milestone 3.3 complete

**Implementation Steps:**
1. Implement `twitter_service.py` in backend:
   - Parse Twitter `bookmarks.json` export file
   - Extract tweet text, author, URL, date
   - Fetch full thread context for bookmarked tweets
   - Handle Twitter data export format
2. Add Twitter import endpoint in `routers/documents.py`:
   - `POST /api/conversations/{id}/twitter`
   - Accept `bookmarks.json` file upload
   - Create documents for each tweet/thread
3. Implement `TwitterImportButton.tsx` in frontend:
   - File upload specific to Twitter bookmarks
   - Show import progress (parsing 100 tweets)
   - Display success message with count
4. Add monthly reminder system:
   - Dashboard shows "🔔 Update Twitter bookmarks?"
   - Links to Twitter settings page
   - Tracks last import date
5. Implement merge logic:
   - Compare tweet IDs to detect duplicates
   - Keep existing bookmarks, add only new ones
   - Update conversation title with import date

**Acceptance Criteria:**
- ✅ User can upload `bookmarks.json` from Twitter data export
- ✅ Parser extracts ~100 bookmarks successfully
- ✅ Full thread context included for multi-tweet threads
- ✅ Creates "Twitter Bookmarks (YYYY-MM-DD)" conversation
- ✅ User can ask: "What have I saved about React?"
- ✅ AI finds relevant tweets and summarizes them
- ✅ User can add notes: "📝 Learned: ..."
- ✅ Re-importing merges new bookmarks (no duplicates)
- ✅ Monthly reminder shown in dashboard

**Files Created:**
```
Backend:
backend/app/services/
└── twitter_service.py

Frontend:
frontend/src/components/twitter/
├── TwitterImportButton.tsx
├── TwitterImportModal.tsx
└── MonthlyReminderBanner.tsx
```

**Twitter `bookmarks.json` Format:**
```json
[
  {
    "tweet": {
      "id_str": "1234567890",
      "full_text": "This is the tweet content...",
      "created_at": "Wed Mar 29 12:00:00 +0000 2024",
      "user": {
        "screen_name": "username",
        "name": "Display Name"
      },
      "entities": {
        "urls": [...],
        "hashtags": [...]
      }
    }
  }
]
```

**Implementation Example:**
```python
# services/twitter_service.py
def parse_twitter_bookmarks(file_path: str) -> list[Document]:
    """
    Parse Twitter bookmark export and extract threads.

    Returns:
        List of Document objects, one per tweet/thread
    """
    with open(file_path) as f:
        data = json.load(f)

    documents = []
    for bookmark in data:
        tweet = bookmark['tweet']

        # Check if part of thread
        if 'in_reply_to_status_id_str' in tweet:
            # Fetch full thread context (recursive)
            thread_tweets = fetch_thread(tweet)
            text = format_thread(thread_tweets)
        else:
            text = format_single_tweet(tweet)

        doc = Document(
            conversation_id=conversation_id,
            filename=f"tweet_{tweet['id_str']}",
            file_type="twitter",
            extracted_text=text
        )
        documents.append(doc)

    return documents

def format_single_tweet(tweet: dict) -> str:
    """Format single tweet as readable text."""
    return f"""
Tweet by @{tweet['user']['screen_name']} ({tweet['user']['name']})
Posted: {tweet['created_at']}

{tweet['full_text']}

Link: https://twitter.com/{tweet['user']['screen_name']}/status/{tweet['id_str']}
Likes: {tweet.get('favorite_count', 0)} | Retweets: {tweet.get('retweet_count', 0)}
""".strip()

def fetch_thread(tweet: dict) -> list[dict]:
    """Recursively fetch all tweets in a thread."""
    # Note: For MVP, this extracts from export data only
    # Future: Could fetch missing tweets via API
    thread = [tweet]

    # Walk up the thread (replies)
    parent_id = tweet.get('in_reply_to_status_id_str')
    if parent_id:
        # Find parent in export data
        parent = find_tweet_by_id(parent_id)
        if parent:
            thread = fetch_thread(parent) + thread

    return thread
```

**Tests Required:**
- `test_twitter_service.py`:
  - `test_parse_single_tweet`
  - `test_parse_thread` (multi-tweet thread)
  - `test_handle_missing_fields` (incomplete data)
  - `test_detect_duplicates` (merge logic)
  - `test_format_tweet_text`
- `TwitterImportButton.test.tsx`:
  - Upload bookmarks.json triggers import
  - Progress indicator shows during parse
  - Success message displays count
- Integration test:
  - Upload bookmarks.json → creates conversation
  - Ask "What have I saved about X?" → finds tweets
  - Add note → saves in conversation

**Definition of Done:**
- [ ] Twitter bookmark parser handles full export format
- [ ] Thread context extraction works
- [ ] Import creates searchable conversation
- [ ] User can ask questions about saved tweets
- [ ] User can add learning notes as chat messages
- [ ] Monthly reminder system implemented
- [ ] Re-import merges (no duplicate tweets)
- [ ] All tests pass (≥80% coverage)
- [ ] Tested with real Twitter export file (100+ bookmarks)

**User Flow:**
```
1. User: Visit twitter.com/settings → "Download your data"
2. Wait: 24 hours for Twitter to prepare export
3. User: Download bookmarks.json from email
4. SecondBrain: Dashboard shows "🔔 Time to update Twitter bookmarks"
5. User: Click "Import Twitter Bookmarks"
6. User: Drag & drop bookmarks.json
7. SecondBrain: Parses 100 bookmarks, extracts threads
8. SecondBrain: Creates "Twitter Bookmarks (2024-03-29)" conversation
9. User: Ask "What have I saved about Next.js?"
10. AI: "You've saved 5 tweets about Next.js. Key themes: App Router..."
11. User: Add note: "📝 Learned: Server components reduce JS bundle"
12. Next month: Repeat steps 1-7 (merge new bookmarks)
```

---

### Milestone 3.5 — AI Summary + TTS Feature

**Duration:** 4-5 hours

**Goal:** You can click "Generate Summary" to get a 2-5 minute AI summary, then click "Generate Audio" to hear it spoken aloud with playback controls.

**Prerequisites:** Milestone 3.2 complete, Milestone 2.3 complete

**Implementation Steps:**
1. Implement `summary_service.py` in backend
2. Implement `tts_service.py` with OpenAI TTS
3. Create summary endpoints in `routers/summaries.py`
4. Implement `SummaryButton.tsx` in frontend
5. Implement `SummaryDisplay.tsx` with markdown rendering
6. Implement `AudioPlayer.tsx`:
   - Play/pause controls
   - Seek bar
   - Playback speed (0.5x, 1x, 1.5x, 2x)
   - Download button
7. Integrate summary feature into ChatWindow

**Acceptance Criteria:**
- ✅ "Generate Summary" button triggers summary generation
- ✅ Summary displays as formatted text (2-5 min read)
- ✅ "Generate Audio" creates TTS MP3
- ✅ Audio player has play/pause, seek, speed controls
- ✅ Audio downloads as MP3 file
- ✅ Summary based on documents + conversation history

**Files Created:**
```
Backend:
backend/app/services/
├── summary_service.py
└── tts_service.py

Frontend:
frontend/src/components/summary/
├── SummaryButton.tsx
├── SummaryDisplay.tsx
└── AudioPlayer.tsx
```

**Tests Required:**
- `test_summary_service.py`:
  - `test_generate_summary` (mock Claude)
  - `test_summary_length_within_range`
- `test_tts_service.py`:
  - `test_generate_audio` (mock OpenAI TTS)
  - `test_audio_format_is_mp3`
- `summary.spec.ts` (E2E):
  - Click "Generate Summary" → summary appears
  - Click "Generate Audio" → audio player appears
  - Play audio → audio plays

**Definition of Done:**
- [ ] Summary service generates 2-5 min summaries
- [ ] TTS service creates MP3 audio
- [ ] Audio player fully functional
- [ ] Download button works
- [ ] Summary integrated into UI
- [ ] All tests pass
- [ ] TTS_MODEL and TTS_VOICE in .env.example

---

### Milestone 4.1 — End-to-End Integration & Bug Fixes

**Duration:** 1 day

**Goal:** The complete user journey works flawlessly: upload PDF → chat about it → enable web search → generate summary → play audio.

**Prerequisites:** All Phase 3 milestones complete

**Implementation Steps:**
1. Test complete user flows manually:
   - Create conversation → upload PDF → ask question → get response
   - Upload audio → transcribe → chat about audio
   - Paste URL → extract text → chat
   - Enable web search → get sources
   - Generate summary → generate audio → play
2. Fix CORS issues
3. Handle edge cases:
   - Empty conversation
   - Long PDF (>4000 chars truncation)
   - Network errors (retry logic)
   - File upload failures
4. Optimize performance bottlenecks
5. Verify all environment variables work

**Acceptance Criteria:**
- ✅ PDF upload → chat → response works end-to-end
- ✅ Audio transcription → chat works
- ✅ URL paste → chat works
- ✅ Web search displays sources
- ✅ Summary + TTS works
- ✅ No CORS errors
- ✅ Error states display user-friendly messages
- ✅ Page refresh preserves state

**Tests Required:**
- Manual testing of all flows
- Error scenario testing:
  - Network timeout
  - Invalid file type
  - Malformed URL
  - API key missing

**Definition of Done:**
- [ ] All core user flows work without errors
- [ ] CORS properly configured
- [ ] Error handling comprehensive
- [ ] Edge cases handled gracefully
- [ ] Performance acceptable (<2s first token)
- [ ] No console errors in browser
- [ ] Backend logs errors properly

---

### Milestone 5.1 — Complete Test Suite

**Duration:** 1.5 days

**Goal:** All unit tests, integration tests, and E2E tests pass with ≥80% code coverage on both frontend and backend.

**Prerequisites:** Milestone 4.1 complete

**Implementation Steps:**
1. Write all missing unit tests (backend)
2. Write all missing integration tests (backend)
3. Write all missing component tests (frontend)
4. Write Playwright E2E tests:
   - `sidebar.spec.ts`
   - `file-upload.spec.ts`
   - `chat.spec.ts`
   - `summary.spec.ts`
5. Achieve ≥80% code coverage on both frontend and backend
6. Fix any failing tests

**Acceptance Criteria:**
- ✅ Backend test coverage ≥80%
- ✅ Frontend test coverage ≥80%
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ All E2E tests pass
- ✅ No skipped or pending tests

**Tests Required:**
All tests from previous milestones plus:
- `sidebar.spec.ts`:
  - New conversation created
  - Conversation title updates after first message
  - Delete removes and redirects
- `file-upload.spec.ts`:
  - Upload PDF via button
  - Progress indicator appears/disappears
  - Question about PDF returns response
- `chat.spec.ts`:
  - User bubble appears immediately
  - Typing indicator during stream
  - Assistant message streams
  - Refresh restores history
  - Web search shows source cards
- `summary.spec.ts`:
  - Generate summary button works
  - Summary text displays
  - Generate audio button works
  - Audio player controls work

**Definition of Done:**
- [ ] All test files created
- [ ] Backend coverage ≥80%
- [ ] Frontend coverage ≥80%
- [ ] All tests passing
- [ ] E2E tests cover critical flows
- [ ] Test reports generated
- [ ] Coverage reports generated

---

### Milestone 5.2 — CI/CD Pipeline

**Duration:** 0.5 days

**Goal:** Every pull request automatically runs linting, tests, and type checking; merging is blocked if any check fails.

**Prerequisites:** Milestone 5.1 complete

**Implementation Steps:**
1. Create `.github/workflows/ci.yml`
2. Configure six parallel jobs:
   - `backend-lint`
   - `backend-unit-tests`
   - `backend-integration-tests`
   - `frontend-lint`
   - `frontend-unit-tests`
   - `frontend-e2e`
3. Add aggregate job `all-checks-pass`
4. Configure branch protection on `main` branch
5. Test CI pipeline with a PR
6. Fix any CI-specific issues (paths, caching, etc.)

**Acceptance Criteria:**
- ✅ All six jobs run in parallel
- ✅ Jobs complete in <10 minutes total
- ✅ `all-checks-pass` job succeeds only if all checks pass
- ✅ PR blocked if CI fails
- ✅ Coverage reports uploaded
- ✅ Branch protection enforced

**Files Created:**
```
.github/workflows/
└── ci.yml
```

**CI Jobs Configuration:**
```yaml
jobs:
  backend-lint:
    - ruff check
    - ruff format --check
    - mypy

  backend-unit-tests:
    - pytest tests/unit/ --cov
    - coverage ≥80%

  backend-integration-tests:
    - pytest tests/integration/

  frontend-lint:
    - eslint
    - prettier --check
    - tsc --noEmit

  frontend-unit-tests:
    - jest --coverage
    - coverage ≥80%

  frontend-e2e:
    - Start backend server
    - Start frontend server
    - playwright test
    - Upload test artifacts

  all-checks-pass:
    - needs: [all 6 jobs above]
```

**Tests Required:**
- Create test PR and verify CI runs
- Test failure scenarios (lint error, test failure)

**Definition of Done:**
- [ ] CI pipeline configured
- [ ] All jobs run successfully
- [ ] Branch protection enabled
- [ ] PR checks required before merge
- [ ] Coverage reports visible
- [ ] CI documented in README.md
- [ ] CI badge added to README.md

---

## 3.2 Milestone Dependencies Graph

```
Milestone 1.1 (Project Structure)
    ↓
Milestone 1.2 (Database)
    ↓
Milestone 2.1 (Document Services)
    ↓
Milestone 2.2 (Claude + Streaming)
    ↓
Milestone 2.3 (API Routes)
    ↓
    ├─→ Milestone 3.1 (Layout + Sidebar)
    │       ↓
    │   Milestone 3.2 (Chat Interface)
    │       ↓
    │   Milestone 3.3 (File Upload)
    │       ↓
    │   Milestone 3.4 (AI Summary + TTS)
    │       ↓
    └───────┴─→ Milestone 4.1 (Integration)
                    ↓
                Milestone 5.1 (Test Suite)
                    ↓
                Milestone 5.2 (CI/CD)
```

---

## 3.3 Quick Reference: Definition of Done Checklist

Use this checklist to verify each milestone is truly complete before moving to the next:

**Every Milestone Must Have:**
- [ ] All acceptance criteria met
- [ ] All required tests written and passing
- [ ] Code reviewed (self-review or peer)
- [ ] No linting errors
- [ ] No console errors/warnings
- [ ] Documentation updated (if applicable)
- [ ] Environment variables documented in `.env.example`

**Backend-Specific:**
- [ ] Type hints on all functions
- [ ] Docstrings on all public functions
- [ ] Error handling implemented
- [ ] Pydantic schemas validated

**Frontend-Specific:**
- [ ] TypeScript types defined (no `any`)
- [ ] Components have proper props interface
- [ ] Accessibility attributes present
- [ ] Responsive design verified

**Integration Milestones:**
- [ ] End-to-end flow tested manually
- [ ] Error scenarios tested
- [ ] Performance within acceptable limits

---

## 4. Environment Variables

### `backend/.env`
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
DATABASE_URL=sqlite:///./secondbrain.db
UPLOAD_DIR=./uploads
CORS_ORIGINS=http://localhost:3000
MAX_FILE_SIZE_MB=50
```

### `frontend/.env.local`
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 5. Data Flows

### File Upload
```
User drops file → UploadZone → useUpload.uploadFile()
  → POST /api/conversations/{id}/upload
  → detect MIME → document_service / audio_service / url_service
  → INSERT documents(conversation_id, extracted_text)
  → 201 response → TanStack Query invalidation
```

### Chat Message (with streaming)
```
User sends message → useChat.sendMessage()
  → optimistic append to store
  → POST /api/conversations/{id}/chat {content, use_search}
  → assemble document context (document_service)
  → if use_search: search_service.search(content) → results
  → fetch last 20 messages (history)
  → claude_service.stream_response(system_prompt, history, msg, search_results)
  → anthropic.messages.stream() → SSE text/event-stream
  → frontend ReadableStream loop: appendToken() per chunk
  → stream ends: isStreaming=false
  → INSERT messages(user + assistant rows)
```

---

## 6. PR Test Checklist (must all pass before merge)

### Backend

**Unit tests** (all external APIs mocked):

`test_document_service.py`
- `test_parse_pdf_returns_text`
- `test_parse_txt_returns_text`
- `test_chunk_text_respects_size` — no chunk > 512 tokens
- `test_assemble_context_respects_max_chars` — output ≤ 4000 chars

`test_audio_service.py`
- `test_transcribe_returns_string` — mock Whisper returns `MagicMock(text="hello")`
- `test_transcribe_saves_file_to_uploads`

`test_search_service.py`
- `test_search_returns_list` — mock Tavily, assert `[{title, url, snippet}]`
- `test_search_handles_empty_results` — returns `[]` without raising

`test_claude_service.py`
- `test_stream_yields_text_chunks` — mock `anthropic.messages.stream()` async ctx manager
- `test_system_prompt_includes_context` — assert document context in prompt string

**Integration tests** (TestClient + in-memory SQLite):

`test_conversations_api.py`
- `test_create_conversation` — 201 with id/title
- `test_list_conversations` — create 3, GET returns list of 3
- `test_delete_conversation` — 204; subsequent GET returns 404
- `test_rename_conversation` — PATCH updates title

`test_documents_api.py`
- `test_upload_pdf` — 201, `extracted_text` non-empty
- `test_upload_txt`
- `test_upload_url` — mock `httpx.get`, assert text stored
- `test_upload_unsupported_type` — `.exe` → 422
- `test_upload_exceeds_size_limit` — oversized → 413

`test_messages_api.py`
- `test_get_empty_history` — new conversation returns `[]`
- `test_chat_streams_response` — SSE content-type, chunked body
- `test_chat_persists_messages` — GET /messages returns user + assistant after stream
- `test_chat_with_search_calls_tavily` — `use_search=True` triggers mock search

`test_search_api.py`
- `test_search_endpoint_returns_results`

### Frontend

**Jest + React Testing Library:**

`Sidebar.test.tsx`
- renders conversation list from mocked API
- "New Chat" fires `POST /api/conversations`
- clicking item navigates to `/chat/{id}`
- delete fires `DELETE` and removes from list

`MessageBubble.test.tsx`
- user message has correct styling class
- assistant message renders markdown (bold, code block)
- message with sources renders `<SourceCard>`

`ChatInput.test.tsx`
- Enter calls `onSend`
- Shift+Enter inserts newline
- file input `onChange` calls `onFileSelect`
- "Web Search" toggle changes active state

`UploadZone.test.tsx`
- drag-over shows overlay
- drop calls `onDrop` with file

`useChat.test.ts`
- mock `fetch` with SSE ReadableStream chunks
- `appendToken` called per chunk
- `isStreaming` transitions `true → false`

**Playwright E2E (Chromium):**

`sidebar.spec.ts`
- new conversation created and appears in sidebar
- conversation title updates after first message
- delete removes and redirects to `/chat`

`file-upload.spec.ts`
- upload PDF via paperclip button
- progress indicator appears/disappears
- question about PDF returns non-empty response

`chat.spec.ts`
- user bubble appears immediately (optimistic)
- typing indicator appears during stream
- assistant message streams token by token
- refresh at `/chat/{id}` restores history
- "Web Search" enabled → source cards appear

### Linting & Type Checking

| Check | Command | Threshold | Hook |
|---|---|---|---|
| Python lint | `ruff check backend/` | 0 errors | pre-commit |
| Python format | `ruff format --check backend/` | 0 diffs | pre-commit |
| Python types | `mypy backend/app --ignore-missing-imports` | 0 errors | CI only |
| JS lint | `eslint frontend/src --ext .ts,.tsx` | 0 errors | pre-commit |
| JS format | `prettier --check "frontend/src/**/*.{ts,tsx,css}"` | 0 diffs | pre-commit |
| TS types | `tsc --noEmit -p frontend/tsconfig.json` | 0 errors | CI only |

**Note**: Pre-commit hook catches linting/formatting issues locally (instant feedback). CI runs full suite including type checking.

---

## 7. GitHub Actions CI (`/.github/workflows/ci.yml`)

Six parallel jobs, all must pass before PR merges:

| Job | What it runs |
|---|---|
| `backend-lint` | ruff check, ruff format, mypy |
| `backend-unit-tests` | pytest tests/unit/, coverage ≥ 80% |
| `backend-integration-tests` | pytest tests/integration/ |
| `frontend-lint` | ESLint, Prettier, tsc --noEmit |
| `frontend-unit-tests` | Jest + RTL, coverage ≥ 80% |
| `frontend-e2e` | Playwright (Chromium), starts both backend + frontend servers |
| `all-checks-pass` | Aggregate gate job — required status check for branch protection |

Branch protection on `main`: `all-checks-pass` must be green before any PR merge.

---

## 7.1 Git Hooks with Husky (Local Development)

Git hooks enforce code quality **locally** before code even reaches CI. This catches issues faster and reduces failed CI runs.

### Setup

**Install Husky + lint-staged:**
```bash
# In frontend directory
npm install --save-dev husky lint-staged
npx husky install
npm pkg set scripts.prepare="husky install"
```

**Create hooks:**
```bash
# Pre-commit: lint and format staged files only
npx husky add .husky/pre-commit "cd frontend && npx lint-staged"

# Pre-push: run tests before pushing
npx husky add .husky/pre-push "cd frontend && npm run test:unit && cd ../backend && pytest tests/unit/"
```

### Configuration Files

**`frontend/package.json`** - Add lint-staged config:
```json
{
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{css,md,json}": [
      "prettier --write"
    ]
  },
  "scripts": {
    "prepare": "husky install",
    "lint": "eslint src --ext .ts,.tsx",
    "format": "prettier --write \"src/**/*.{ts,tsx,css}\"",
    "test:unit": "jest --passWithNoTests"
  }
}
```

**`.husky/pre-commit`** - Lint staged files:
```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

echo "🔍 Running pre-commit checks..."

# Frontend linting
cd frontend
npx lint-staged

# Backend linting (only if Python files changed)
cd ../backend
if git diff --cached --name-only | grep -q "\.py$"; then
  echo "🐍 Linting Python files..."
  git diff --cached --name-only --diff-filter=ACM | grep "\.py$" | xargs ruff check
  git diff --cached --name-only --diff-filter=ACM | grep "\.py$" | xargs ruff format --check
fi

echo "✅ Pre-commit checks passed!"
```

**`.husky/pre-push`** - Run tests:
```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

echo "🧪 Running pre-push tests..."

# Frontend unit tests
cd frontend
npm run test:unit

# Backend unit tests
cd ../backend
pytest tests/unit/ --maxfail=1

echo "✅ All tests passed!"
```

### What Gets Checked

| Hook | Frontend | Backend | When |
|---|---|---|---|
| `pre-commit` | ESLint, Prettier, TypeScript (staged files only) | Ruff lint, Ruff format (staged files only) | Before every commit |
| `pre-push` | Jest unit tests (full suite) | Pytest unit tests (full suite) | Before every push |

### Benefits

- **Fast feedback**: Catch issues in seconds, not minutes (CI takes longer)
- **Fail fast**: Bad code never leaves your machine
- **Auto-fix**: ESLint/Prettier/Ruff auto-fix issues when possible
- **Selective**: `lint-staged` only checks changed files (pre-commit is instant)
- **Team consistency**: Everyone has the same checks automatically

### Bypassing Hooks (Emergency Only)

```bash
# Skip pre-commit (not recommended)
git commit --no-verify -m "emergency fix"

# Skip pre-push (not recommended)
git push --no-verify
```

**Important**: CI will still catch these issues, but you'll waste time waiting for CI to fail.

---

## 8. Architectural Decisions

- **SQLite over Postgres**: zero-dependency local dev; Alembic migrations allow upgrading later.
- **No vector DB (MVP)**: naive full-text truncation to 4000 chars. `assemble_context()` can be swapped for ChromaDB + embeddings later without touching routers.
- **SSE over WebSockets**: unidirectional stream matches chat response pattern; works through HTTP proxies; consumable with native browser `fetch`.
- **TanStack Query for server state**: auto cache invalidation keeps sidebar list fresh without manual refetching.
- **Optimistic UI**: user message appended to store before server responds, eliminating perceived latency.

---

## 9. Deployment Strategy (Vercel)

### 9.1 Deployment Overview

SecondBrain will be deployed to Vercel with:
- **Frontend**: Next.js 14 app on Vercel Edge Network
- **Backend**: FastAPI deployed as serverless function or separate service
- **Database**: SQLite for MVP (upgrade to Vercel Postgres for production)
- **Preview Deployments**: Automatic preview for every PR

### 9.2 Environment Configuration

**Vercel Environment Variables** (via dashboard or `vercel env`):

```bash
# Production
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
DATABASE_URL=postgresql://...  # Production: Vercel Postgres
NEXT_PUBLIC_API_URL=https://api.studysync.com

# Preview (per branch)
ANTHROPIC_API_KEY=sk-ant-test-...
DATABASE_URL=sqlite:///./preview.db
NEXT_PUBLIC_API_URL=https://api-preview.studysync.com
```

### 9.3 Deployment Commands

**Install Vercel CLI:**
```bash
npm i -g vercel
vercel login
```

**Link Project:**
```bash
cd frontend
vercel link
```

**Deploy Preview:**
```bash
# Automatic on git push to any branch
git push origin feature/new-chat-ui
# Vercel automatically creates preview: https://studysync-abc123.vercel.app
```

**Deploy Production:**
```bash
# From main branch
vercel --prod
```

### 9.4 Backend Deployment Options

**Option A: Vercel Serverless Functions (Recommended for MVP)**
- Deploy FastAPI as `/api/*` routes using `vercel.json`
- Limited to 10s execution time (sufficient for SSE streaming)
- Auto-scales, zero-config

```json
// vercel.json
{
  "builds": [
    { "src": "frontend/**", "use": "@vercel/next" },
    { "src": "backend/app/main.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "backend/app/main.py" },
    { "src": "/(.*)", "dest": "frontend/$1" }
  ]
}
```

**Option B: Separate Backend Service**
- Deploy backend to Railway, Render, or Fly.io
- Better for long-running SSE connections
- More control over Python environment

### 9.5 Database Migration Strategy

**MVP: SQLite**
- Store `secondbrain.db` in `/tmp` on Vercel (ephemeral)
- Use Vercel KV or Vercel Blob for persistent storage

**Production: Vercel Postgres**
```bash
vercel postgres create studysync-db
vercel env pull
```

**Alembic Migration on Deploy:**
```bash
# Add to vercel.json build command
{
  "builds": [
    {
      "src": "backend/**",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "15mb"
      }
    }
  ],
  "build": {
    "env": {
      "PYTHONPATH": "./backend"
    }
  }
}

# Run migrations via Vercel build hook
postbuild: "alembic upgrade head"
```

### 9.6 Performance Monitoring

**Vercel Analytics:**
```typescript
// frontend/app/layout.tsx
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/next'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  )
}
```

### 9.7 CI/CD Integration

**GitHub Actions + Vercel:**
```yaml
# .github/workflows/preview.yml
name: Preview Deployment
on:
  pull_request:
    branches: [main]

jobs:
  deploy-preview:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          scope: ${{ secrets.VERCEL_ORG_ID }}
```

### 9.8 Deployment Checklist

Before deploying to production:
- [ ] All environment variables set in Vercel dashboard
- [ ] Database migrations tested
- [ ] API rate limits configured (Anthropic, OpenAI, Tavily)
- [ ] Error tracking configured (Sentry or Vercel Error Monitoring)
- [ ] CORS origins updated for production domain
- [ ] File upload size limits verified (Vercel has 4.5MB body limit)
- [ ] SSE streaming tested with production API keys
- [ ] Custom domain configured (studysync.com)
- [ ] SSL/HTTPS enabled (automatic with Vercel)

---

## Appendix A: Code Review Checklist (Vercel Best Practices)

Use this checklist when reviewing PRs to ensure best practices are followed.

### Performance (CRITICAL)

#### Bundle Size
- [ ] No barrel imports from `lucide-react`, `@/components`, etc.
- [ ] `next.config.ts` has `optimizePackageImports` configured
- [ ] Heavy components lazy-loaded with `next/dynamic`
- [ ] Analytics/tracking deferred with `{ ssr: false }`

#### Streaming & Data Fetching
- [ ] Page components use `<Suspense>` boundaries for independent data fetches
- [ ] Parallel data fetching with `Promise.all()` instead of sequential `await`
- [ ] RSC components minimize serialized props (only IDs, not full objects)
- [ ] SSE streaming properly integrated with TanStack Query cache

#### Re-renders
- [ ] Expensive computations wrapped in `useMemo()`
- [ ] Complex child components wrapped in `memo()`
- [ ] Event handlers don't subscribe to unnecessary state
- [ ] Zustand selectors are specific, not broad `(state => state)`

### Component Architecture (CRITICAL)

#### Boolean Props
- [ ] No components with >3 boolean props (`isLoading`, `isError`, `canEdit`, etc.)
- [ ] State variants use explicit component types instead of conditionals
- [ ] Compound components used for complex UI (Chat, Upload, Message)

#### State Management
- [ ] UI components don't directly import Zustand/TanStack Query hooks
- [ ] Context Provider decouples state implementation from UI
- [ ] State lifted to composition level when needed by multiple children

#### Composition
- [ ] `children` prop preferred over render props when possible
- [ ] Compound components expose subcomponents, not config objects
- [ ] Context provides `{ state, actions }` interface, not raw store

### Accessibility (HIGH)

#### Keyboard & Focus
- [ ] All interactive elements keyboard-accessible (Tab, Enter, Space)
- [ ] `focus-visible` styles present, never `outline: none` without replacement
- [ ] Icon-only buttons have `aria-label`
- [ ] Current page/section marked with `aria-current`

#### Forms & Inputs
- [ ] Text inputs have `aria-label` or associated `<label>`
- [ ] Error messages use `role="alert"` and `aria-live="assertive"`
- [ ] Submit buttons show loading state with `aria-busy`
- [ ] Form validation errors focus first invalid input

#### Dynamic Content
- [ ] Upload progress uses `aria-live="polite"` with `role="status"`
- [ ] Success/error toasts use `aria-live` appropriate to urgency
- [ ] Streaming messages announce new content for screen readers

### UI/UX (MEDIUM)

#### Typography & Formatting
- [ ] Dates formatted with `Intl.DateTimeFormat`
- [ ] File sizes formatted with `Intl.NumberFormat` (compact notation)
- [ ] Proper unicode: `…` not `...`, `"quotes"` not `"quotes"`
- [ ] Non-breaking spaces used appropriately (`Fig.\u00A0A`)

#### Motion & Animation
- [ ] Respects `prefers-reduced-motion` media query
- [ ] Only animates `transform` and `opacity` (GPU-accelerated)
- [ ] Animations can be disabled or skipped
- [ ] Loading states use deterministic spinners, not infinite loops

#### Images & Media
- [ ] Images have explicit `width` and `height` (prevent layout shift)
- [ ] Images use `loading="lazy"` for below-fold content
- [ ] Alt text provided for all images
- [ ] Video/audio has captions or transcripts

#### Virtualization
- [ ] Lists >50 items use `@tanstack/react-virtual`
- [ ] Infinite scroll implemented with intersection observer
- [ ] Skeleton loaders match final content dimensions

### Data & API (HIGH)

#### TanStack Query
- [ ] Query keys are deterministic and consistent
- [ ] `staleTime` configured appropriately for data type
- [ ] Mutations invalidate relevant query keys
- [ ] Error boundaries catch query errors gracefully

#### SSE Streaming
- [ ] EventSource properly closed on component unmount
- [ ] Reconnection logic handles dropped connections
- [ ] Partial messages handled (buffer incomplete JSON)
- [ ] Cache updated incrementally during stream

#### Error Handling
- [ ] Network errors show user-friendly messages
- [ ] Retry buttons enabled for failed requests
- [ ] Form validation errors displayed inline
- [ ] Global error boundary catches uncaught exceptions

### Security (CRITICAL)

#### Environment Variables
- [ ] No API keys in client-side code
- [ ] `NEXT_PUBLIC_*` variables contain no secrets
- [ ] `.env.local` in `.gitignore`
- [ ] Production env vars configured in Vercel dashboard

#### File Uploads
- [ ] File size limits enforced (both client and server)
- [ ] File type validation on server
- [ ] Uploaded files scanned for malware (if applicable)
- [ ] Uploads stored outside web root

#### CORS & API Security
- [ ] CORS origins explicitly listed, not `*`
- [ ] Rate limiting configured on API endpoints
- [ ] Input sanitization for user-generated content
- [ ] SQL injection prevention (parameterized queries)

### Testing (HIGH)

#### Unit Tests
- [ ] All services have >80% coverage
- [ ] External APIs mocked in unit tests
- [ ] Edge cases tested (empty state, error states, loading states)

#### Integration Tests
- [ ] API endpoints tested with TestClient
- [ ] Database migrations tested in CI
- [ ] File upload flow tested end-to-end

#### E2E Tests
- [ ] Critical user flows covered (upload → chat → response)
- [ ] Tested in Chrome (minimum browser requirement)
- [ ] Network conditions simulated (slow 3G)

### Deployment (MEDIUM)

#### Vercel Configuration
- [ ] `vercel.json` configured correctly for monorepo
- [ ] Environment variables set for all environments (preview, production)
- [ ] Custom domain configured and SSL enabled
- [ ] Vercel Analytics installed

#### Monitoring
- [ ] Error tracking configured (Sentry or Vercel)
- [ ] Performance monitoring active (Speed Insights)
- [ ] Database query performance logged
- [ ] API rate limit monitoring alerts configured

---

**How to Use This Checklist:**
1. Copy relevant sections into PR description
2. Reviewer checks each item during code review
3. Merge only when all CRITICAL and HIGH items pass
4. MEDIUM items can be follow-up tasks if needed
