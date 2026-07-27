import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
import config


# --- Read ---

def read_document(path):
    text = Path(path).read_text(encoding="utf-8")
    return {"source": Path(path).name, "text": text}


# --- Chunk ---

def chunk_text(text, source, size=config.CHUNK_SIZE):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            # Only look for breaks in the last half to avoid tiny chunks
            for sep in [". ", "\n", "; "]:
                pos = text.rfind(sep, start + size // 2, end)
                if pos > start:
                    end = pos + len(sep)
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append({"source": source, "chunk_index": len(chunks), "text": chunk})
        start = end
    return chunks


# --- LLM ---

import time

def call_llm(prompt, system=""):
    """Call on-prem Qwen via OpenAI-compatible /v1/chat/completions endpoint with retry logic."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    max_retries = 5
    backoff = 2
    for attempt in range(max_retries):
        try:
            resp = requests.post(f"{config.LLM_BASE_URL}/chat/completions", json={
                "model": config.LLM_MODEL,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 2048,
                "chat_template_kwargs": {"enable_thinking": False}
            }, timeout=60)
            if resp.status_code != 200:
                print(f"  HTTP Error {resp.status_code} on attempt {attempt + 1}: {resp.text}")
                resp.raise_for_status()
            
            msg = resp.json()["choices"][0]["message"]
            text = msg.get("content") or msg.get("reasoning_content") or ""
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            return text
        except (requests.exceptions.RequestException, KeyError, ValueError) as e:
            if attempt == max_retries - 1:
                raise e
            print(f"  Connection/LLM error on attempt {attempt + 1}/{max_retries}: {e}. Retrying in {backoff}s...")
            time.sleep(backoff)
            backoff *= 2
    return ""


EXTRACTION_PROMPT = """Extract ALL construction rules from this text as a JSON array.
Each rule must have:
- "category": domain area (Concrete, Structural, Electrical, Plumbing, Safety, etc.)
- "attribute": specific property (Grade, Spacing, Depth, Width, etc.)
- "operator": comparison (=, >, <, >=, <=, range, shall, must)
- "value": the specified value with units
- "description": brief human-readable description

Output ONLY a valid JSON array. No explanation.

Text:
{text}"""


def extract_rules(chunk):
    raw = call_llm(EXTRACTION_PROMPT.format(text=chunk["text"]))

    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start == -1 or end == 0:
        return []

    try:
        rules = json.loads(raw[start:end])
    except json.JSONDecodeError:
        print(f"  Warning: bad JSON from chunk {chunk['chunk_index']} of {chunk['source']}, skipping")
        return []

    now = datetime.now(timezone.utc).isoformat()
    for rule in rules:
        rule["rule_id"] = str(uuid.uuid4())
        rule["source"] = chunk["source"]
        rule["chunk_index"] = chunk["chunk_index"]
        rule["created_at"] = now
    return rules


# --- Pipeline ---

def process_document(path):
    doc = read_document(path)
    chunks = chunk_text(doc["text"], doc["source"])
    rules = []
    for chunk in chunks:
        rules.extend(extract_rules(chunk))
    return rules


def process_all_documents():
    config.RULES.mkdir(exist_ok=True)
    all_rules = []
    docs = sorted(config.DOCUMENTS.glob("*.txt"))
    for i, path in enumerate(docs, 1):
        out = config.RULES / f"{path.stem}_rules.json"
        if out.exists():
            try:
                rules = json.loads(out.read_text())
                print(f"[{i}/{len(docs)}] {path.name}... (Loaded from cache: {len(rules)} rules)")
                all_rules.extend(rules)
                continue
            except json.JSONDecodeError:
                pass
        
        print(f"[{i}/{len(docs)}] {path.name}...")
        rules = process_document(path)
        out.write_text(json.dumps(rules, indent=2))
        print(f"  -> {len(rules)} rules")
        all_rules.extend(rules)
    print(f"\nTotal: {len(all_rules)} rules from {len(docs)} documents")
    return all_rules
