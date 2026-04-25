from __future__ import annotations

import math
import os
from functools import lru_cache
from typing import Iterable, Sequence

import torch
from huggingface_hub import login
from sentence_transformers import CrossEncoder, SentenceTransformer


DEFAULT_EMBED_MODEL = "intfloat/multilingual-e5-large"
DEFAULT_RERANK_MODEL = "BAAI/bge-reranker-v2-m3"

DEFAULT_BATCH_SIZE_CUDA = 16
DEFAULT_BATCH_SIZE_CPU = 4


def _get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    stripped = value.strip()
    return stripped if stripped else default


def _get_env_any(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = _get_env(name)
        if value is not None:
            return value
    return default


def _get_env_int_any(*names: str, default: int, min_value: int = 1) -> int:
    raw_value = _get_env_any(*names)
    if raw_value is None:
        return default

    try:
        parsed = int(raw_value)
    except ValueError:
        return default

    return max(min_value, parsed)


def get_hf_retrieval_top_k() -> int:

    return _get_env_int_any(
        "HF_TOP_K",
        "HR_TOP_K",
        "HR_RETRIEVAL_TOP_K",
        default=10,
        min_value=1,
    )


def get_hf_rerank_top_n_config() -> int:
    """
    Конфигурационное значение top_n для rerank-этапа.
    """
    return _get_env_int_any(
        "HF_RERANK_TOP_N",
        "HR_RERANK_TOP_N",
        default=10,
        min_value=1,
    )


def _normalize_text(text: str | None) -> str:
    return " ".join((text or "").strip().split())


def _safe_float(value) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _resolve_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def _resolve_batch_size(device: str) -> int:
    env_value = _get_env("HF_BATCH_SIZE")
    if env_value is not None:
        try:
            parsed = int(env_value)
            if parsed > 0:
                return parsed
        except ValueError:
            pass
    return DEFAULT_BATCH_SIZE_CUDA if device == "cuda" else DEFAULT_BATCH_SIZE_CPU


def _resolve_normalize_embeddings() -> bool:
    """
    Возвращает, нужно ли нормализовать embeddings.
    """
    raw = (
        _get_env("HF_NORMALIZE_EMBEDDINGS")
        or _get_env("HR_NORMALIZE_EMBEDDINGS")
        or _get_env("NORMALIZE_EMBEDDINGS")
    )

    if raw is None:
        return True

    normalized = raw.strip().lower()
    return normalized in {"1", "true", "yes", "y", "on"}


def _get_hf_token() -> str | None:
    return (
        _get_env("HF_TOKEN")
        or _get_env("HUGGINGFACE_TOKEN")
        or _get_env("HUGGING_FACE_HUB_TOKEN")
    )


def _login_if_needed() -> None:
    token = _get_hf_token()
    if not token:
        return
    try:
        login(token=token, add_to_git_credential=False)
    except Exception:
        pass


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(float(x) * float(y) for x, y in zip(a, b))


def _norm(a: Sequence[float]) -> float:
    return math.sqrt(sum(float(x) * float(x) for x in a))


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return 0.0
    denominator = _norm(a) * _norm(b)
    if denominator == 0:
        return 0.0
    return _dot(a, b) / denominator


def get_hf_device() -> str:
    return _resolve_device()


def get_hf_batch_size() -> int:
    return _resolve_batch_size(get_hf_device())


def should_normalize_embeddings() -> bool:
    return _resolve_normalize_embeddings()


def get_hf_normalize_embeddings() -> bool:
    return should_normalize_embeddings()


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    _login_if_needed()

    model_name = _get_env_any(
        "HF_EMBEDDING_MODEL",
        "HR_EMBED_MODEL",
        "SENTENCE_TRANSFORMER_MODEL",
        default=DEFAULT_EMBED_MODEL,
    )
    device = get_hf_device()

    model = SentenceTransformer(
        model_name,
        device=device,
        trust_remote_code=False,
    )
    return model


@lru_cache(maxsize=1)
def get_hf_embedding_model() -> SentenceTransformer:
    return get_embedding_model()


@lru_cache(maxsize=1)
def get_reranker_model() -> CrossEncoder:
    _login_if_needed()

    model_name = _get_env_any(
        "HF_RERANKER_MODEL",
        "HR_RERANK_MODEL",
        "CROSS_ENCODER_MODEL",
        default=DEFAULT_RERANK_MODEL,
    )
    device = get_hf_device()

    model = CrossEncoder(
        model_name_or_path=model_name,
        device=device,
        trust_remote_code=False,
    )
    return model


def get_hf_embeddings(
    texts: Sequence[str],
    *,
    normalize_embeddings: bool | None = None,
) -> list[list[float]]:
    normalized_texts = [_normalize_text(text) for text in (texts or [])]
    if not normalized_texts:
        return []

    if normalize_embeddings is None:
        normalize_embeddings = should_normalize_embeddings()

    model = get_hf_embedding_model()
    batch_size = get_hf_batch_size()

    vectors = model.encode(
        normalized_texts,
        batch_size=batch_size,
        normalize_embeddings=normalize_embeddings,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    return [vector.tolist() for vector in vectors]


def get_hf_single_embedding(
    text: str,
    *,
    normalize_embeddings: bool | None = None,
) -> list[float]:
    embeddings = get_hf_embeddings(
        [text],
        normalize_embeddings=normalize_embeddings,
    )
    return embeddings[0] if embeddings else []


def get_hf_top_k(
    query_embedding: Sequence[float],
    candidate_embeddings: Sequence[Sequence[float]],
    *,
    top_k: int = 10,
) -> list[tuple[int, float]]:
    if not query_embedding or not candidate_embeddings:
        return []

    scored: list[tuple[int, float]] = []
    for index, candidate_embedding in enumerate(candidate_embeddings):
        score = _cosine_similarity(query_embedding, candidate_embedding)
        scored.append((index, float(score)))

    scored.sort(key=lambda item: item[1], reverse=True)

    if top_k <= 0:
        return scored
    return scored[:top_k]


def get_hf_rerank_top_n(
    query_text: str,
    candidates: Iterable[dict],
    *,
    text_key: str = "aggregated_text",
    top_n: int = 10,
) -> list[dict]:
    normalized_query = _normalize_text(query_text)
    candidate_list = list(candidates or [])

    if not candidate_list:
        return []

    if not normalized_query:
        return candidate_list[:top_n]

    reranker = get_reranker_model()

    pairs: list[list[str]] = []
    for candidate in candidate_list:
        candidate_text = _normalize_text(str(candidate.get(text_key, "") or ""))
        pairs.append([normalized_query, candidate_text])

    raw_scores = reranker.predict(pairs)

    ranked_items: list[dict] = []
    for candidate, score in zip(candidate_list, raw_scores):
        item = dict(candidate)
        item["hf_rerank_score"] = _safe_float(score)
        ranked_items.append(item)

    ranked_items.sort(
        key=lambda row: _safe_float(row.get("hf_rerank_score", 0.0)),
        reverse=True,
    )

    return ranked_items[:top_n]


def get_hf_pair_scores(
    query_text: str,
    documents: Sequence[str],
) -> list[float]:
    normalized_query = _normalize_text(query_text)
    normalized_docs = [_normalize_text(doc) for doc in (documents or [])]

    if not normalized_query or not normalized_docs:
        return []

    reranker = get_reranker_model()
    pairs = [[normalized_query, doc] for doc in normalized_docs]
    raw_scores = reranker.predict(pairs)
    return [_safe_float(score) for score in raw_scores]