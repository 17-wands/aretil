-- aretil data model. See ARCHITECTURE.md section 4.
-- Tables are ordered so every foreign-key target exists before it is referenced.

CREATE TABLE clients (
    client_id        VARCHAR PRIMARY KEY,
    name             VARCHAR NOT NULL,
    industry         VARCHAR,
    parent_client_id VARCHAR REFERENCES clients (client_id)
);

CREATE TABLE matters (
    matter_id     VARCHAR PRIMARY KEY,
    name          VARCHAR NOT NULL,
    client_id     VARCHAR NOT NULL REFERENCES clients (client_id),
    practice_area VARCHAR,
    deal_type     VARCHAR,
    jurisdiction  VARCHAR,
    deal_value    DECIMAL(18, 2),
    year          INTEGER,
    firm_role     VARCHAR,
    description   VARCHAR,
    attributes    VARIANT
);

CREATE TABLE timekeepers (
    timekeeper_id    VARCHAR PRIMARY KEY,
    name             VARCHAR NOT NULL,
    title            VARCHAR,
    practice_group   VARCHAR,
    years_experience INTEGER
);

CREATE TABLE matter_timekeepers (
    matter_id      VARCHAR NOT NULL REFERENCES matters (matter_id),
    timekeeper_id  VARCHAR NOT NULL REFERENCES timekeepers (timekeeper_id),
    role_on_matter VARCHAR,
    PRIMARY KEY (matter_id, timekeeper_id)
);

CREATE TABLE parties (
    party_id   VARCHAR PRIMARY KEY,
    matter_id  VARCHAR NOT NULL REFERENCES matters (matter_id),
    raw_name   VARCHAR NOT NULL,
    party_type VARCHAR,
    side       VARCHAR
);

CREATE TABLE resolved_parties (
    canonical_party_id VARCHAR PRIMARY KEY,
    canonical_name     VARCHAR NOT NULL
);

CREATE TABLE party_resolution (
    party_id           VARCHAR PRIMARY KEY REFERENCES parties (party_id),
    canonical_party_id VARCHAR NOT NULL REFERENCES resolved_parties (canonical_party_id)
);

CREATE TABLE tags (
    tag_id   VARCHAR PRIMARY KEY,
    tag_type VARCHAR NOT NULL,
    value    VARCHAR NOT NULL
);

CREATE TABLE matter_tags (
    matter_id VARCHAR NOT NULL REFERENCES matters (matter_id),
    tag_id    VARCHAR NOT NULL REFERENCES tags (tag_id),
    PRIMARY KEY (matter_id, tag_id)
);

-- matter_embeddings holds matter-description vectors. Issue #6 finalises the
-- embedding storage (Lance dataset and the chosen model dimension).
CREATE TABLE matter_embeddings (
    matter_id VARCHAR PRIMARY KEY REFERENCES matters (matter_id),
    embedding FLOAT[]
);
