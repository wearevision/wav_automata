from __future__ import annotations

import os
import math
import hashlib
from typing import List

from dotenv import load_dotenv

load_dotenv()

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_DIMENSIONS = 1536


def _pseudo_embedding(text: str, dimensions: int = DEFAULT_DIMENSIONS) -> List[float]:
    """Genera un embedding determinístico pseudoaleatorio cuando no hay proveedor.

    Útil para desarrollo offline. No representa semántica real.
    """
    # Usa SHA256 en bloques para generar floats en [-1, 1]
    vec: List[float] = []
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    counter = 0
    while len(vec) < dimensions:
        h = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        # Convierte 8 bytes en un float
        for i in range(0, len(h), 8):
            chunk = h[i : i + 8]
            if len(chunk) < 8:
                break
            n = int.from_bytes(chunk, "big", signed=False)
            # Normaliza a rango [-1, 1]
            f = (n / (2**64 - 1)) * 2 - 1
            vec.append(float(f))
            if len(vec) >= dimensions:
                break
        counter += 1
    # Normaliza vector a norma 1 para estabilidad
    s = sum(abs(x) for x in vec) or 1.0
    return [x / s for x in vec]


def get_embedding(text: str, model: str = DEFAULT_EMBEDDING_MODEL) -> List[float]:
    """Obtiene un embedding con OpenAI si hay API key, o uno pseudo si no.

    Devuelve un vector de tamaño 'DEFAULT_DIMENSIONS' por defecto.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _pseudo_embedding(text, DEFAULT_DIMENSIONS)

    try:
        # Import local para no requerir paquete si no se usa
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        resp = client.embeddings.create(model=model, input=text)
        return list(resp.data[0].embedding)
    except Exception:
        # Fallback robusto en caso de error de red o modelo
        return _pseudo_embedding(text, DEFAULT_DIMENSIONS)
