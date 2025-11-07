-- WAV Automata: posts_feedback schema (engagement tracking)

create table if not exists public.posts_feedback (
  id bigserial primary key,
  account text not null,
  post_id text not null,
  content_type text,
  likes integer default 0,
  comments integer default 0,
  saves integer default 0,
  reach integer default 0,
  followers integer,
  engagement_score double precision,
  posted_at timestamptz default now()
);

create index if not exists posts_feedback_account_idx on public.posts_feedback(account);
create index if not exists posts_feedback_posted_at_idx on public.posts_feedback(posted_at desc);
