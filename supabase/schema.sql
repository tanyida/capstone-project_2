-- ParentedSG — database setup for family accounts on Supabase.
--
-- Run this once: Supabase dashboard → SQL Editor → New query → paste this file → Run.
-- It is safe to run again; it only creates what is missing and refreshes the rest.
--
-- How sharing works
--   * Every parent signs in with their own email and password (Supabase Auth).
--   * A family account holds the children, leave and benefit records.
--   * The first parent creates the family and gets an invite code; the second parent
--     enters that code to join. A family holds at most two parents.
--   * Row-level security limits every table to members of the family that owns the row,
--     so the public "anon" key in the web page cannot read anyone's data.

-- ---------------------------------------------------------------- tables

create table if not exists public.families (
  id          uuid primary key default gen_random_uuid(),
  invite_code text not null unique,
  p1_name     text not null default 'Mum' check (char_length(p1_name) between 1 and 20),
  p2_name     text not null default 'Dad' check (char_length(p2_name) between 1 and 20),
  created_at  timestamptz not null default now()
);

create table if not exists public.family_members (
  family_id uuid not null references public.families (id) on delete cascade,
  user_id   uuid not null references auth.users (id) on delete cascade,
  email     text,
  joined_at timestamptz not null default now(),
  primary key (family_id, user_id)
);
-- one family per person keeps "which family am I in?" unambiguous
create unique index if not exists family_members_one_family_per_user on public.family_members (user_id);

create table if not exists public.children (
  id         uuid primary key,
  family_id  uuid not null references public.families (id) on delete cascade,
  name       text not null check (char_length(name) between 1 and 40),
  dob        date not null check (dob between '2000-01-01' and '2040-12-31'),
  created_at timestamptz not null default now(),
  unique (id, family_id)
);

create table if not exists public.custom_leave_types (
  id        uuid primary key,
  family_id uuid not null references public.families (id) on delete cascade,
  name      text not null check (char_length(name) between 1 and 30),
  days      numeric(5, 1) not null check (days > 0 and days <= 366)
);

-- child_id is set for maternity, paternity and Shared Parental Leave. The composite
-- foreign key stops a row pointing at another family's child.
create table if not exists public.leave_entries (
  id         uuid primary key,
  family_id  uuid not null references public.families (id) on delete cascade,
  parent     text not null check (parent in ('p1', 'p2')),
  type       text not null check (char_length(type) between 1 and 40),
  child_id   uuid,
  start_date date not null,
  end_date   date not null,
  days       numeric(5, 1) not null check (days > 0 and days <= 400),
  note       text not null default '' check (char_length(note) <= 80),
  created_at timestamptz not null default now(),
  check (end_date >= start_date),
  foreign key (child_id, family_id) references public.children (id, family_id) on delete cascade
);

create table if not exists public.benefit_transactions (
  id         uuid primary key,
  family_id  uuid not null references public.families (id) on delete cascade,
  child_id   uuid not null,
  account    text not null check (account in ('cda', 'lifesg', 'edusave', 'psea', 'medisave')),
  kind       text not null check (kind in ('spent', 'deposit', 'credit')),
  amount     numeric(12, 2) not null check (amount > 0 and amount < 1000000),
  tx_date    date not null,
  note       text not null default '' check (char_length(note) <= 80),
  created_at timestamptz not null default now(),
  foreign key (child_id, family_id) references public.children (id, family_id) on delete cascade
);

-- cash payouts a parent has ticked off as received
create table if not exists public.confirmed_payouts (
  family_id uuid not null references public.families (id) on delete cascade,
  payout_id text not null check (char_length(payout_id) <= 160),
  child_id  uuid not null,
  primary key (family_id, payout_id),
  foreign key (child_id, family_id) references public.children (id, family_id) on delete cascade
);

-- ---------------------------------------------------------------- helpers

create or replace function public.is_family_member(fid uuid)
returns boolean
language sql stable security definer set search_path = public
as $$
  select exists (select 1 from public.family_members where family_id = fid and user_id = auth.uid());
$$;

-- Eight characters from an alphabet without look-alikes (no 0/O, 1/I), shown as ABCD-EFGH.
-- Bytes come from gen_random_uuid(), which uses the server's strong random source; the
-- uuid's fixed version and variant positions are skipped.
create or replace function public.new_invite_code()
returns text
language plpgsql volatile set search_path = public
as $$
declare
  alphabet constant text := 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  hex   text := replace(gen_random_uuid()::text, '-', '');
  picks int[] := array[1, 3, 5, 7, 9, 11, 19, 21];
  code  text := '';
  p     int;
begin
  foreach p in array picks loop
    code := code || substr(alphabet, (('x' || substr(hex, p, 2))::bit(8)::int % 32) + 1, 1);
  end loop;
  return substr(code, 1, 4) || '-' || substr(code, 5, 4);
end;
$$;

create or replace function public.normalise_invite_code(code text)
returns text
language sql immutable
as $$
  select case when char_length(c) = 8 then substr(c, 1, 4) || '-' || substr(c, 5, 4) else c end
  from (select upper(regexp_replace(coalesce(code, ''), '[^A-Za-z0-9]', '', 'g')) as c) s;
$$;

-- Removing a custom leave type removes the leave logged against it.
create or replace function public.delete_custom_leave_entries()
returns trigger
language plpgsql security definer set search_path = public
as $$
begin
  delete from public.leave_entries where family_id = old.family_id and type = 'c:' || old.id::text;
  return old;
end;
$$;

drop trigger if exists custom_leave_type_deleted on public.custom_leave_types;
create trigger custom_leave_type_deleted
  after delete on public.custom_leave_types
  for each row execute function public.delete_custom_leave_entries();

-- ---------------------------------------------------------------- family membership

create or replace function public.create_family()
returns uuid
language plpgsql security definer set search_path = public
as $$
declare
  uid uuid := auth.uid();
  fid uuid;
  tries int := 0;
begin
  if uid is null then
    raise exception 'Sign in first.';
  end if;
  if exists (select 1 from public.family_members where user_id = uid) then
    raise exception 'You already belong to a family account.';
  end if;
  loop
    begin
      insert into public.families (invite_code) values (public.new_invite_code()) returning id into fid;
      exit;
    exception when unique_violation then
      tries := tries + 1;
      if tries > 5 then raise; end if;
    end;
  end loop;
  insert into public.family_members (family_id, user_id, email) values (fid, uid, auth.jwt() ->> 'email');
  return fid;
end;
$$;

create or replace function public.join_family(code text)
returns uuid
language plpgsql security definer set search_path = public
as $$
declare
  uid  uuid := auth.uid();
  fid  uuid;
  mine uuid;
begin
  if uid is null then
    raise exception 'Sign in first.';
  end if;
  -- lock the family row so two people cannot both take the second place
  select id into fid from public.families
   where invite_code = public.normalise_invite_code(code)
   for update;
  if fid is null then
    raise exception 'That invite code does not match a family account. Check it with your spouse.';
  end if;
  select family_id into mine from public.family_members where user_id = uid;
  if mine = fid then
    return fid;
  end if;
  if mine is not null then
    raise exception 'You already belong to another family account. Leave it first.';
  end if;
  if (select count(*) from public.family_members where family_id = fid) >= 2 then
    raise exception 'This family account already has two parents.';
  end if;
  insert into public.family_members (family_id, user_id, email) values (fid, uid, auth.jwt() ->> 'email');
  return fid;
end;
$$;

create or replace function public.regenerate_invite_code()
returns text
language plpgsql security definer set search_path = public
as $$
declare
  fid  uuid;
  code text;
begin
  select family_id into fid from public.family_members where user_id = auth.uid();
  if fid is null then
    raise exception 'Join or create a family account first.';
  end if;
  loop
    begin
      code := public.new_invite_code();
      update public.families set invite_code = code where id = fid;
      return code;
    exception when unique_violation then
      null;  -- vanishingly rare; draw again
    end;
  end loop;
end;
$$;

-- The last parent to leave takes the family's records with them.
create or replace function public.leave_family()
returns void
language plpgsql security definer set search_path = public
as $$
declare
  fid uuid;
begin
  delete from public.family_members where user_id = auth.uid() returning family_id into fid;
  if fid is not null and not exists (select 1 from public.family_members where family_id = fid) then
    delete from public.families where id = fid;
  end if;
end;
$$;

-- Replace everything in the caller's family in one transaction: restoring a backup,
-- moving data saved on a device into the account, or erasing it all.
create or replace function public.replace_family_data(payload jsonb)
returns void
language plpgsql security definer set search_path = public
as $$
declare
  fid uuid;
begin
  select family_id into fid from public.family_members where user_id = auth.uid();
  if fid is null then
    raise exception 'Join or create a family account first.';
  end if;

  delete from public.custom_leave_types where family_id = fid;
  delete from public.children where family_id = fid;          -- cascades to child-linked rows
  delete from public.leave_entries where family_id = fid;
  delete from public.benefit_transactions where family_id = fid;
  delete from public.confirmed_payouts where family_id = fid;

  update public.families
     set p1_name = coalesce(nullif(left(payload -> 'parents' ->> 'p1', 20), ''), 'Mum'),
         p2_name = coalesce(nullif(left(payload -> 'parents' ->> 'p2', 20), ''), 'Dad')
   where id = fid;

  insert into public.children (id, family_id, name, dob)
  select x.id, fid, x.name, x.dob
    from jsonb_to_recordset(coalesce(payload -> 'kids', '[]')) as x (id uuid, name text, dob date);

  insert into public.custom_leave_types (id, family_id, name, days)
  select x.id, fid, x.name, x.days
    from jsonb_to_recordset(coalesce(payload -> 'custom', '[]')) as x (id uuid, name text, days numeric);

  insert into public.leave_entries (id, family_id, parent, type, child_id, start_date, end_date, days, note)
  select x.id, fid, x.parent, x.type, x."childId", x.start, coalesce(x."end", x.start), x.days, coalesce(x.note, '')
    from jsonb_to_recordset(coalesce(payload -> 'leave', '[]'))
      as x (id uuid, parent text, type text, "childId" uuid, start date, "end" date, days numeric, note text);

  insert into public.benefit_transactions (id, family_id, child_id, account, kind, amount, tx_date, note)
  select x.id, fid, x."childId", x.account, x.kind, x.amount, x.date, coalesce(x.note, '')
    from jsonb_to_recordset(coalesce(payload -> 'tx', '[]'))
      as x (id uuid, "childId" uuid, account text, kind text, amount numeric, date date, note text);

  insert into public.confirmed_payouts (family_id, payout_id, child_id)
  select fid, x.payout_id, x.child_id
    from jsonb_to_recordset(coalesce(payload -> 'confirmed', '[]')) as x (payout_id text, child_id uuid);
end;
$$;

-- ---------------------------------------------------------------- row-level security

alter table public.families             enable row level security;
alter table public.family_members       enable row level security;
alter table public.children             enable row level security;
alter table public.custom_leave_types   enable row level security;
alter table public.leave_entries        enable row level security;
alter table public.benefit_transactions enable row level security;
alter table public.confirmed_payouts    enable row level security;

drop policy if exists "members read their family" on public.families;
create policy "members read their family" on public.families
  for select to authenticated using (public.is_family_member(id));

drop policy if exists "members rename parents" on public.families;
create policy "members rename parents" on public.families
  for update to authenticated using (public.is_family_member(id)) with check (public.is_family_member(id));

drop policy if exists "members see each other" on public.family_members;
create policy "members see each other" on public.family_members
  for select to authenticated using (public.is_family_member(family_id));

do $$
declare
  t text;
begin
  foreach t in array array['children', 'custom_leave_types', 'leave_entries', 'benefit_transactions', 'confirmed_payouts'] loop
    execute format('drop policy if exists "family members manage %1$s" on public.%1$I', t);
    execute format(
      'create policy "family members manage %1$s" on public.%1$I for all to authenticated '
      'using (public.is_family_member(family_id)) with check (public.is_family_member(family_id))', t);
  end loop;
end;
$$;

-- Members may rename the parents but nothing else on the family row. Joining, leaving
-- and invite codes only happen through the functions above.
revoke insert, update, delete on public.families from anon, authenticated;
grant update (p1_name, p2_name) on public.families to authenticated;
revoke insert, update, delete on public.family_members from anon, authenticated;

revoke all on function public.is_family_member(uuid)       from public, anon;
revoke all on function public.new_invite_code()            from public, anon, authenticated;
revoke all on function public.create_family()              from public, anon;
revoke all on function public.join_family(text)            from public, anon;
revoke all on function public.regenerate_invite_code()     from public, anon;
revoke all on function public.leave_family()               from public, anon;
revoke all on function public.replace_family_data(jsonb)   from public, anon;
grant execute on function public.is_family_member(uuid)     to authenticated;
grant execute on function public.create_family()            to authenticated;
grant execute on function public.join_family(text)          to authenticated;
grant execute on function public.regenerate_invite_code()   to authenticated;
grant execute on function public.leave_family()             to authenticated;
grant execute on function public.replace_family_data(jsonb) to authenticated;

-- ---------------------------------------------------------------- live updates

-- Lets both parents' screens refresh when either one logs something.
do $$
declare
  t text;
begin
  if exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    foreach t in array array['families', 'family_members', 'children', 'custom_leave_types',
                             'leave_entries', 'benefit_transactions', 'confirmed_payouts'] loop
      if not exists (select 1 from pg_publication_tables
                      where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = t) then
        execute format('alter publication supabase_realtime add table public.%I', t);
      end if;
    end loop;
  end if;
end;
$$;
