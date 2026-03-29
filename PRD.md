# StudySync — Product Requirements Document (PRD)

**Version:** 1.0
**Date:** 2026-03-28
**Status:** Draft

---

## 1. Overview

### 1.1 Product Summary
StudySync is a personal AI study assistant that lets users upload learning materials (PDFs, text files, audio recordings) or paste a URL, then have a multi-turn conversation about the content. It combines Claude's reasoning, real-time web search, and persistent conversation history into a single ChatGPT-like interface.

### 1.2 Problem Statement
Students and self-learners frequently switch between reading PDFs, listening to lectures, searching the web, and taking notes — all in separate tools. There is no single place to ingest all of these formats and have an intelligent conversation across them.

### 1.3 Goal
Build a focused, single-user web app that collapses document ingestion, AI Q&A, and web research into one conversational interface, saving study time and improving retention through active dialogue with content.

---

## 2. Users

### Primary User
A student or self-learner who:
- Has lecture notes, research PDFs, or audio recordings they want to query
- Wants to ask follow-up questions and get cited answers from their own materials
- Occasionally wants to supplement their materials with live web search results

### Out of Scope (v1)
- Multi-user / team collaboration
- Mobile app
- Real-time document co-editing
- Flashcard or quiz generation (future phase)

---

## 3. Core Features

### F1 — Document Ingestion
Users can add content to a conversation in three ways:

| Input Type | Accepted Formats | How It Works |
|---|---|---|
| File upload | PDF, TXT | Parsed to plain text, stored per conversation |
| Audio upload | MP3, WAV, M4A | Transcribed via OpenAI Whisper, stored as text |
| URL paste | Any public URL | Scraped and stripped to plain text (8,000 char limit) |

- Multiple documents can be added to a single conversation.
- All extracted text is stored and used as context for every subsequent message in that conversation.
- Max file size: 50 MB.
- Unsupported formats return a clear error.

### F2 — Conversational Q&A (Chat)
- Users type messages and receive streaming responses from Claude.
- Claude's responses are grounded in the uploaded document content (passed in the system prompt).
- Responses stream token-by-token (SSE), matching a ChatGPT-like feel.
- Conversation history (last 20 turns) is included in every request for coherent multi-turn dialogue.
- Markdown is rendered in assistant responses (bold, code blocks, lists, headings).

### F3 — Web Search Mode
- A toggle in the chat input enables "Web Search" mode for a given message.
- When enabled, Tavily Search is called with the user's query and up to 5 results are injected into Claude's context.
- Source cards (`{title, url, snippet}`) are displayed beneath the assistant's response.
- Web search is opt-in per message, not automatic.

### F4 — Conversation Management (Sidebar)
- All conversations are listed in a persistent left sidebar, ordered by most recent.
- Users can:
  - Create a new conversation (blank or with immediate file upload)
  - Rename a conversation
  - Delete a conversation
- Conversation title is auto-generated from the first user message.
- Clicking a conversation restores its full message history.

### F5 — Persistent History
- All messages (user and assistant) are stored in SQLite.
- Refreshing the page or revisiting a conversation URL restores the full thread.
- History persists across browser sessions (server-side, not localStorage).

### F6 — Twitter Bookmarks Import (Knowledge Base)
Users can import their saved Twitter bookmarks to create a searchable knowledge base:

| Feature | Description |
|---|---|
| **Import Method** | Upload Twitter data export (`bookmarks.json`) |
| **Content Imported** | Tweet text, author, URL, date, full thread context |
| **Organization** | Single conversation: "Twitter Bookmarks (YYYY-MM-DD)" |
| **Search** | Ask questions: "What have I saved about React?" |
| **Personal Notes** | Add learning notes as chat messages |
| **Monthly Sync** | Dashboard reminder to re-import (merge new bookmarks) |

**User Flow:**
1. User requests Twitter data export (Settings → Download your data)
2. After 24h, Twitter emails `bookmarks.json`
3. User drags & drops file into StudySync
4. StudySync parses ~100 bookmarks, extracts threads
5. Creates "Twitter Bookmarks" conversation
6. User asks: "What have I saved about Next.js?"
7. AI finds relevant tweets + summarizes
8. User adds notes: "📝 Learned: App Router replaces pages..."
9. Monthly reminder to re-import (new bookmarks merged)

**Problem Solved:** Users save tweets but never have time to review them and can't find them when needed.

---

## 4. User Stories

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| US-01 | Student | Upload a PDF lecture slide | I can ask questions about specific slides |
| US-02 | Student | Upload an MP3 recording | I can ask what was said at a specific point |
| US-03 | Student | Paste a URL | I can chat about an article without copy-pasting it |
| US-04 | Student | Ask a follow-up question | The assistant remembers what we discussed earlier |
| US-05 | Student | Toggle web search | I can get current information alongside my own materials |
| US-06 | Student | See source citations | I can verify where the answer came from |
| US-07 | Student | See a list of my past conversations | I can pick up where I left off |
| US-08 | Student | Delete a conversation | I can clean up sessions I no longer need |
| US-09 | Student | Rename a conversation | I can give it a meaningful title |
| US-10 | Student | Refresh the page | I don't lose my conversation history |
| US-11 | Student | Import my Twitter bookmarks | I can search tweets I saved months ago |
| US-12 | Student | Ask about saved tweets | I can find relevant content without scrolling through 100 bookmarks |
| US-13 | Student | Add learning notes to tweets | I can document what I learned from each topic |
| US-14 | Student | Get monthly import reminders | I keep my knowledge base up-to-date effortlessly |

---

## 5. Functional Requirements

### 5.1 Backend API

| Endpoint | Method | Description |
|---|---|---|
| `/api/conversations` | GET | List all conversations |
| `/api/conversations` | POST | Create a new conversation |
| `/api/conversations/{id}` | PATCH | Rename a conversation |
| `/api/conversations/{id}` | DELETE | Delete a conversation and its messages/documents |
| `/api/conversations/{id}/messages` | GET | Fetch full message history |
| `/api/conversations/{id}/chat` | POST | Send a message, returns SSE streaming response |
| `/api/conversations/{id}/upload` | POST | Upload a file (multipart/form-data) |
| `/api/conversations/{id}/url` | POST | Ingest a URL |
| `/api/conversations/{id}/twitter` | POST | Import Twitter bookmarks JSON |
| `/api/search` | POST | Standalone Tavily web search |
| `/api/health` | GET | Health check (used by CI) |

### 5.2 Frontend Pages & Routes

| Route | Description |
|---|---|
| `/` | Redirect to `/chat` |
| `/chat` | New conversation (empty state) |
| `/chat/{conversationId}` | Active conversation view |

### 5.3 Data Models

**Conversation**
```
id            UUID (PK)
title         string
created_at    datetime
updated_at    datetime
```

**Message**
```
id               UUID (PK)
conversation_id  UUID (FK)
role             enum: user | assistant
content          text
sources          JSON (nullable) — [{title, url, snippet}]
created_at       datetime
```

**Document**
```
id               UUID (PK)
conversation_id  UUID (FK)
filename         string
file_type        enum: pdf | txt | audio | url
extracted_text   text
created_at       datetime
```

---

## 6. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Streaming latency** | First token must appear within 2 seconds of sending a message |
| **Upload speed** | File processing (parse + store) must complete within 10 seconds for files ≤ 50 MB |
| **Context limit** | Document context passed to Claude capped at 4,000 characters (naive truncation for MVP) |
| **History window** | Last 20 turns included in each Claude request |
| **Reliability** | UI must gracefully handle network errors (show error state, allow retry) |
| **Security** | No user auth in v1 (single-user local tool); API keys stored server-side only, never exposed to frontend |
| **Browser support** | Latest Chrome, Safari, Firefox |
| **Accessibility** | Keyboard navigable chat input; sufficient color contrast |

---

## 7. Out of Scope (v1)

- User authentication / multi-user support
- Vector database / semantic search over documents
- Flashcard or quiz generation
- Export conversation as PDF/DOCX
- Mobile app
- Real-time collaborative editing
- Image or video file support
- Streaming document upload progress (indeterminate only)
- Twitter API auto-sync (requires $100/month subscription)
- LinkedIn / Reddit bookmarks import (future platforms)
- AI categorization of bookmarks by topic (future enhancement)

---

## 8. Success Metrics

| Metric | Target |
|---|---|
| Upload → first AI response | < 15 seconds for a typical PDF |
| Streaming first-token latency | < 2 seconds |
| Conversation history load time | < 500ms |
| All CI checks pass on every PR | 100% |
| Backend test coverage | ≥ 80% |
| Frontend component test coverage | ≥ 80% |

---

## 9. Milestones and Timeline

| Phase | Deliverable | Target |
|---|---|---|
| Phase 1 — Scaffold | Both apps start; monorepo structure in place | Day 1 |
| Phase 2 — Backend Core | All API routes functional, services integrated | Days 2–4 |
| Phase 3 — Frontend | Full ChatGPT-like UI, streaming, upload | Days 5–7 |
| Phase 4 — Integration | End-to-end local flows verified | Day 8 |
| Phase 5 — Testing | Full test suite + CI pipeline green | Days 9–10 |

---

## 10. Open Questions

| # | Question | Owner | Status |
|---|---|---|---|
| OQ-1 | Should conversation titles be auto-generated by Claude or extracted from the first N words of the user message? | — | Open |
| OQ-2 | Should documents be scoped per-conversation or shareable across conversations? | — | Open (defaulting to per-conversation) |
| OQ-3 | What happens when the extracted text from a large PDF exceeds 4,000 chars — truncate silently or warn the user? | — | Open |
| OQ-4 | Should web search be triggered automatically when Claude lacks confidence, or always manual? | — | Open (defaulting to manual toggle) |
| OQ-5 | Is a 50 MB file size limit the right cap, or should it be lower for audio (Whisper has its own limits)? | — | Open |
