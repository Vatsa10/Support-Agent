# 24x7 AI Support Agent

A production-ready, plug-and-play AI support agent system using **ReACT Agent** architecture with **LangGraph**, **Qdrant**, and **Gemini 2.0 Flash**.

---

## Features

- **ReACT Agent** - Reasoning + Acting agent that dynamically uses tools
- **Hybrid Search** - Combines dense (Google embeddings) and sparse (BM25) vectors
- **Conversation Memory** - LangChain buffer memory for session-based context
- **Plug-and-Play** - Simply add documents to knowledge base directory
- **Multiple File Formats** - Supports `.txt`, `.md`, `.csv`, `.json`, `.html`
- **Auto-Escalation** - Creates support tickets when needed
- **Intent Classification** - Categorizes queries (billing, technical, shipping, etc.)
- **Sentiment Analysis** - Detects customer emotion (positive, neutral, negative, frustrated)

---

## Project Structure

```
support-agent/
├── src/
│   ├── __init__.py
│   ├── prompt.md                    # System prompt (Claude-style)
│   ├── config.py                    # Configuration
│   ├── config/
│   │   ├── __init__.py
│   │   └── system_prompt.py         # Dynamic prompt loading
│   ├── agents/
│   │   ├── __init__.py
│   │   └── react.py                 # ReACT agent implementation
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py                  # Tool abstraction
│   │   └── definitions.py           # Tool implementations
│   ├── memory/
│   │   ├── __init__.py
│   │   └── buffer.py                # Conversation buffer memory
│   ├── vector_db/
│   │   ├── __init__.py
│   │   ├── embeddings.py            # Dense + sparse embeddings
│   │   ├── ingestion.py            # Document chunking
│   │   └── retrieval.py            # Hybrid search
│   ├── knowledge_base/              # Add your documents here
│   │   ├── faqs.txt
│   │   ├── policies.txt
│   │   └── procedures.txt
│   └── api/
│       ├── __init__.py
│       ├── server.py                # FastAPI app
│       └── routes.py                # API endpoints
├── .env                             # Environment variables
├── requirements.txt
├── main.py                          # CLI interface
└── README.md
```

---

## Quick Start

### 1. Prerequisites

- Python 3.9+
- Docker (for Qdrant vector database)
- Google API Key

### 2. Setup

```bash
# Clone and navigate to project
cd support-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant:latest
```

### 3. Configure

Copy `.env.example` to `.env` and add your Google API key:

```env
GOOGLE_API_KEY=your_google_api_key_here
QDRANT_URL=http://localhost:6333
```

### 4. Add Knowledge Base

Simply drop files into `src/knowledge_base/`:

```
src/knowledge_base/
├── faqs.txt
├── policies.txt
├── procedures.txt
└── your_custom_docs.md  # Any supported format
```

Supported formats: `.txt`, `.md`, `.csv`, `.json`, `.html`

### 5. Run

**CLI Mode:**

```bash
python main.py
```

**API Server:**

```bash
python -m uvicorn src.api.server:app --reload --port 8000
```

---

## API Endpoints

### POST /api/chat

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I reset my password?",
    "user_id": "user123"
  }'
```

**Response:**

```json
{
  "thread_id": "uuid",
  "response": "To reset your password...",
  "ticket_id": null,
  "status": "resolved",
  "metadata": {
    "category": "account",
    "intent": "get_info",
    "sentiment": "neutral",
    "confidence": 0.85,
    "escalated": false,
    "retrieval_scores": {"dense": 0.9, "sparse": 0.7}
  }
}
```

### GET /api/chat/history//

Get conversation history.

### GET /api/health

Health check endpoint.

---

## How It Works

### ReACT Agent Loop

```
1. THINK   → Agent decides what action to take
2. ACT     → Execute tool (search, classify, generate, escalate)
3. OBSERVE → Get result and update state
4. REPEAT  → Continue until resolution
```

### Available Tools

| Tool                  | Description                                      |
| --------------------- | ------------------------------------------------ |
| `knowledge_search`  | Search knowledge base using hybrid vector search |
| `classify_intent`   | Classify query category, intent, and sentiment   |
| `generate_response` | Generate final response using LLM                |
| `create_ticket`     | Create support ticket for human escalation       |

### Memory System

- **Buffer Memory** - Stores conversation history per session
- **Automatic Trimming** - Keeps last 10 message pairs
- **Context Injection** - Past messages passed to LLM for continuity

---

## Configuration

| Variable                 | Default               | Description                     |
| ------------------------ | --------------------- | ------------------------------- |
| `GOOGLE_API_KEY`       | -                     | Required for Gemini             |
| `QDRANT_URL`           | http://localhost:6333 | Qdrant server                   |
| `QDRANT_API_KEY`       | -                     | Optional API key                |
| `TOP_K_RETRIEVAL`      | 5                     | Documents to retrieve           |
| `CONFIDENCE_THRESHOLD` | 0.7                   | Min confidence for auto-resolve |
| `PORT`                 | 8000                  | API server port                 |

---

## Customization

### Modify System Prompt

Edit `src/prompt.md` to change agent behavior:

```markdown
# Support Agent System Prompt
## 1. Core Identity
You are a helpful, empathetic customer support agent...
```

### Add New Tools

1. Create tool class in `src/tools/definitions.py`
2. Register with `tool_registry`
3. Agent will automatically use it

---

## Performance

- **Retrieval**: ~100-200ms
- **Classification**: ~500ms
- **Response Generation**: ~1-2s
- **Total Latency**: ~2-3s

---

## Production Deployment

1. Use PostgreSQL for persistent conversation storage
2. Add Redis for distributed memory
3. Deploy with Docker/GCP/AWS
4. Add monitoring (Prometheus, Grafana)
