
DROP TABLE IF EXISTS feedback_events;
DROP TABLE IF EXISTS briefings;
DROP TABLE IF EXISTS user_entities;
DROP TABLE IF EXISTS user_interests;
DROP TABLE IF EXISTS user_sources;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id              uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  name            text        NOT NULL,
  email           text        NOT NULL UNIQUE,
  password_hash   text        NOT NULL,
  reading_time    text,
  format          text,
  delivery_time   text,
  read_reason     text,
  created_at      timestamptz DEFAULT now()
  );

CREATE TABLE user_sources (
  id       uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id  uuid REFERENCES users(id) ON DELETE CASCADE,
  source   text NOT NULL
);

CREATE TABLE user_interests (
  id            uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id       uuid        REFERENCES users(id) ON DELETE CASCADE,
  topic         text        NOT NULL,
  parent_topic  text,
  source        text,
  weight        float       DEFAULT 1.0,
  updated_at    timestamptz DEFAULT now()
);

CREATE TABLE user_entities (
  id           uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id      uuid        REFERENCES users(id) ON DELETE CASCADE,
  entity_name  text        NOT NULL,
  weight       float       DEFAULT 1.0,
  updated_at   timestamptz DEFAULT now()
);

CREATE TABLE briefings (
  id          uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id     uuid        REFERENCES users(id) ON DELETE CASCADE,
  sent_at     timestamptz DEFAULT now(),
  article_ids text[]
);

CREATE TABLE feedback_events (
  id           uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id      uuid        REFERENCES users(id) ON DELETE CASCADE,
  article_id   text        NOT NULL,
  event_type   text        NOT NULL,
  occurred_at  timestamptz DEFAULT now()
);


--old version of dtabase schema, not used anymore but keeping for reference
/*
CREATE TABLE users(
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  name text,
  email text,
  date_created timestamptz DEFAULT now()
);

CREATE TABLE user_interests (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid REFERENCES users(id),
  topic text,
  preference_vector vector(1536),
  created_at timestamptz DEFAULT now()
);
*/


