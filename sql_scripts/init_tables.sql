CREATE TABLE IF NOT EXISTS osm (
    geometry geometry,
    type varchar(255),
    id bigint NOT NULL,
    tags text
);

CREATE TABLE IF NOT EXISTS comuni (
    istat_comune bigint primary key,
    geometry geometry(MultiPolygon,4326),
    regione text,
    nome text,
    nome_secondario text,
    area double precision,
    popolazione bigint
);

CREATE TABLE IF NOT EXISTS coni (
    code int primary key,
    name varchar,
    region varchar,
    province varchar,
    comune varchar,
    agonistici int,
    praticanti int
);