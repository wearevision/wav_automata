from __future__ import annotations

from fastapi import APIRouter

from ..models.schemas import (
    EmbedItemRequest,
    EmbedItemResponse,
    ScoreRequest,
    ScoreResponse,
)
from ..services.embeddings import DEFAULT_DIMENSIONS, DEFAULT_EMBEDDING_MODEL, get_embedding
from ..services.supabase_client import get_client

router = APIRouter(prefix="/semantic", tags=["semantic"])


@router.post("/embed_item", response_model=EmbedItemResponse)
def embed_item(payload: EmbedItemRequest) -> EmbedItemResponse:
    supabase = get_client()

    # 1) Inserta item base
    data = {
        "source": payload.source,
        "title": payload.title,
        "url": payload.url,
        "summary": payload.summary,
    }
    insert = supabase.table("items").insert(data).execute()
    item_id = insert.data[0]["id"] if insert.data else None

    # 2) Genera embedding del texto combinado
    text = f"{payload.title}\n\n{payload.summary or ''}"
    model = payload.model or DEFAULT_EMBEDDING_MODEL
    vector = get_embedding(text, model=model)

    # 3) Persiste embedding
    supabase.table("item_embeddings").insert(
        {
            "item_id": item_id,
            "embedding": vector,
            "model": model,
        }
    ).execute()

    return EmbedItemResponse(
        status="ok",
        item_id=item_id,
        embedding_model=model,
        embedding_dimensions=len(vector) if vector else DEFAULT_DIMENSIONS,
    )


@router.post("/score", response_model=ScoreResponse)
def score(payload: ScoreRequest) -> ScoreResponse:
    # Heurística simple como placeholder
    text = payload.text.strip()
    context = (payload.context or "").strip()

    # Relevancia basada en solapamiento simple de tokens
    tset = set(text.lower().split())
    cset = set(context.lower().split()) if context else set()
    overlap = len(tset & cset)
    relevance = min(1.0, (overlap / (len(tset) + 1e-6)) * 2)

    # Momentum: proxy por longitud y diversidad de tokens
    unique_ratio = len(tset) / max(1, len(text.split()))
    momentum = max(0.05, min(1.0, 0.3 + 0.7 * unique_ratio))

    # ROI predictivo: promedio ponderado
    roi = round((0.6 * relevance + 0.4 * momentum), 4)

    return ScoreResponse(
        relevance=round(relevance, 4), momentum=round(momentum, 4), roi_prediction=roi
    )
