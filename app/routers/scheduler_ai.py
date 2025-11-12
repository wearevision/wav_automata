"""Scheduler AI router.

Decide cuentas, formatos y horarios óptimos para publicar cada día
en base a métricas históricas (Supabase) y relevancia temática.

Notas:
- Las tablas referenciadas son sugeridas: `posts_feedback` y `items`.
  Si no existen, los endpoints devuelven heurísticas de respaldo y
  no fallan. El esquema puede evolucionar sin romper la API.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

try:
    import numpy as np
except Exception:  # pragma: no cover - fallback mínimo
    # Fallback liviano si numpy no está disponible en el entorno del editor
    import random as _random

    class _RNG:
        def __init__(self, seed: int):
            self._r = _random.Random(seed)

        def integers(self, low: int, high: Optional[int] = None) -> int:
            if high is None:
                return self._r.randrange(low)
            return self._r.randrange(low, high)

    class _NP:
        @staticmethod
        def mean(arr: List[float]) -> float:
            return float(sum(arr) / len(arr)) if arr else 0.0

        @staticmethod
        def clip(x: float, a: float, b: float) -> float:
            return max(a, min(b, x))

        class random:
            @staticmethod
            def default_rng(seed: int) -> _RNG:
                return _RNG(seed)

    np = _NP()

from ..models.schemas import GeneratorRequest, GeneratorResponse
from ..services.supabase_client import get_client
from .generator import generate_post

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


# --------------------------
# Pydantic models
# --------------------------


class NextPostResponse(BaseModel):
    account: str
    recommended_time: str = Field(description="Hora local en formato HH:MM")
    content_type: str
    topic: str
    priority: float


class FeedbackRequest(BaseModel):
    account: str
    post_id: str
    likes: int
    comments: int
    saves: int
    reach: int
    followers: Optional[int] = Field(default=None, description="Followers del momento del post")


class FeedbackResponse(BaseModel):
    status: str
    stored: bool
    engagement_score: float


class TrendItem(BaseModel):
    topic: str
    momentum: float


class AutoGenerateRequest(BaseModel):
    account: str = "vibecodinglatam"
    brand_voice: Optional[str] = None
    keywords: Optional[List[str]] = None
    length: Optional[int] = 120


class AutoGenerateResponse(BaseModel):
    scheduled: NextPostResponse
    content: GeneratorResponse
    # Nota: En algunas instalaciones la tabla `items` usa BIGSERIAL (int)
    # y en otras UUID. Para compatibilidad amplia, exponemos item_id como str.
    item_id: Optional[str] = None


class WeightsResponse(BaseModel):
    """Parámetros actuales del modelo por cuenta.

    Atributos:
        account: Cuenta consultada.
        w_engagement: Peso del componente de engagement.
        w_relevance: Peso del componente de relevancia temática.
        learning_rate: Tasa de aprendizaje usada en el ajuste incremental.
        updated_at: Timestamp de última actualización, si existe.
        message: Mensaje informativo (por ejemplo, uso de defaults).
        error: Código de error si la consulta falla.
    """

    account: str
    w_engagement: float
    w_relevance: float
    learning_rate: float
    updated_at: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


class WeightsUpdatePayload(BaseModel):
    """Solicitud de actualización manual de pesos del scheduler.

    Se valida que w_engagement y w_relevance estén en [0,1], que learning_rate
    esté en [0.001, 0.1] y que la suma de los pesos sea ≈ 1 con tolerancia 0.05.
    """

    account: str
    w_engagement: float
    w_relevance: float
    learning_rate: float = 0.05


class WeightsUpdateResponse(BaseModel):
    account: str
    status: str
    new_weights: dict


class RunDailyRequest(BaseModel):
    """Payload para ejecutar generación diaria por múltiples cuentas."""

    accounts: List[str] = ["vibecodinglatam"]
    brand_voice: Optional[str] = None
    keywords: Optional[List[str]] = None
    length: Optional[int] = 120


class RunDailyResponse(BaseModel):
    results: List[AutoGenerateResponse]


# --------------------------
# Utilidades internas
# --------------------------


def _stable_choice(options: List[str], seed: int) -> str:
    rng = np.random.default_rng(seed)
    idx = int(rng.integers(0, len(options)))
    return options[idx]


def _stable_time(seed: int) -> str:
    """Devuelve una hora HH:MM estable para el día, basada en seed."""
    rng = np.random.default_rng(seed)
    hour = int(rng.integers(17, 21))  # ventana 17-20 hs
    minute = int(rng.integers(0, 2)) * 30  # 00 o 30
    return f"{hour:02d}:{minute:02d}"


def _heuristic_next_post(account: str, topic_hint: str | None = None) -> NextPostResponse:
    now = datetime.now().astimezone()
    seed = int(now.strftime("%Y%j"))  # año+día_juliano
    weekday = now.weekday()

    # Formatos candidatos
    formats = ["reel", "carousel", "post", "story"]
    content_type = _stable_choice(formats, seed + weekday)

    # Horas sugeridas por día (semilla + patrón base)
    recommended_time = _stable_time(seed + 3 * weekday)

    topic = topic_hint or "Innovación humana y colaboración IA"
    priority = float(np.clip(0.75 + (weekday * 0.01), 0.75, 0.9))

    return NextPostResponse(
        account=account,
        recommended_time=recommended_time,
        content_type=content_type,
        topic=topic,
        priority=round(priority, 2),
    )


def _compute_engagement_score(row: Dict[str, float]) -> float:
    likes = float(row.get("likes", 0))
    comments = float(row.get("comments", 0))
    saves = float(row.get("saves", 0))
    followers = float(row.get("followers", 0) or 0)
    if followers <= 0:
        return 0.0
    return float((likes + 2 * comments + 0.5 * saves) / followers)


def _simple_relevance(text: str, context: str) -> float:
    """Replica una métrica de relevancia simple estilo /semantic/score."""
    tset = set(text.lower().split())
    cset = set(context.lower().split()) if context else set()
    overlap = len(tset & cset)
    return float(min(1.0, (overlap / (len(tset) + 1e-6)) * 2))


def _topical_relevance(supabase: Any, topic: str) -> float:
    """Calcula relevancia temática respecto a items recientes.

    Hoy usa un proxy de solapamiento de tokens contra títulos/resúmenes
    de items recientes. En el futuro, puede sustituirse por embeddings
    y similitudes promedio.
    """
    try:
        if not supabase:
            return 0.5
        # Últimos 20 items
        recent = (
            supabase.table("items")
            .select("title,summary")
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        ctx_list = []
        for r in recent.data or []:
            title = (r.get("title") or "").strip()
            summary = (r.get("summary") or "").strip()
            if title:
                ctx_list.append(title)
            if summary:
                ctx_list.append(summary)
        context = " \n ".join(ctx_list)
        if not context:
            return 0.5
        return _simple_relevance(topic, context)
    except Exception:
        return 0.5


def _get_model_params(supabase: Any, account: str) -> tuple[float, float, float]:
    """Obtiene (w_engagement, w_relevance, learning_rate) para una cuenta.

    Si no existe registro, intenta crearlo con defaults (0.6, 0.4, 0.05).
    Ante cualquier error, devuelve los defaults.
    """
    DEFAULTS = (0.6, 0.4, 0.05)
    try:
        if not supabase:
            return DEFAULTS
        res = (
            supabase.table("scheduler_model_params")
            .select("w_engagement,w_relevance,learning_rate")
            .eq("account", account)
            .limit(1)
            .execute()
        )
        row = (res.data or [None])[0]
        if not row:
            try:
                supabase.table("scheduler_model_params").insert(
                    {
                        "account": account,
                        "w_engagement": 0.6,
                        "w_relevance": 0.4,
                        "learning_rate": 0.05,
                    }
                ).execute()
                return DEFAULTS
            except Exception:
                return DEFAULTS
        return (
            float(row.get("w_engagement", 0.6)),
            float(row.get("w_relevance", 0.4)),
            float(row.get("learning_rate", 0.05)),
        )
    except Exception:
        return DEFAULTS


def _update_model_params(
    supabase: Any, account: str, w_e: float, w_r: float, learning_rate: float
) -> None:
    """Actualiza pesos del modelo para una cuenta. Falla de forma silenciosa."""
    try:
        if not supabase:
            return
        supabase.table("scheduler_model_params").upsert(
            {
                "account": account,
                "w_engagement": w_e,
                "w_relevance": w_r,
                "learning_rate": learning_rate,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()
    except Exception:
        # Silencioso: no romper endpoint por fallos de tabla/conexión
        pass


# --------------------------
# Endpoints
# --------------------------


@router.get("/next_post", response_model=NextPostResponse)
def next_post(account: str = "vibecodinglatam") -> NextPostResponse:
    """Recomienda cuenta, formato y horario para la próxima publicación.

    Combina engagement histórico y relevancia temática:
    priority = 0.6 * engagement_score + 0.4 * topical_relevance
    """
    try:
        supabase = get_client()
    except Exception:
        # Sin entorno de Supabase configurado: usar heurística directa
        return _heuristic_next_post(account)

    # 1) Intentar derivar topic más prometedor (título más reciente)
    topic_hint = None
    try:
        items = (
            supabase.table("items")
            .select("title")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if items.data:
            topic_hint = (items.data[0].get("title") or "").strip() or None
    except Exception:
        topic_hint = None

    # 2) Buscar métricas históricas por cuenta para inferir formato y hora
    try:
        rows = (
            supabase.table("posts_feedback")
            .select("likes,comments,saves,followers,content_type,posted_at")
            .eq("account", account)
            .order("posted_at", desc=True)
            .limit(200)
            .execute()
        )

        data = rows.data or []
        if not data:
            return _heuristic_next_post(account, topic_hint)

        # Agregación por (content_type, hour)
        buckets: Dict[tuple, List[float]] = {}
        hours: Dict[tuple, str] = {}
        for r in data:
            score = _compute_engagement_score(r)
            ctype = (r.get("content_type") or "reel").lower()
            posted_at = r.get("posted_at")
            try:
                # posted_at ISO -> hour local
                dt = (
                    datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
                    if isinstance(posted_at, str)
                    else datetime.now(timezone.utc)
                )
                hour_local = dt.astimezone().strftime("%H:00")
            except Exception:
                hour_local = "18:00"
            key = (ctype, hour_local)
            buckets.setdefault(key, []).append(score)
            hours[key] = hour_local

        # Seleccionar bucket top por promedio
        best_key = None
        best_value = -1.0
        for k, scores in buckets.items():
            avg = float(np.mean(scores)) if scores else 0.0
            if avg > best_value:
                best_value = avg
                best_key = k

        if best_key is None:
            return _heuristic_next_post(account, topic_hint)

        content_type, recommended_time = best_key

        # 3) Relevancia temática
        topic = topic_hint or "Innovación humana y colaboración IA"
        top_rel = _topical_relevance(supabase, topic)

        # 4) Pesos por cuenta (defaults si no existen)
        w_e, w_r, _lr = _get_model_params(supabase, account)
        best_value = float(np.clip(best_value, 0.0, 1.0))
        top_rel = float(np.clip(top_rel, 0.0, 1.0))
        priority = float(w_e * best_value + w_r * top_rel)

        return NextPostResponse(
            account=account,
            recommended_time=recommended_time,
            content_type=str(content_type),
            topic=topic,
            priority=round(priority, 2),
        )
    except Exception:
        # Cualquier error: fallback estable
        return _heuristic_next_post(account, topic_hint)


@router.post("/feedback", response_model=FeedbackResponse)
def store_feedback(payload: FeedbackRequest) -> FeedbackResponse:
    """Guarda feedback real del post publicada para mejorar el scheduler."""
    try:
        supabase = get_client()
    except Exception:
        engagement = _compute_engagement_score(payload.model_dump())
        return FeedbackResponse(status="error", stored=False, engagement_score=round(engagement, 4))

    engagement = _compute_engagement_score(payload.model_dump())

    try:
        supabase.table("posts_feedback").insert(
            {
                "account": payload.account,
                "post_id": payload.post_id,
                "likes": payload.likes,
                "comments": payload.comments,
                "saves": payload.saves,
                "reach": payload.reach,
                "followers": payload.followers,
                "engagement_score": engagement,
                "posted_at": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()
        stored_ok = True
    except Exception:
        # Si no se pudo guardar, seguir con aprendizaje y reportar stored=False
        stored_ok = False

    # Mini gradient descent learning
    try:
        # 1) Pesos actuales
        w_e, w_r, lr = _get_model_params(supabase, payload.account)

        # 2) Señales
        #    Para topical_relevance usamos topic más reciente como proxy
        topic_hint = None
        try:
            items = (
                supabase.table("items")
                .select("title")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if items.data:
                topic_hint = (items.data[0].get("title") or "").strip() or None
        except Exception:
            topic_hint = None
        topic = topic_hint or "Innovación humana y colaboración IA"
        top_rel = float(np.clip(_topical_relevance(supabase, topic), 0.0, 1.0))

        # 3) Predicción y error
        if hasattr(np, "array"):
            weights = np.array([w_e, w_r], dtype=float)
            feats = np.array([engagement, top_rel], dtype=float)
            pred = float(weights.dot(feats))
            err = float(engagement - pred)
            weights = weights + lr * err * feats
            s = float(weights.sum()) or 1.0
            weights = np.clip(weights / s, 0.0, 1.0)
            w_e, w_r = float(weights[0]), float(weights[1])
        else:
            pred = w_e * engagement + w_r * top_rel
            err = engagement - pred
            w_e = w_e + lr * err * engagement
            w_r = w_r + lr * err * top_rel
            s = (w_e + w_r) or 1.0
            w_e, w_r = max(0.0, w_e / s), max(0.0, w_r / s)

        # 4) Persistir
        _update_model_params(supabase, payload.account, w_e, w_r, lr)
    except Exception as e:
        print("[scheduler.learning] warning:", e)

    return FeedbackResponse(status="ok", stored=bool(stored_ok), engagement_score=round(engagement, 4))


@router.get("/trends", response_model=List[TrendItem])
def trends(limit: int = 6) -> List[TrendItem]:
    """Calcula momentum semanal por tema simple derivado de títulos.

    momentum = current_week_count / max(1, previous_week_count)
    """
    try:
        supabase = get_client()
    except Exception:
        supabase = None

    # Ventana: últimos 14 días
    now = datetime.now(timezone.utc)
    try:
        rows = (
            supabase.table("items")
            .select("title, created_at")
            .order("created_at", desc=True)
            .limit(500)
            .execute()
        )
        data = rows.data or []
    except Exception:
        data = []

    def topic_of(title: str) -> str:
        parts = [p for p in title.strip().split() if p]
        return " ".join(parts[:2]) if parts else "General"

    buckets_cur: Dict[str, int] = {}
    buckets_prev: Dict[str, int] = {}

    for r in data:
        title = (r.get("title") or "").strip()
        created_at = r.get("created_at")
        try:
            dt = (
                datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if isinstance(created_at, str)
                else now
            )
        except Exception:
            dt = now
        topic = topic_of(title)
        days_diff = (now - dt).days
        if days_diff <= 7:
            buckets_cur[topic] = buckets_cur.get(topic, 0) + 1
        elif days_diff <= 14:
            buckets_prev[topic] = buckets_prev.get(topic, 0) + 1

    items: List[TrendItem] = []
    all_topics = set(buckets_cur) | set(buckets_prev)
    for t in all_topics:
        cur = buckets_cur.get(t, 0)
        prev = buckets_prev.get(t, 0)
        momentum = float(cur / max(1, prev)) if cur else 0.0
        items.append(TrendItem(topic=t, momentum=round(momentum, 2)))

    # Ordena por momentum descendente y limita
    items.sort(key=lambda x: x.momentum, reverse=True)
    return items[: max(1, limit)]


@router.post("/auto_generate", response_model=AutoGenerateResponse)
def auto_generate(payload: AutoGenerateRequest) -> AutoGenerateResponse:
    """Orquesta recomendación + generación y persiste el item en `items`.

    - Usa `next_post` para obtener topic/horario sugerido.
    - Genera contenido con `generator.generate_post`.
    - Inserta un item en Supabase con source="scheduler".
    """
    # 1) Recomendación
    scheduled = next_post(account=payload.account)

    # 2) Generación
    gen_req = GeneratorRequest(
        topic=scheduled.topic,
        brand_voice=payload.brand_voice,
        keywords=payload.keywords,
        length=payload.length,
    )
    content = generate_post(gen_req)

    # 3) Persistencia (best-effort)
    item_id: Optional[str] = None
    try:
        supabase = get_client()
        resp = (
            supabase.table("items")
            .insert(
                {
                    "source": "scheduler",
                    "title": scheduled.topic,
                    "url": None,
                    "summary": content.text,
                }
            )
            .execute()
        )
        if resp.data:
            _id = resp.data[0].get("id")
            # Coerce a string para soportar BIGINT o UUID sin validar tipo
            if _id is not None:
                item_id = str(_id)
    except Exception:
        item_id = None

    return AutoGenerateResponse(scheduled=scheduled, content=content, item_id=item_id)


@router.post("/run_daily", response_model=RunDailyResponse)
def run_daily(payload: RunDailyRequest) -> RunDailyResponse:
    """Ejecuta auto_generate para una lista de cuentas y devuelve resultados.

    Persiste cada item (best-effort) mediante el proceso interno de auto_generate.
    """
    results: List[AutoGenerateResponse] = []
    for acc in payload.accounts:
        ag = auto_generate(
            AutoGenerateRequest(
                account=acc,
                brand_voice=payload.brand_voice,
                keywords=payload.keywords,
                length=payload.length,
            )
        )
        results.append(ag)
    return RunDailyResponse(results=results)


@router.get("/weights", response_model=WeightsResponse)
def get_weights(account: str) -> WeightsResponse:
    """Devuelve los pesos actuales del modelo por cuenta.

    Usa `scheduler_model_params`. Si no existen registros, devuelve defaults
    (0.6/0.4) y un mensaje informativo. En caso de error de conexión/tabla,
    retorna un objeto con `error` y defaults seguros.
    """
    try:
        supabase = get_client()
    except Exception:
        return WeightsResponse(
            account=account,
            w_engagement=0.6,
            w_relevance=0.4,
            learning_rate=0.05,
            updated_at=None,
            message="Error conectando a Supabase",
            error="supabase_unavailable",
        )

    try:
        res = (
            supabase.table("scheduler_model_params")
            .select("account,w_engagement,w_relevance,learning_rate,updated_at")
            .eq("account", account)
            .limit(1)
            .execute()
        )
        row = (res.data or [None])[0]
        if not row:
            return WeightsResponse(
                account=account,
                w_engagement=0.6,
                w_relevance=0.4,
                learning_rate=0.05,
                updated_at=None,
                message="No se encontraron parámetros; se usan defaults 0.6/0.4.",
            )
        return WeightsResponse(
            account=account,
            w_engagement=float(row.get("w_engagement", 0.6)),
            w_relevance=float(row.get("w_relevance", 0.4)),
            learning_rate=float(row.get("learning_rate", 0.05)),
            updated_at=str(row.get("updated_at")) if row.get("updated_at") is not None else None,
        )
    except Exception as e:
        return WeightsResponse(
            account=account,
            w_engagement=0.6,
            w_relevance=0.4,
            learning_rate=0.05,
            updated_at=None,
            message=f"Error consultando parámetros: {e}",
            error="query_failed",
        )


@router.post("/weights/update", response_model=WeightsUpdateResponse)
def update_weights(
    payload: WeightsUpdatePayload,
    x_admin_token: str = Header(..., alias="X-Admin-Token"),
) -> WeightsUpdateResponse:
    """Actualiza manualmente pesos del scheduler con auditoría.

    Seguridad basada en `X-Admin-Token` (comparado con ADMIN_TOKEN del entorno).
    Aplica validaciones estrictas de rangos y normalización tolerada.
    Registra un evento en `scheduler_model_audit` (best-effort).
    """
    admin_token = os.getenv("ADMIN_TOKEN")
    if not admin_token or x_admin_token != admin_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    w_e = float(payload.w_engagement)
    w_r = float(payload.w_relevance)
    lr = float(payload.learning_rate)

    # Validaciones
    if not (0.0 <= w_e <= 1.0) or not (0.0 <= w_r <= 1.0):
        raise HTTPException(status_code=422, detail="Weights must be within [0,1]")
    if not (0.001 <= lr <= 0.1):
        raise HTTPException(status_code=422, detail="learning_rate must be within [0.001, 0.1]")
    if abs((w_e + w_r) - 1.0) > 0.05:
        raise HTTPException(status_code=422, detail="w_engagement + w_relevance must be ~1 ± 0.05")

    try:
        supabase = get_client()
    except Exception:
        raise HTTPException(status_code=503, detail="Supabase unavailable")

    # Pesos previos
    prev_w_e, prev_w_r, prev_lr = _get_model_params(supabase, payload.account)

    # Upsert de nuevos pesos
    _update_model_params(supabase, payload.account, w_e, w_r, lr)

    # Auditoría (best-effort)
    try:
        supabase.table("scheduler_model_audit").insert(
            {
                "account": payload.account,
                "prev_w_engagement": prev_w_e,
                "prev_w_relevance": prev_w_r,
                "new_w_engagement": w_e,
                "new_w_relevance": w_r,
                "learning_rate": lr,
                "updated_by": "admin",
                "source": "manual",
            }
        ).execute()
    except Exception as e:
        print("[scheduler.audit] warning:", e)

    return WeightsUpdateResponse(
        account=payload.account,
        status="updated",
        new_weights={"w_engagement": w_e, "w_relevance": w_r, "learning_rate": lr},
    )
