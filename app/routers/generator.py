from __future__ import annotations

from fastapi import APIRouter

from ..models.schemas import GeneratorRequest, GeneratorResponse

router = APIRouter(prefix="/generator", tags=["generator"])


@router.post("/post", response_model=GeneratorResponse)
def generate_post(payload: GeneratorRequest) -> GeneratorResponse:
    """
    Genera un copy, hashtags y prompt visual coherente con la cuenta o marca indicada.
    Puede ser usado por el agente para generar contenido diario automatizado.
    """
    topic = payload.topic.strip()
    voice = (payload.brand_voice or "").strip()
    kws = payload.keywords or []
    account = getattr(payload, "account", "").lower()
    length = max(80, min(400, payload.length or 150))

    # Estilos base por cuenta
    styles = {
        "wavwearevision": "tono institucional, reflexivo y estratégico",
        "vibecodinglatam": "tono innovador, optimista y tecnológico",
        "consdelrosario": "tono empático, emocional y humano",
        "felguetaedwards": "tono inspirador, introspectivo y honesto",
    }
    style = styles.get(account, f"tono {voice}" if voice else "tono neutro y coherente")

    # Construcción del copy
    base = f"{topic} ({style})."
    detail = " " + ", ".join(kws) if kws else ""
    copy = (
        f"{base} {detail}"
        if len(base) + len(detail) <= length
        else (base + detail)[: length - 1] + "…"
    )

    # Hashtags adaptativos
    hashtags = [f"#{k.replace(' ', '').capitalize()}" for k in kws if k]
    if account == "vibecodinglatam":
        hashtags += ["#IA", "#Innovacion", "#Comunidad"]
    elif account == "wavwearevision":
        hashtags += ["#Liderazgo", "#Cultura", "#Proposito"]
    elif account == "consdelrosario":
        hashtags += ["#Psicologia", "#Autenticidad", "#Bienestar"]
    elif account == "felguetaedwards":
        hashtags += ["#MasculinidadConsciente", "#Reflexion", "#Propósito"]

    # Prompt visual
    visual_prompt = (
        f"Arte conceptual del tema '{topic}', estilo coherente con {account or 'la marca'}, "
        f"{style}, composición limpia, color balanceado, formato cuadrado 1:1."
    )

    return GeneratorResponse(text=copy.strip(), hashtags=hashtags[:8], visual_prompt=visual_prompt)
