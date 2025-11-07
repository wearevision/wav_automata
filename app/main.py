from fastapi import FastAPI
from dotenv import load_dotenv
import os

from .models.schemas import ItemInput
from .services.supabase_client import get_client
from .routers import semantic, generator

# 🔹 Carga variables del archivo .env
load_dotenv()

# 🔹 Instancia de la app FastAPI
app = FastAPI(
    title="WAV Automata",
    version="0.1.0",
    description="Backend neurocoherente para detección, análisis y generación de contenido inteligente."
)

# 🔹 Registro de routers por dominio
app.include_router(semantic.router)
app.include_router(generator.router)


# 🩺 Endpoint de salud (verifica que la API esté viva)
@app.get("/health")
def health():
    return {"status": "ok", "project": "WAV Automata"}


# 🧩 Endpoint de prueba de conexión a Supabase
@app.get("/check_supabase")
def check_supabase():
    """
    Verifica que Supabase esté accesible desde FastAPI.
    Retorna el nombre del proyecto y conexión exitosa si todo está bien.
    """
    try:
        supabase = get_client()
    except Exception as e:
        return {"supabase_connection": "failed", "detail": str(e)}
    try:
        response = supabase.table("items").select("*").limit(1).execute()
        return {
            "supabase_connection": "ok",
            "rows_sample": len(response.data),
            "project": os.getenv("PROJECT_NAME")
        }
    except Exception as e:
        return {"supabase_connection": "error", "detail": str(e)}


# 🧱 Endpoint raíz (opcional, landing técnica)
@app.get("/")
def root():
    return {
        "message": "Bienvenido a WAV Automata — API Neurocoherente",
        "docs": "/docs",
        "status": "active"
    }

# 🚀 Endpoint para insertar nuevos items
@app.post("/insert_item")
def insert_item(item: ItemInput):
    """
    Inserta un nuevo item en la tabla public.items
    desde cualquier fuente (RSS, IA o manual).
    """
    try:
        supabase = get_client()
        response = supabase.table("items").insert({
            "source": item.source,
            "title": item.title,
            "url": item.url,
            "summary": item.summary
        }).execute()

        return {
            "status": "ok",
            "inserted_id": response.data[0]["id"] if response.data else None,
            "rows_affected": len(response.data)
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}