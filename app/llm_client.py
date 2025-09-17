import os, requests

def _ollama_generate(prompt: str) -> str:
    url = os.getenv("OLLAMA_URL", "http://ollama:11434/api/generate")
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    try:
        r = requests.post(url, json={"model": model, "prompt": prompt, "stream": False}, timeout=120)
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except Exception as e:
        return f"[OLLAMA_ERROR] {e}"

def _hf_generate(prompt: str) -> str:
    api_url = os.getenv("HF_API_URL", "").strip()
    api_key = os.getenv("HF_API_KEY", "").strip()
    if not api_url or not api_key:
        return "[HF_ERROR] Missing HF_API_URL or HF_API_KEY"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 256}}
    try:
        r = requests.post(api_url, headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        out = r.json()
        if isinstance(out, list) and out and "generated_text" in out[0]:
            return out[0]["generated_text"]
        if isinstance(out, dict) and "generated_text" in out:
            return out["generated_text"]
        return str(out)
    except Exception as e:
        return f"[HF_ERROR] {e}"

def _groq_generate(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    if not api_key:
        return "[GROQ_ERROR] Missing GROQ_API_KEY"
    url = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": model, "messages": [{"role":"user","content": prompt}], "temperature": 0.3}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[GROQ_ERROR] {e}"

def generate(prompt: str) -> str:
    backend = os.getenv("LLM_BACKEND", "ollama").lower()
    if backend == "ollama":
        return _ollama_generate(prompt)
    if backend in ("hf", "huggingface"):
        return _hf_generate(prompt)
    if backend == "groq":
        return _groq_generate(prompt)
    return f"[FALLBACK_GENERATION]\\nPrompt:{prompt[:120]}..."