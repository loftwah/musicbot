create table if not exists musicbot_public.filter
(
    id           serial primary key,
    user_id      integer not null references musicbot_public.user (id) on delete cascade default musicbot_public.current_musicbot_id(),
    name         text not null,
    min_duration integer default 0,
    max_duration integer default +2147483647,
    min_size     integer default 0,
    max_size     integer default +2147483647,
    min_rating   float default 0.0 check (min_rating between 0.0 and 5.0),
    max_rating   float default 5.0 check (max_rating between 0.0 and 5.0),
    artists      text[] default '{}',
    no_artists   text[] default '{}',
    albums       text[] default '{}',
    no_albums    text[] default '{}',
    titles       text[] default '{}',
    no_titles    text[] default '{}',
    genres       text[] default '{}',
    no_genres    text[] default '{}',
    formats      text[] default '{}',
    no_formats   text[] default '{}',
    keywords     text[] default '{}',
    no_keywords  text[] default '{}',
    shuffle      boolean default 'false',
    relative     boolean default 'false',
    "limit"      integer default +2147483647,
    youtubes     text[] default '{}',
    no_youtubes  text[] default '{}',
    spotifys     text[] default '{}',
    no_spotifys  text[] default '{}',
	created_at   timestamp with time zone default now(),
	updated_at   timestamp with time zone default now(),
    unique(name, user_id)
);
alter table if exists musicbot_public.filter enable row level security;
grant select on table musicbot_public.filter to musicbot_anonymous, musicbot_user;
grant insert, update, delete on table musicbot_public.filter to musicbot_user;
grant usage on sequence musicbot_public.filter_id_seq to musicbot_user;

drop policy if exists insert_filter on musicbot_public.filter cascade;
create policy insert_filter on musicbot_public.filter for insert with check (user_id = musicbot_public.current_musicbot_id());

drop policy if exists select_filter on musicbot_public.filter cascade;
create policy select_filter on musicbot_public.filter for select using (user_id = musicbot_public.current_musicbot_id());

drop policy if exists update_filter on musicbot_public.filter cascade;
create policy update_filter on musicbot_public.filter for update using (user_id = musicbot_public.current_musicbot_id());

drop policy if exists delete_filter on musicbot_public.filter cascade;
create policy delete_filter on musicbot_public.filter for delete using (user_id = musicbot_public.current_musicbot_id());

create or replace function musicbot_public.load_default_filters()
returns void as
$$
begin
    insert into musicbot_public.filter as f (name) values ('default') on conflict do nothing;
    insert into musicbot_public.filter as f (name, youtubes) values ('youtube not found', '{not found}') on conflict do nothing;
    insert into musicbot_public.filter as f (name, spotifys) values ('spotify not found', '{not found}') on conflict do nothing;
    insert into musicbot_public.filter as f (name, youtubes) values ('no youtube links', '{}') on conflict do nothing;
    insert into musicbot_public.filter as f (name, spotifys) values ('no spotify links', '{}') on conflict do nothing;
    insert into musicbot_public.filter as f (name, min_rating, max_rating) values ('no rating', 0.0, 0.0) on conflict do nothing;
    insert into musicbot_public.filter as f (name, min_rating, no_keywords) values ('best (4.0+)', 4.0, '{cutoff,bad,demo,intro}') on conflict do nothing;
    insert into musicbot_public.filter as f (name, min_rating, no_keywords) values ('best (4.5+)', 4.5, '{cutoff,bad,demo,intro}') on conflict do nothing;
    insert into musicbot_public.filter as f (name, min_rating, no_keywords) values ('best (5.0+)', 5.0, '{cutoff,bad,demo,intro}') on conflict do nothing;
    insert into musicbot_public.filter as f (name, no_keywords) values ('no live', '{live}') on conflict do nothing;
    insert into musicbot_public.filter as f (name, keywords) values ('only live', '{live}') on conflict do nothing;
end;
$$ language plpgsql;
grant execute on function musicbot_public.load_default_filters to musicbot_user;
