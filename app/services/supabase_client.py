from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client

_client: Optional[Client] = None


def get_client() -> Client:
    """Singleton del cliente de Supabase, inicializado con variables de entorno.

    Requiere SUPABASE_URL y SUPABASE_KEY en el entorno.
    """
    global _client
    if _client is not None:
        return _client

    # Asegura carga de .env si es ejecución local
    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL o SUPABASE_KEY no configurados en el entorno")

    try:
        _client = create_client(url, key)
        return _client
    except Exception as e:
        raise RuntimeError(f"No se pudo inicializar el cliente de Supabase: {e}")
