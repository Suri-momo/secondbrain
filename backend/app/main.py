"""SecondBrain FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SecondBrain API",
    description="Your AI-powered second brain for documents, notes, and saved content",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to SecondBrain API"}


@app.get("/api/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "service": "secondbrain-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
