-- WAV Automata schema (Postgres + pgvector)
-- Ejecuta esto en el SQL Editor de Supabase o tu instancia Postgres.

-- 1) Extensiones necesarias
create extension if not exists vector;

-- 2) Tabla de items base
create table if not exists public.items (
  id bigserial primary key,
  source text,
  title text not null,
  url text,
  summary text,
  created_at timestamptz default now()
);

-- 3) Embeddings por item
-- Ajusta el tamaño del vector si usas otro modelo (ej: 1536 para text-embedding-3-small)
create table if not exists public.item_embeddings (
  item_id bigint not null references public.items(id) on delete cascade,
  embedding vector(1536) not null,
  model text not null,
  created_at timestamptz default now()
);

-- 4) Índices para vector search (IVFFLAT requiere configurar lists apropiadamente)
-- Nota: IVFFLAT performa mejor con 'lists' proporcional al nº de filas (ej: ~sqrt(n)).
create index if not exists item_embeddings_embedding_ivfflat
  on public.item_embeddings using ivfflat (embedding vector_cosine_ops);

-- 5) (Opcional) RLS y políticas
-- Habilita RLS si expones tablas mediante claves 'anon'; usa Service Role para backend.
-- alter table public.items enable row level security;
-- alter table public.item_embeddings enable row level security;
-- create policy "read_items" on public.items for select using (true);
-- create policy "read_item_embeddings" on public.item_embeddings for select using (true);
