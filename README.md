# StudySync

A conversational AI study assistant that helps you learn from PDFs, audio recordings, and URLs.

## Overview

StudySync is a full-stack application that combines document ingestion, AI-powered Q&A, web search, and persistent conversation history into a single ChatGPT-like interface for studying.

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

🚧 **Planning Phase** - Implementation has not started yet.

See [PLAN.md](./PLAN.md) for detailed implementation milestones.
See [PRD.md](./PRD.md) for product requirements.

## Getting Started

_(Coming soon after Milestone 1.1 is complete)_

## Documentation

- [PLAN.md](./PLAN.md) - Detailed implementation plan with 12 milestones
- [PRD.md](./PRD.md) - Product requirements document

## License

MIT

## Contributing

This is a personal learning project. Contributions are not currently accepted.
