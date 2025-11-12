# 🚀 Próximos Pasos: Conectar Supabase

## El Problema (Actual)
El error `"Error conectando a Supabase"` ocurre porque **no hay credenciales de Supabase configuradas**.

✅ **Buena noticia:** El código está correcto y tiene fallbacks seguros. Los endpoints sin DB funcionan perfectamente.  
⚠️ **Para funcionalidad completa:** Necesitas configurar Supabase.

---

## 📋 Checklist Rápido

- [ ] Crear proyecto en https://supabase.com/dashboard
- [ ] Copiar `SUPABASE_URL` y `SUPABASE_KEY` de Settings → API
- [ ] Crear archivo `.env` en `/Users/fede/wav_automata/`
- [ ] Completar `.env` con tus credenciales
- [ ] Ejecutar tablas SQL desde `src/sql/` (opcional pero recomendado)
- [ ] Reiniciar servidor y verificar

---

## 🎯 Tu Acción Inmediata (3 min)

### Paso 1: Crear `.env`
```bash
cd /Users/fede/wav_automata
cp .env.example .env
```

### Paso 2: Abrir y completar
```bash
# En VS Code
code .env

# O en nano
nano .env
```

Cambia estas líneas con TUS valores de Supabase:
```env
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_KEY=YOUR-ACTUAL-API-KEY
```

### Paso 3: Guardar y reiniciar servidor
```bash
# Mata el servidor anterior
pkill -f uvicorn

# Reinicia
cd /Users/fede/wav_automata
source .venv/bin/activate
make run
```

### Paso 4: Verificar conexión
En otra terminal:
```bash
curl "http://127.0.0.1:8000/scheduler/weights?account=vibecodinglatam" | python3 -m json.tool
```

Si ves `"error": null` → **¡Conectado! 🎉**

---

## 📚 Documentación Detallada

- **SUPABASE_SETUP.md** → Guía paso a paso completa (incluyendo cómo obtener credenciales)
- **verify_supabase.py** → Script para validar configuración

Úsalos si necesitas detalles o debugging.

---

## 🎬 Quick Start (Copy-Paste)

```bash
# 1. Ir al proyecto
cd /Users/fede/wav_automata

# 2. Crear .env
cp .env.example .env

# 3. Editar (pon tus valores de Supabase)
# Abre .env en VS Code y completa SUPABASE_URL y SUPABASE_KEY

# 4. Reiniciar servidor
pkill -f uvicorn
source .venv/bin/activate
make run

# 5. En otra terminal, verificar
curl "http://127.0.0.1:8000/scheduler/weights?account=vibecodinglatam" | jq '.error'
# Si ves: null → ✅ Conectado
# Si ves: "supabase_unavailable" → ❌ Revisar .env
```

---

## ⚠️ Importante: Seguridad

- **NUNCA commitees `.env`** (ya está en `.gitignore`)
- Usa API Key "anon" para desarrollo local (menos privilegios)
- Para GitHub Actions, agrega SUPABASE_URL y SUPABASE_KEY en Secrets

---

## 🤔 ¿Necesitas Ayuda?

1. **Lee SUPABASE_SETUP.md** → Instrucciones paso a paso detalladas
2. **Ejecuta verify_supabase.py** → Detecta qué está mal
3. **Consulta la sección Troubleshooting** en SUPABASE_SETUP.md

---

**Status:** Estructura limpia ✅ | Tests pasando ✅ | API funcionando ✅ | Supabase: Configuración pendiente ⏳

Haz los pasos arriba y todo estará 100% operacional.
