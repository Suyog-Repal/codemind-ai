from abc import ABC, abstractmethod
from config import get_settings


class BaseLLM(ABC):
    @abstractmethod
    def generate(self, prompt: str, system: str = "") -> str:
        ...

    @abstractmethod
    def stream(self, prompt: str, system: str = ""):
        ...


# ── Gemini provider ────────────────────────────────────────────────────────────

class GeminiLLM(BaseLLM):
    def __init__(self, api_key: str, model: str):
        from google import genai
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, system: str = "") -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = self.client.models.generate_content(
            model=self.model,
            contents=full_prompt,
        )
        return response.text

    def stream(self, prompt: str, system: str = ""):
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        for chunk in self.client.models.generate_content_stream(
            model=self.model,
            contents=full_prompt,
        ):
            if chunk.text:
                yield chunk.text


# ── Groq provider (free tier, no daily quota issues) ──────────────────────────

class GroqLLM(BaseLLM):
    """
    Uses Groq's free API — no per-day quota, just a per-minute rate limit
    that is far more generous than Gemini's free tier.

    Sign up at https://console.groq.com and set GROQ_API_KEY in your .env.
    Recommended model: llama-3.3-70b-versatile (free)
    """

    def __init__(self, api_key: str, model: str):
        from groq import Groq
        self.client = Groq(api_key=api_key)
        self.model = model

    def _messages(self, prompt: str, system: str) -> list[dict]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return messages

    def generate(self, prompt: str, system: str = "") -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self._messages(prompt, system),
        )
        return response.choices[0].message.content

    def stream(self, prompt: str, system: str = ""):
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=self._messages(prompt, system),
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


# ── Factory ───────────────────────────────────────────────────────────────────

def get_llm_client() -> BaseLLM:
    settings = get_settings()

    if settings.llm_provider == "gemini":
        return GeminiLLM(settings.gemini_api_key, settings.llm_model)

    if settings.llm_provider == "groq":
        return GroqLLM(settings.groq_api_key, settings.groq_model)

    raise ValueError(
        f"Unsupported LLM_PROVIDER '{settings.llm_provider}'. "
        "Valid options: 'gemini', 'groq'"
    )


# ── Prompt templates ──────────────────────────────────────────────────────────

def build_prompt(query: str, context: str, task_type: str) -> str:
    templates = {
        "qa": (
            "You are a codebase assistant. Answer only from the supplied context.\n"
            "Do not invent files, functions, line numbers, libraries, or behavior.\n"
            "If the context does not contain the answer, say that clearly.\n"
            "Use concise plain Markdown with short headings and bullet points. "
            "Do not use a table unless the user asks for one. "
            "Cite only the exact file paths and line ranges present in the context.\n\n"
            "Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
        ),
        "bug_finding": (
            "Analyze the following code for potential bugs, security issues, or bad practices.\n\n"
            "Code:\n{context}\n\n"
            "Return a JSON list of objects with keys: line, issue, severity, suggestion."
        ),
        "docstring": (
            "Write a clear, concise docstring for the following function. "
            "Follow standard conventions for its language.\n\nFunction:\n{query}"
        ),
        "file_creation": (
            "Generate complete, production-ready code for the following request.\n\n"
            "Request: {query}\n\nRelevant existing code for context:\n{context}\n\n"
            "Return only the code, no explanations."
        ),
    }
    template = templates.get(task_type, templates["qa"])
    return template.format(query=query, context=context)


def count_tokens(text: str) -> int:
    import tiktoken
    encoder = tiktoken.get_encoding("cl100k_base")
    return len(encoder.encode(text))