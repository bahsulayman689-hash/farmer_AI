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

-- ---------------------------------------------------------------------------
-- Reminders: one profile row per farmer (phone, channel, location, language).
-- ---------------------------------------------------------------------------
create table if not exists public.profiles (
  user_id    uuid primary key default auth.uid() references auth.users(id) on delete cascade,
  phone      text not null default '',
  channel    text not null default 'whatsapp' check (channel in ('whatsapp', 'sms')),
  location   text not null default 'Banjul',
  lang       text not null default 'English',
  reminders  boolean not null default false,
  last_sent  date,
  updated_at timestamptz not null default now()
);
alter table public.profiles enable row level security;
drop policy if exists "own rows" on public.profiles;
create policy "own rows" on public.profiles for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

-- ---------------------------------------------------------------------------
-- Cooperatives: farmers join with a code and choose to share their fields and disease scans.
-- The cooperative owner never reads the base tables. They only get the limited columns below,
-- and never phone numbers or ledger (money) data.
-- ---------------------------------------------------------------------------
alter table public.profiles add column if not exists name text not null default '';

create table if not exists public.cooperatives (
  id         bigint generated always as identity primary key,
  owner_id   uuid not null default auth.uid() references auth.users(id) on delete cascade,
  name       text not null check (length(trim(name)) > 0),
  join_code  text not null unique default upper(substr(md5(random()::text || clock_timestamp()::text), 1, 6)),
  created_at timestamptz not null default now()
);

create table if not exists public.coop_members (
  user_id    uuid primary key default auth.uid() references auth.users(id) on delete cascade,   -- one cooperative per farmer
  coop_id    bigint not null references public.cooperatives(id) on delete cascade,
  share_data boolean not null default true,
  joined_at  timestamptz not null default now()
);

alter table public.cooperatives enable row level security;
alter table public.coop_members enable row level security;
drop policy if exists "owner manages" on public.cooperatives;
drop policy if exists "member sees own row" on public.coop_members;
create policy "owner manages" on public.cooperatives for all to authenticated using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "member sees own row" on public.coop_members for select to authenticated using (user_id = auth.uid());
-- no insert/update/delete policies on coop_members: farmers use the functions below

-- Farmer side ----------------------------------------------------------------
create or replace function public.join_cooperative(p_code text) returns text
language plpgsql security definer set search_path = public as $$
declare c record;
begin
  if auth.uid() is null then raise exception 'Not signed in'; end if;
  select * into c from public.cooperatives where join_code = upper(trim(p_code));
  if not found then raise exception 'Invalid cooperative code'; end if;
  insert into public.coop_members(user_id, coop_id, share_data) values (auth.uid(), c.id, true)
    on conflict (user_id) do update set coop_id = excluded.coop_id, share_data = true, joined_at = now();
  return c.name;
end $$;

create or replace function public.my_cooperative() returns table(name text, share_data boolean)
language sql stable security definer set search_path = public as $$
  select c.name, m.share_data from public.coop_members m join public.cooperatives c on c.id = m.coop_id where m.user_id = auth.uid();
$$;

create or replace function public.set_coop_sharing(p_share boolean) returns void
language sql security definer set search_path = public as $$
  update public.coop_members set share_data = p_share where user_id = auth.uid();
$$;

create or replace function public.leave_cooperative() returns void
language sql security definer set search_path = public as $$
  delete from public.coop_members where user_id = auth.uid();
$$;

-- Owner side (each function checks that the caller owns the cooperative) --------
create or replace function public.coop_members_list() returns table(user_id uuid, name text, location text, joined_at timestamptz, last_active text)
language sql stable security definer set search_path = public as $$
  select m.user_id, coalesce(nullif(p.name, ''), 'Farmer ' || substr(m.user_id::text, 1, 4)), coalesce(p.location, ''), m.joined_at,
         (select max(h.ts) from public.history h where h.user_id = m.user_id)
  from public.coop_members m
  left join public.profiles p on p.user_id = m.user_id
  where m.share_data and m.coop_id in (select id from public.cooperatives where owner_id = auth.uid());
$$;

create or replace function public.coop_fields() returns table(user_id uuid, plot_id bigint, crop text, area numeric, planted date)
language sql stable security definer set search_path = public as $$
  select pl.user_id, pl.id, pl.crop, pl.area, pl.planted
  from public.plots pl join public.coop_members m on m.user_id = pl.user_id
  where m.share_data and m.coop_id in (select id from public.cooperatives where owner_id = auth.uid());
$$;

create or replace function public.coop_done() returns table(plot_id bigint, idx int)
language sql stable security definer set search_path = public as $$
  select t.plot_id, t.idx
  from public.task_done t join public.coop_members m on m.user_id = t.user_id
  where m.share_data and m.coop_id in (select id from public.cooperatives where owner_id = auth.uid());
$$;

create or replace function public.coop_scans(p_days int default 30) returns table(user_id uuid, ts text, summary text)
language sql stable security definer set search_path = public as $$
  select h.user_id, h.ts, h.summary
  from public.history h join public.coop_members m on m.user_id = h.user_id
  where h.kind = 'Disease' and m.share_data and m.coop_id in (select id from public.cooperatives where owner_id = auth.uid())
    and h.ts >= to_char(now() - make_interval(days => p_days), 'YYYY-MM-DD')
  order by h.ts desc limit 500;
$$;

create or replace function public.coop_remove_member(p_user uuid) returns void
language sql security definer set search_path = public as $$
  delete from public.coop_members where user_id = p_user and coop_id in (select id from public.cooperatives where owner_id = auth.uid());
$$;

create or replace function public.coop_new_code(p_coop bigint) returns text
language sql security definer set search_path = public as $$
  update public.cooperatives set join_code = upper(substr(md5(random()::text || clock_timestamp()::text), 1, 6))
  where id = p_coop and owner_id = auth.uid() returning join_code;
$$;

-- Only signed-in users may call these
revoke all on function public.join_cooperative(text), public.my_cooperative(), public.set_coop_sharing(boolean), public.leave_cooperative(),
  public.coop_members_list(), public.coop_fields(), public.coop_done(), public.coop_scans(int), public.coop_remove_member(uuid), public.coop_new_code(bigint) from public;
grant execute on function public.join_cooperative(text), public.my_cooperative(), public.set_coop_sharing(boolean), public.leave_cooperative(),
  public.coop_members_list(), public.coop_fields(), public.coop_done(), public.coop_scans(int), public.coop_remove_member(uuid), public.coop_new_code(bigint) to authenticated;

-- ---------------------------------------------------------------------------
-- First-run setup (profile fields) and in-app feedback.
-- ---------------------------------------------------------------------------
alter table public.profiles add column if not exists crops text not null default '';
alter table public.profiles add column if not exists onboarded boolean not null default false;

create table if not exists public.feedback (
  id         bigint generated always as identity primary key,
  user_id    uuid not null default auth.uid() references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  from_page  text not null default '',
  category   text not null default '',
  rating     int check (rating between 1 and 5),
  message    text not null default '' check (length(message) <= 2000)
);
alter table public.feedback enable row level security;
drop policy if exists "own rows" on public.feedback;
create policy "own rows" on public.feedback for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

-- To read feedback yourself (Supabase -> SQL Editor):
--   select f.created_at, p.name, p.location, f.from_page, f.category, f.rating, f.message
--   from public.feedback f left join public.profiles p using (user_id) order by f.created_at desc;

-- ---------------------------------------------------------------------------
-- Cooperative alerts: the owner warns all members. Members read them in the app,
-- and the daily reminder job adds new ones to the next morning message.
-- Members receive alerts even when they have switched data sharing off.
-- ---------------------------------------------------------------------------
alter table public.profiles add column if not exists last_sent_at timestamptz;

create table if not exists public.coop_alerts (
  id         bigint generated always as identity primary key,
  coop_id    bigint not null references public.cooperatives(id) on delete cascade,
  created_at timestamptz not null default now(),
  title      text not null check (length(trim(title)) between 1 and 80),
  body       text not null check (length(trim(body)) between 1 and 600),
  severity   text not null default 'info' check (severity in ('info', 'warning', 'urgent'))
);
create index if not exists coop_alerts_coop_idx on public.coop_alerts(coop_id, created_at desc);

create table if not exists public.alert_reads (
  user_id  uuid   not null default auth.uid() references auth.users(id) on delete cascade,
  alert_id bigint not null references public.coop_alerts(id) on delete cascade,
  read_at  timestamptz not null default now(),
  primary key (user_id, alert_id)
);

alter table public.coop_alerts enable row level security;
alter table public.alert_reads enable row level security;
drop policy if exists "owner manages alerts" on public.coop_alerts;
drop policy if exists "own reads" on public.alert_reads;
create policy "owner manages alerts" on public.coop_alerts for all to authenticated
  using (coop_id in (select id from public.cooperatives where owner_id = auth.uid()))
  with check (coop_id in (select id from public.cooperatives where owner_id = auth.uid()));
create policy "own reads" on public.alert_reads for select to authenticated using (user_id = auth.uid());
-- members never read coop_alerts directly; they use my_alerts() below

create or replace function public.send_coop_alert(p_title text, p_body text, p_severity text default 'info') returns int
language plpgsql security definer set search_path = public as $$
declare cid bigint; n int;
begin
  select id into cid from public.cooperatives where owner_id = auth.uid() order by id limit 1;
  if cid is null then raise exception 'You do not run a cooperative'; end if;
  if (select count(*) from public.coop_alerts where coop_id = cid and created_at > now() - interval '24 hours') >= 10 then
    raise exception 'Daily alert limit reached (10 per day)';
  end if;
  insert into public.coop_alerts(coop_id, title, body, severity) values (cid, trim(p_title), trim(p_body), coalesce(p_severity, 'info'));
  select count(*) into n from public.coop_members where coop_id = cid;
  return n;
end $$;

create or replace function public.coop_reach() returns int
language sql stable security definer set search_path = public as $$
  select count(*)::int from public.coop_members where coop_id in (select id from public.cooperatives where owner_id = auth.uid());
$$;

create or replace function public.coop_sent_alerts() returns table(id bigint, created_at timestamptz, title text, body text, severity text, reads bigint, members bigint)
language sql stable security definer set search_path = public as $$
  select a.id, a.created_at, a.title, a.body, a.severity,
         (select count(*) from public.alert_reads r where r.alert_id = a.id),
         (select count(*) from public.coop_members m where m.coop_id = a.coop_id and m.joined_at <= a.created_at)
  from public.coop_alerts a
  where a.coop_id in (select id from public.cooperatives where owner_id = auth.uid())
  order by a.created_at desc limit 20;
$$;

create or replace function public.my_alerts(p_days int default 30) returns table(id bigint, created_at timestamptz, title text, body text, severity text, coop_name text, is_read boolean)
language sql stable security definer set search_path = public as $$
  select a.id, a.created_at, a.title, a.body, a.severity, c.name,
         exists (select 1 from public.alert_reads r where r.alert_id = a.id and r.user_id = auth.uid())
  from public.coop_alerts a
  join public.coop_members m on m.coop_id = a.coop_id
  join public.cooperatives c on c.id = a.coop_id
  where m.user_id = auth.uid() and a.created_at >= m.joined_at and a.created_at >= now() - make_interval(days => p_days)
  order by a.created_at desc limit 50;
$$;

create or replace function public.mark_alerts_read() returns void
language sql security definer set search_path = public as $$
  insert into public.alert_reads(user_id, alert_id)
  select auth.uid(), a.id from public.coop_alerts a join public.coop_members m on m.coop_id = a.coop_id
  where m.user_id = auth.uid() and a.created_at >= m.joined_at
  on conflict do nothing;
$$;

revoke all on function public.send_coop_alert(text, text, text), public.coop_reach(), public.coop_sent_alerts(), public.my_alerts(int), public.mark_alerts_read() from public;
grant execute on function public.send_coop_alert(text, text, text), public.coop_reach(), public.coop_sent_alerts(), public.my_alerts(int), public.mark_alerts_read() to authenticated;