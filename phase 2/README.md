# Construction Knowledge Validation Platform — Phase 2

A Retrieval-Augmented Validation (RAV) system that extracts construction rules from documents, stores them in a knowledge repository, and uses an LLM to perform rule-based document comparison and validation.

## Setup

```bash
cd "D:\framework-agent\phase 2"
venv\Scripts\activate
pip install -r requirements.txt
ollama pull qwen2.5
```

## Usage

### CLI Mode

```bash
python main.py ingest              # Process documents → extract rules → store
python main.py graph               # Build knowledge graph from rules
python main.py categories          # List all rule categories
python main.py stats               # Show repository statistics
python main.py compare "query"     # Compare documents
python main.py serve               # Start API server with Swagger UI
```

### API Mode (Swagger UI)

```bash
python main.py serve
# Open http://localhost:8002/docs
```

## Pipeline

```
documents/ (20 txt files)
    → rule_generator.py (read → chunk → extract via Qwen)
    → database_store/rules.json (mock MongoDB)
    → knowledge_graph.py (build concept graph)
    → retriever.py (fetch relevant rules + build prompt)
    → compare_agent.py (select docs → compare → report)
    → logs (audit trail)
```

## Files

| File | Purpose |
|---|---|
| `config.py` | Paths, model name, chunk settings |
| `rule_generator.py` | Read text → chunk → extract rules via Qwen/Ollama |
| `database.py` | JSON-backed storage (MongoDB interface) |
| `knowledge_graph.py` | Build/query concept graph |
| `retriever.py` | Fetch relevant rules + build system prompt |
| `compare_agent.py` | Select documents + compare + report |
| `main.py` | CLI + FastAPI entry point |
