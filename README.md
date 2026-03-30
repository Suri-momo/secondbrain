# SecondBrain

[![CI](https://github.com/Suri-momo/secondbrain/actions/workflows/ci.yml/badge.svg)](https://github.com/Suri-momo/secondbrain/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/Suri-momo/secondbrain/branch/main/graph/badge.svg)](https://codecov.io/gh/Suri-momo/secondbrain)

A conversational AI study assistant that helps you learn from PDFs, audio recordings, URLs, and Twitter bookmarks.

## Overview

SecondBrain is a full-stack application that combines document ingestion, AI-powered Q&A, web search, and persistent conversation history into a single ChatGPT-like interface for studying and knowledge management.

## Tech Stack

**Frontend:**
- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS
- TanStack Query (server state)
- Zustand (client state)

**Backend:**
- Python 3.11+
- FastAPI
- SQLAlchemy + SQLite
- Anthropic Claude API
- OpenAI Whisper API (audio transcription)
- OpenAI TTS API (text-to-speech)
- Tavily Search API

## Features

- 📄 **Document Ingestion**: Upload PDFs, text files, audio recordings, or paste URLs
- 💬 **Conversational Chat**: Multi-turn conversations with streaming responses
- 🔍 **Web Search**: Optional real-time web search integration via Tavily
- 📝 **AI Summaries**: Generate 2-5 minute summaries of your study materials
- 🔊 **Text-to-Speech**: Listen to summaries with playback controls
- 💾 **Persistent History**: All conversations saved to SQLite
- 🎨 **Modern UI**: Clean, responsive interface with markdown support

## Project Status

🚀 **Active Development** - Foundation complete, building core features.

**Completed Milestones:**
- ✅ Milestone 1.1: Project Structure & Tooling Setup
- ✅ Milestone 1.2: Database Foundation
- ✅ Milestone 1.3: CI/CD Pipeline

**Current:**
- 🚧 Milestone 2.1: Core API Endpoints (next up)

See [PLAN.md](./PLAN.md) for detailed implementation milestones.
See [PRD.md](./PRD.md) for product requirements.
See [LOG.md](./LOG.md) for development progress.

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- npm 10+

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Suri-momo/secondbrain.git
   cd secondbrain
   ```

2. **Set up backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   pip install -r requirements-dev.txt

   # Copy environment variables
   cp .env.example .env
   # Edit .env and add your API keys

   # Run migrations
   alembic upgrade head
   ```

3. **Set up frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Install git hooks (optional)**
   ```bash
   cd .. # back to root
   npm install
   ```

### Running Locally

**Backend:**
```bash
cd backend
uvicorn app.main:app --reload
# API available at http://localhost:8000
```

**Frontend:**
```bash
cd frontend
npm run dev
# App available at http://localhost:3000
```

### Running Tests

**Backend:**
```bash
cd backend
pytest                  # Run all tests
pytest --cov=app       # With coverage
```

**Frontend:**
```bash
cd frontend
npm test               # Run Jest tests
npm run test:e2e       # Run Playwright E2E tests
```

**All tests (from root):**
```bash
npm test
```

## Documentation

- [PLAN.md](./PLAN.md) - Detailed implementation plan with 12 milestones
- [PRD.md](./PRD.md) - Product requirements document
- [DESIGN.md](./DESIGN.md) - System architecture and design decisions
- [LOG.md](./LOG.md) - Development log with milestone progress
- [TAKEAWAYS.md](./TAKEAWAYS.md) - Key decisions and deployment strategy analysis

## License

MIT

## Contributing

This is a personal learning project. Contributions are not currently accepted.
