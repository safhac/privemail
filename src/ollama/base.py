import ollama
import asyncio

# Global Concurrency Lock
OLLAMA_LOCK = asyncio.Lock()

# Use a single async client instance for efficiency
client = ollama.AsyncClient(host='http://localhost:11434')