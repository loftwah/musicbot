create materialized view if not exists mmusics as
select
    m.id        as id,
    m.title     as title,
    al.name     as album,
    g.name      as genre,
    a.name      as artist,
    f.name      as folder,
    m.youtube   as youtube,
    m.number    as number,
    m.path      as path,
    m.rating    as rating,
    m.duration  as duration,
    m.size      as size,
    (
        select coalesce(array_agg(name), '{}')
        from
        (
            select distinct name
            from music_tags mt
            inner join tags t on mt.tag_id = t.id
            where mt.music_id = m.id
        ) as separated_keywords
    ) as keywords
from musics m
inner join albums al on al.id = m.album_id
inner join artists a on a.id = m.artist_id
inner join genres g on g.id = m.genre_id
inner join folders f on f.id = m.folder_id
order by a.name, al.name, m.number;
create unique index if not exists mmusics_id_idx on mmusics (id);
create unique index if not exists mmusics_path_idx on mmusics (path);
create index if not exists mmusics_artist_idx on mmusics (artist);

--create materialized view if not exists smusics as
--select
--    m.id        as id,
--    m.title     as title,
--    al.name     as album,
--    g.name      as genre,
--    a.name      as artist,
--    f.name      as folder,
--    m.youtube   as youtube,
--    m.number    as number,
--    m.path      as path,
--    m.rating    as rating,
--    m.duration  as duration,
--    m.size      as size,
--    (
--        select coalesce(array_agg(name), '{}')
--        from
--        (
--            select distinct name
--            from music_tags mt
--            inner join tags t on mt.tag_id = t.id
--            where mt.music_id = m.id
--        ) as separated_keywords
--    ) as keywords,
--    setweight(to_tsvector('simple', coalesce(m.title, '')), 'A') ||
--    setweight(to_tsvector('simple', coalesce(a.name, '')), 'B') ||
--    setweight(to_tsvector('simple', coalesce(al.name, '')), 'C') ||
--    setweight(to_tsvector('simple', coalesce(g.name, '')), 'D') ||
--    setweight(to_tsvector('simple', (select string_agg(distinct name, ' ')
--                           from music_tags mt
--                           inner join tags t on mt.tag_id = t.id
--                           where mt.music_id = m.id
--                         )), 'D') as document
--from musics m
--inner join albums al on al.id = m.album_id
--inner join artists a on a.id = m.artist_id
--inner join genres g on g.id = m.genre_id
--inner join folders f on f.id = m.folder_id
--order by a.name, al.name, m.number;
----create unique index if not exists idx_id on smusics (id);
--create unique index on smusics (id);
--create index if not exists idx_fts_search on smusics using gin(document);
--
--create materialized view if not exists unique_lexeme as
--select word from ts_stat(
--'select
--    to_tsvector(''simple'', coalesce(m.title, '''')) ||
--    to_tsvector(''simple'', coalesce(a.name, '''')) ||
--    to_tsvector(''simple'', coalesce(al.name, '''')) ||
--    to_tsvector(''simple'', coalesce(g.name, '''')) ||
--    to_tsvector(''simple'', (select string_agg(distinct name, '' '')
--                           from music_tags mt
--                           inner join tags t on mt.tag_id = t.id
--                           where mt.music_id = m.id
--                         )) as document
--from musics m
--inner join albums al on al.id = m.album_id
--inner join artists a on a.id = m.artist_id
--inner join genres g on g.id = m.genre_id
--inner join folders f on f.id = m.folder_id');
--create index if not exists words_idx on unique_lexeme using gin(word gin_trgm_ops);

--with fuzzy as (select word from unique_lexeme where similarity(word, 'buck') > 0.3 order by word <-> 'buck' limit 1) select * from smusics where document @@ to_tsquery('simple', (select word from fuzzy)) order by ts_rank(document, to_tsquery('simple', (select word from fuzzy))) desc;
