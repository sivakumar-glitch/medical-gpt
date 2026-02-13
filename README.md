


# Medical Chatbot System

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (Optional, for containerized run)

## Quick Start (Docker)

The easiest way to run the full system is with Docker Compose:

```bash
docker-compose up --build
```

## Manual Setup & Run

### 1. Backend Setup

Navigate to the root directory.

**Install Dependencies:**
```bash
# Create virtual env if not exists
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\activate

# Install requirements
pip install -r backend/requirements.txt
```

**Run Ingestion (Generate Embeddings/Index):**
*Note: This downloads the embedding model (~100MB) and processes the CSV.*

```bash
# Make sure you are in the root directory and venv is active
python -m backend.app.rag.ingest
```

**Run Backend Server:**
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
Backend will be available at `http://localhost:8000`. API Docs at `http://localhost:8000/docs`.

### 2. Frontend Setup

Open a new terminal.

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```
Frontend will be available at `http://localhost:3000`.
