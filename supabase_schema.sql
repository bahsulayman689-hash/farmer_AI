-- FarmAI: run this once in Supabase -> SQL Editor.
-- Every table is locked to its owner with row-level security, so farmers only ever see their own data.

create table if not exists public.plots (
  id         bigint generated always as identity primary key,
  user_id    uuid not null default auth.uid() references auth.users(id) on delete cascade,
  crop       text not null,
  area       numeric not null check (area > 0),
  soil       text,
  planted    date not null,
  created_at timestamptz not null default now()
);

create table if not exists public.task_done (
  plot_id bigint not null references public.plots(id) on delete cascade,
  idx     int    not null,
  user_id uuid   not null default auth.uid() references auth.users(id) on delete cascade,
  primary key (plot_id, idx)
);

create table if not exists public.ledger (
  id         bigint generated always as identity primary key,
  user_id    uuid not null default auth.uid() references auth.users(id) on delete cascade,
  d          date not null,
  kind       text not null check (kind in ('cost', 'sale')),
  crop       text,
  cat        text,
  amount     numeric not null check (amount >= 0),
  note       text not null default '',
  created_at timestamptz not null default now()
);

create table if not exists public.history (
  id      bigint generated always as identity primary key,
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  ts      text not null,
  kind    text not null,
  summary text not null
);

create index if not exists plots_user_idx    on public.plots(user_id);
create index if not exists task_done_user_idx on public.task_done(user_id);
create index if not exists ledger_user_idx   on public.ledger(user_id, d desc);
create index if not exists history_user_idx  on public.history(user_id, id desc);

alter table public.plots     enable row level security;
alter table public.task_done enable row level security;
alter table public.ledger    enable row level security;
alter table public.history   enable row level security;

drop policy if exists "own rows" on public.plots;
drop policy if exists "own rows" on public.task_done;
drop policy if exists "own rows" on public.ledger;
drop policy if exists "own rows" on public.history;

create policy "own rows" on public.plots     for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "own rows" on public.task_done for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "own rows" on public.ledger    for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "own rows" on public.history   for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());