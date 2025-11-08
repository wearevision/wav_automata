# WAV Automata 🧠
![CI](https://github.com/wearevision/wav_automata/actions/workflows/ci.yml/badge.svg?branch=main)

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

### 🧩 Endpoints

| Endpoint | Descripción |
|-----------|--------------|
| `/health` | Estado del sistema |
| `/semantic/embed_item` | Genera embeddings y metadatos |
| `/semantic/score` | Calcula relevancia, momentum y ROI predictivo |
| `/generator/post` | Genera copy, hashtags y prompt visual coherente |
| `/scheduler/next_post` | Recomendación de cuenta/hora/formato/tema |
| `/scheduler/feedback` | Guarda métricas reales del post (engagement) |
| `/scheduler/trends` | Momentum semanal por tema |
| `/scheduler/auto_generate` | Recomienda + genera contenido y guarda item |
| `/scheduler/run_daily` | Ejecuta auto_generate en lote por cuentas |

---

### 🌱 Entorno local

```bash
uvicorn app.main:app --reload
```

La API estará disponible en [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

### 📈 Esquema SQL

En `src/sql/` encontrarás:
- `schema_pgvector.sql` → tablas `items` y `item_embeddings` + índice IVFFLAT
- `schema_posts_feedback.sql` → tabla `posts_feedback` (engagement histórico)

Ejecuta ambos en el SQL Editor de Supabase.

---

### 🧪 Ejemplos rápidos (curl)

```bash
# Recomendación
curl -s http://127.0.0.1:8000/scheduler/next_post | jq

# Generar automáticamente y guardar item
curl -s -X POST http://127.0.0.1:8000/scheduler/auto_generate \
	-H 'Content-Type: application/json' \
	-d '{"account":"vibecodinglatam","brand_voice":"humano-visionario","keywords":["IA","creatividad"],"length":140}' | jq

# Lote diario
curl -s -X POST http://127.0.0.1:8000/scheduler/run_daily \
	-H 'Content-Type: application/json' \
	-d '{"accounts":["vibecodinglatam","vision"]}' | jq

# Feedback real del post
curl -s -X POST http://127.0.0.1:8000/scheduler/feedback \
	-H 'Content-Type: application/json' \
	-d '{"account":"vibecodinglatam","post_id":"abc123","likes":540,"comments":82,"saves":60,"reach":14000}' | jq

# Tendencias semanales
curl -s http://127.0.0.1:8000/scheduler/trends | jq
```

---

### 🔐 Seguridad y administración

Endpoints protegidos
- `POST /scheduler/weights/update` requiere header `X-Admin-Token` y valida rangos.

Ejemplos curl
```bash
# Consultar pesos actuales
curl -s "http://127.0.0.1:8000/scheduler/weights?account=vibecodinglatam" | jq

# Actualizar pesos (token en header)
curl -s -X POST http://127.0.0.1:8000/scheduler/weights/update \
	-H "Content-Type: application/json" \
	-H "X-Admin-Token: $ADMIN_TOKEN" \
	-d '{
				"account":"vibecodinglatam",
				"w_engagement":0.65,
				"w_relevance":0.35,
				"learning_rate":0.05
			}' | jq
```

Configurar token
- Local: agregar en `.env`
	- `ADMIN_TOKEN=<tu_token_secreto>`
- GitHub Actions (repo → Settings → Secrets and variables → Actions):
	- Nuevo secreto: `ADMIN_TOKEN` con el mismo valor

Buenas prácticas
- No commitear `.env` ni tokens.
- Rotar periódicamente el token y limitar su alcance.

---

### 🧰 Atajos con Makefile

```bash
make install   # instala dependencias
make run       # levanta API con reload
make test      # corre pytest
make fmt       # formatea con black
make lint      # ruff + black --check
make type      # mypy type-check
make hooks     # instala pre-commit hooks
make check     # lint + type + tests
```

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
