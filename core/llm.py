"""Optional LLM access. Works only when the user supplies an API key (secrets or sidebar)."""
import requests

PROVIDERS = {
    "Groq": ("https://api.groq.com/openai/v1/chat/completions", "llama-3.1-8b-instant"),
    "OpenAI": ("https://api.openai.com/v1/chat/completions", "gpt-4o-mini"),
    "Gemini": (None, "gemini-1.5-flash"),
}


def chat(provider: str, api_key: str, prompt: str, timeout: int = 60) -> str:
    if provider not in PROVIDERS:
        raise ValueError("Unknown provider")
    url, model = PROVIDERS[provider]
    if provider == "Gemini":
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=timeout)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    r = requests.post(url, headers={"Authorization": f"Bearer {api_key}"},
                      json={"model": model, "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.3}, timeout=timeout)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()
