CREATE TABLE IF NOT EXISTS osm (
    type varchar(255),
    id bigint NOT NULL,
    tags text,
    geometry geometry
);

CREATE TABLE IF NOT EXISTS segments (
    id bigint primary key,
    name varchar, 
    activity_type varchar(20),
    effort_count int, 
    athlete_count int,
    distance float, 
    average_grade float, 
    maximum_grade float, 
    elevation_high float,
    elevation_low float, 
    total_elevation_gain float, 
    geometry geometry
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