import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# Paths
BASE = Path(__file__).parent
DOCUMENTS = BASE / "documents"
RULES = BASE / "rules"
LOGS = BASE / "logs"

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
MONGO_DB = os.getenv("MONGO_DB", "construction_rav")

# LLM
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://175.155.64.191:19298/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen3.5-9B")

# Chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
