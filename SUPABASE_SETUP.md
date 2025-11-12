# 🔧 Guía de Configuración: Conectar Supabase a WAV Automata

## Problema Actual
El error `"Error conectando a Supabase"` aparece porque **no hay variables de entorno configuradas** (`SUPABASE_URL` y `SUPABASE_KEY`). El código está bien y tiene fallbacks seguros, pero para funcionalidad completa necesitas credenciales.

---

## ✅ Paso 1: Crear/Verificar Proyecto Supabase

1. Ve a https://supabase.com/dashboard (inicia sesión o regístrate)
2. Haz clic en **New Project** (o usa uno existente)
3. Completa:
   - **Name:** wav-automata (o similar)
   - **Password:** genera una contraseña segura
   - **Region:** elige la más cercana (ej. América → us-east-1)
4. Haz clic en **Create new project** y espera (2-3 min)

---

## 📋 Paso 2: Obtener Credenciales

Una vez creado el proyecto, ve a **Settings → API** en el panel izquierdo:

### SUPABASE_URL
- Copiar la URL bajo "Project URL"
- Parece: `https://abc123def456.supabase.co`

### SUPABASE_KEY
- **Opción A (Recomendada para desarrollo local):** Usa la clave **`anon`** (API Key)
  - Menos privilegios, buena para desarrollo
  - Mostrada en la sección "Project API Keys"
- **Opción B (Para API server):** Usa la clave **`service_role`** (Service Role Key)
  - Más privilegios (acceso completo a BD)
  - Requiere más cuidado, nunca exponerla públicamente

Para desarrollo local, usa **anon**. Para producción server-side, usa **service_role**.

---

## 🗄️ Paso 3: Crear Tablas SQL (Opcional pero recomendado)

Si quieres que la persistencia de datos funcione, ejecuta los scripts en Supabase SQL Editor:

### 3a) Abre SQL Editor
En Supabase Dashboard → **SQL Editor** (panel izquierdo)

### 3b) Copia y ejecuta el esquema
Archivo: `/Users/fede/wav_automata/src/sql/`

Ejecuta en orden:
1. **schema_pgvector.sql** → Crea tabla `items` + vector search
2. **schema_posts_feedback.sql** → Crea tabla `posts_feedback`
3. **scheduler_model_params.sql** → Crea tabla `scheduler_model_params`
4. **scheduler_model_audit.sql** → Crea tabla `scheduler_model_audit`

Después de ejecutar, verás las tablas en **Database → Tables** en el panel izquierdo.

---

## 🔑 Paso 4: Configurar `.env` Local

1. Copia el archivo `.env.example` como `.env`:
   ```bash
   cp .env.example .env
   ```

2. Abre `.env` y rellena tus valores:
   ```bash
   nano .env
   # o usa VS Code
   code .env
   ```

3. Completa al menos estas líneas:
   ```env
   SUPABASE_URL=https://abc123def456.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

4. Guarda (Ctrl+O en nano, Cmd+S en VS Code)

---

## 🚀 Paso 5: Verificar Conexión

### Detener servidor anterior (si está corriendo)
```bash
pkill -f uvicorn
sleep 1
```

### Reiniciar con new .env
```bash
cd /Users/fede/wav_automata
source .venv/bin/activate
uvicorn app.main:app --reload
```

### Prueba el endpoint /scheduler/weights
En otra terminal:
```bash
curl -s "http://127.0.0.1:8000/scheduler/weights?account=vibecodinglatam" | python3 -m json.tool
```

**Resultado esperado (con Supabase conectado):**
```json
{
    "account": "vibecodinglatam",
    "w_engagement": 0.6,
    "w_relevance": 0.4,
    "learning_rate": 0.05,
    "updated_at": null,
    "message": null,
    "error": null
}
```

**Si ves error=null y message=null → ¡Conectado exitosamente!** 🎉

---

## 🛡️ Seguridad: No Commitees `.env`

Tu `.gitignore` ya incluye `.env`, así que está protegido:
```bash
git status
# No verá `.env` listado
```

Para GitHub Actions (CI/CD), ve a **Settings → Secrets and variables → Actions** en tu repo y agrega:
- `SUPABASE_URL`
- `SUPABASE_KEY`

---

## 🐛 Troubleshooting

### Error: "SUPABASE_URL o SUPABASE_KEY no configurados"
- ✅ Verifica que `.env` existe en `/Users/fede/wav_automata/`
- ✅ Verifica valores no estén vacíos: `grep SUPABASE .env`
- ✅ Reinicia el servidor: `pkill -f uvicorn && make run`

### Error: "Error conectando a Supabase" pero .env existe
- ✅ Verifica que SUPABASE_URL no tiene espacios: `curl "$SUPABASE_URL"` debe funcionar
- ✅ Verifica que SUPABASE_KEY es válido (largo, contiene puntos si es JWT)
- ✅ Prueba conectando desde Python:
  ```bash
  source .venv/bin/activate
  python3 -c "from app.services.supabase_client import get_client; print(get_client())"
  ```

### Tablas no existen
- ✅ Ve a Supabase SQL Editor
- ✅ Ejecuta los scripts en `src/sql/`
- ✅ Verifica en Database → Tables

---

## 📊 Endpoints Afectados por Supabase

| Endpoint | Requerimiento | Con Supabase | Sin Supabase |
|----------|---|---|---|
| `/health` | No | ✅ | ✅ |
| `/generator/post` | No | ✅ | ✅ |
| `/semantic/score` | No | ✅ | ✅ |
| `/scheduler/next_post` | Parcial | 📈 Mejor | Heurísticas básicas |
| `/scheduler/weights` | Sí | ✅ Pesos guardados | 0.6/0.4 defaults |
| `/scheduler/feedback` | Sí | 📊 Guardado | Solo calcula score |
| `/scheduler/trends` | Sí | 📈 Datos históricos | Array vacío |
| `/scheduler/auto_generate` | Parcial | ✅ Completo | Funciona sin BD |
| `/scheduler/run_daily` | Parcial | ✅ Completo | Funciona sin BD |

---

## 🎯 Resumen Rápido

```bash
# 1. Copiar .env desde ejemplo
cp .env.example .env

# 2. Editar con tus credenciales Supabase
nano .env

# 3. Guardar y reiniciar servidor
pkill -f uvicorn
source .venv/bin/activate
make run

# 4. Probar
curl "http://127.0.0.1:8000/scheduler/weights?account=vibecodinglatam" | jq
```

**Si ves `"error": null` → ¡Todo funciona! 🎉**

---

**Fecha:** 11 Nov 2025  
**Estado:** Guía completa para conectar Supabase
