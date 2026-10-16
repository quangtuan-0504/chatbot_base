import json
from dataclasses import dataclass, asdict


@dataclass
class SearchMetrics:
    """Cost and latency of retrieving context for one query, logged as one 'search_metrics' JSON line.
    Covers query rewrite (LLM), query embedding and Milvus search; not the final answer generation."""
    rewrite_prompt_tokens: int = 0
    rewrite_completion_tokens: int = 0
    rewrite_reasoning_tokens: int = 0  # part of completion tokens, for reasoning models
    embedding_tokens: int = 0
    rewrite_ms: float = 0.0
    embedding_ms: float = 0.0
    vector_search_ms: float = 0.0  # Milvus: dense + BM25 search and vicinity queries
    total_ms: float = 0.0
    rewritten: bool = False
    context_chars: int = 0
    n_files: int = 0
    error: str = ""

    @property
    def total_tokens(self) -> int:
        return self.rewrite_prompt_tokens + self.rewrite_completion_tokens + self.embedding_tokens

    def add_rewrite_usage(self, usage) -> None:
        """Read token usage of a chat completion; some OpenAI-compatible servers return no usage."""
        if usage is None:
            return
        self.rewrite_prompt_tokens += usage.prompt_tokens or 0
        self.rewrite_completion_tokens += usage.completion_tokens or 0
        details = getattr(usage, "completion_tokens_details", None)
        self.rewrite_reasoning_tokens += (getattr(details, "reasoning_tokens", 0) or 0) if details else 0

    def add_embedding_usage(self, usage) -> None:
        if usage is None:
            return
        self.embedding_tokens += usage.total_tokens or usage.prompt_tokens or 0

    def to_log(self) -> str:
        data = asdict(self)
        data["total_tokens"] = self.total_tokens
        for key in ("rewrite_ms", "embedding_ms", "vector_search_ms", "total_ms"):
            data[key] = round(data[key], 1)
        return "search_metrics " + json.dumps(data, ensure_ascii=False)
