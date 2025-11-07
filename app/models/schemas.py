from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# Items
class ItemInput(BaseModel):
    source: Optional[str] = Field(default="manual", description="Fuente del item")
    title: str
    url: Optional[str] = None
    summary: Optional[str] = None


# Embeddings
class EmbedItemRequest(ItemInput):
    model: str = Field(default="text-embedding-3-small")


class EmbedItemResponse(BaseModel):
    status: str
    item_id: Optional[int] = None
    embedding_model: Optional[str] = None
    embedding_dimensions: Optional[int] = None


# Scoring
class ScoreRequest(BaseModel):
    text: str
    context: Optional[str] = None


class ScoreResponse(BaseModel):
    relevance: float
    momentum: float
    roi_prediction: float


# Generación
class GeneratorRequest(BaseModel):
    topic: str
    brand_voice: Optional[str] = None
    keywords: Optional[List[str]] = None
    length: Optional[int] = Field(default=120, description="Largo aproximado del copy")


class GeneratorResponse(BaseModel):
    copy: str
    hashtags: List[str]
    visual_prompt: str
