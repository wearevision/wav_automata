#!/usr/bin/env python3
"""
Validador de configuración de Supabase para WAV Automata.

Uso:
    python3 verify_supabase.py

Verifica:
1. Archivo .env existe y tiene variables requeridas
2. Variables de entorno están cargadas
3. Cliente Supabase se puede inicializar
4. Conexión a Supabase funciona
5. Tablas requeridas existen
"""

import os
import sys
from pathlib import Path

def check_env_file() -> bool:
    """Verifica que .env existe en la raíz del proyecto."""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Archivo .env no encontrado")
        print("   Solución: cp .env.example .env")
        return False
    print("✅ Archivo .env encontrado")
    return True


def check_env_vars() -> bool:
    """Verifica que variables de entorno requeridas están configuradas."""
    from dotenv import load_dotenv
    load_dotenv()
    
    required = ["SUPABASE_URL", "SUPABASE_KEY"]
    missing = []
    
    for var in required:
        value = os.getenv(var, "").strip()
        if not value:
            missing.append(var)
            print(f"❌ {var} no configurada o vacía")
        else:
            # Mostrar parcialmente por seguridad
            masked = value[:10] + "..." + value[-4:] if len(value) > 20 else "*" * len(value)
            print(f"✅ {var} configurada: {masked}")
    
    return len(missing) == 0


def check_client_init() -> bool:
    """Verifica que el cliente de Supabase se puede inicializar."""
    try:
        from app.services.supabase_client import get_client
        client = get_client()
        print("✅ Cliente Supabase inicializado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al inicializar cliente: {e}")
        return False


def check_connection() -> bool:
    """Verifica que hay conexión funcional a Supabase."""
    try:
        from app.services.supabase_client import get_client
        client = get_client()
        # Intenta una query simple para verificar conexión
        response = client.table("scheduler_model_params").select("count", count="exact").limit(1).execute()
        print(f"✅ Conexión a Supabase verificada")
        return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("   Verifica que SUPABASE_URL y SUPABASE_KEY son correctos")
        return False


def check_tables() -> bool:
    """Verifica que las tablas requeridas existen."""
    try:
        from app.services.supabase_client import get_client
        client = get_client()
        
        required_tables = [
            "scheduler_model_params",
            "posts_feedback",
            "items",
            "scheduler_model_audit"
        ]
        
        missing_tables = []
        for table in required_tables:
            try:
                client.table(table).select("count", count="exact").limit(1).execute()
                print(f"✅ Tabla '{table}' existe")
            except Exception:
                missing_tables.append(table)
                print(f"⚠️  Tabla '{table}' no encontrada")
        
        if missing_tables:
            print(f"\n   Tablas faltantes: {', '.join(missing_tables)}")
            print("   Solución: Ejecuta scripts en src/sql/ en Supabase SQL Editor")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error al verificar tablas: {e}")
        return False


def main():
    """Ejecuta todas las verificaciones."""
    print("=" * 60)
    print("🔧 Validador de Configuración - WAV Automata + Supabase")
    print("=" * 60)
    print()
    
    checks = [
        ("Archivo .env existe", check_env_file),
        ("Variables de entorno", check_env_vars),
        ("Cliente Supabase", check_client_init),
        ("Conexión a Supabase", check_connection),
        ("Tablas requeridas", check_tables),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n🔍 Verificando: {name}")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            results.append((name, False))
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} verificaciones pasadas")
    
    if passed == total:
        print("\n🎉 ¡Configuración lista! Supabase está conectado correctamente.")
        print("\nPuedes empezar a usar los endpoints:")
        print("  curl http://127.0.0.1:8000/health")
        return 0
    else:
        print("\n⚠️  Hay problemas de configuración. Ver detalles arriba.")
        print("\nPasos de solución:")
        print("1. Verifica .env existe: ls -la .env")
        print("2. Verifica variables: grep SUPABASE .env")
        print("3. Reinicia el servidor: make run")
        print("4. Lee SUPABASE_SETUP.md para más detalles")
        return 1


if __name__ == "__main__":
    sys.exit(main())
