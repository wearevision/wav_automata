# WAV Automata 🧠

**La inteligencia viva detrás de la comunicación coherente.**

WAV Automata es el backend operativo del ecosistema WAV Automata
Orquesta procesos de análisis emántico, detección de tendencias y generación de contenidos
autónomos conectados con los principios de EQI (Calidad Emocional), REI (Equidad Relacional)
y ROI (Retorno de Inversión).

---

### 🧠 Arquitectura

- **FastAPI + Python 3.11** → capa de orquestación e inferencia  
- **Supabase (Postgres + pgvector)** → persistencia y análisis semántico  
- **OpenAI / Gemini** → embeddings y generación contextual  
- **n8n / Make** → automatización de flujos y publicación  
- **Railway / Cloud Run** → despliegue cloud persistente

---

### 🧩 Endpoints iniciales

| Endpoint | Descripción |
|-----------|--------------|
| `/health` | Estado del sistema |
| `/semantic/embed_item` | Genera embeddings y metadatos |
| `/semantic/score` | Calcula relevancia, momentum y ROI predictivo |
| `/generator/post` | Genera copy, hashtags y prompt visual coherente |

---

### 🌱 Entorno local

```bash
uvicorn app.main:app --reload
```

La API estará disponible en [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

### 🔐 Variables `.env`

Usa un archivo `.env` local (no commiteado) o un gestor de secretos. Copia desde `.env.example` y completa tus valores:

```env
OPENAI_API_KEY=<tu_api_key_opcional>
SUPABASE_URL=https://<tu-proyecto>.supabase.co
SUPABASE_KEY=<tu_service_role_o_anon_key>
PROJECT_NAME=WAV_Automata
```

> ⚠️ No compartas claves reales en documentación ni repos públicos. Revoca cualquier clave previamente expuesta y genera una nueva.
