"""pgvector similarity search helpers."""
from __future__ import annotations
from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.models import ProductCatalogItem, Company
from config import settings


def embed_text(texts: List[str]) -> List[List[float]]:
    """Lazily load the local sentence-transformer and embed."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(settings.embedding_model)
    return model.encode(texts, convert_to_numpy=True).tolist()


def search_product_catalog(
    query: str,
    db: Session,
    top_k: int = 3,
) -> List[Tuple[ProductCatalogItem, float]]:
    """Return top_k product catalog items most similar to query."""
    [vec] = embed_text([query])
    # pgvector cosine distance operator: <=>
    results = (
        db.query(
            ProductCatalogItem,
            ProductCatalogItem.embedding.cosine_distance(vec).label("distance"),
        )
        .order_by("distance")
        .limit(top_k)
        .all()
    )
    return [(item, round(1 - dist, 4)) for item, dist in results]


def search_companies(
    query: str,
    db: Session,
    top_k: int = 3,
) -> List[Tuple[Company, float]]:
    """Return top_k companies most similar to query (for RAG context)."""
    [vec] = embed_text([query])
    results = (
        db.query(
            Company,
            Company.embedding.cosine_distance(vec).label("distance"),
        )
        .order_by("distance")
        .limit(top_k)
        .all()
    )
    return [(company, round(1 - dist, 4)) for company, dist in results]