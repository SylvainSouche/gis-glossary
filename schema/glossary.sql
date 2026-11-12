-- Glossary data model. See docs/data-model.md.

PRAGMA foreign_keys = ON;

-- A source as described in registry/sources.csv.
CREATE TABLE source (
    id         TEXT PRIMARY KEY,   -- registry id
    name       TEXT NOT NULL,
    address    TEXT NOT NULL,
    licence    TEXT NOT NULL,
    retrieved  TEXT NOT NULL
);

-- One concept as a source records it. Never edited: rebuilt from published/.
CREATE TABLE entry (
    id          INTEGER PRIMARY KEY,
    source_id   TEXT NOT NULL REFERENCES source(id),
    source_key  TEXT NOT NULL,     -- the source's own concept identifier
    subject     TEXT,              -- subject field or standard cited by the source
    UNIQUE (source_id, source_key)
);

-- A term as a source records it.
CREATE TABLE term (
    id          INTEGER PRIMARY KEY,
    entry_id    INTEGER NOT NULL REFERENCES entry(id),
    language    TEXT NOT NULL,
    text        TEXT NOT NULL,
    normalized  TEXT NOT NULL,     -- lower case, single spaces; used for matching
    term_type   TEXT NOT NULL DEFAULT 'term'
                CHECK (term_type IN ('term', 'abbreviation', 'phrase', 'formula')),
    status      TEXT NOT NULL DEFAULT 'unknown'
                CHECK (status IN ('preferred', 'admitted', 'deprecated', 'superseded', 'proposed', 'unknown')),
    reliability TEXT               -- source's own score, not comparable across sources
);
CREATE INDEX term_lookup ON term (language, normalized);

-- The project's unit of meaning: one sense, however many sources describe it.
CREATE TABLE concept (
    id          INTEGER PRIMARY KEY,
    label       TEXT NOT NULL,     -- English working label
    sense_note  TEXT,              -- written by this project, never copied
    status      TEXT NOT NULL DEFAULT 'candidate'
                CHECK (status IN ('candidate', 'reviewed', 'rejected')),
    ambiguous   INTEGER NOT NULL DEFAULT 0  -- 1 if a source has several senses here
);

-- Which source entries express a concept. Automatic links stay candidates.
CREATE TABLE concept_entry (
    concept_id  INTEGER NOT NULL REFERENCES concept(id),
    entry_id    INTEGER NOT NULL REFERENCES entry(id),
    method      TEXT NOT NULL,     -- e.g. english-exact, manual
    status      TEXT NOT NULL DEFAULT 'candidate'
                CHECK (status IN ('candidate', 'confirmed', 'rejected')),
    PRIMARY KEY (concept_id, entry_id)
);

-- The term chosen for a concept in a language, by review.
CREATE TABLE preferred_term (
    concept_id  INTEGER NOT NULL REFERENCES concept(id),
    language    TEXT NOT NULL,
    term_id     INTEGER NOT NULL REFERENCES term(id),
    decided_by  TEXT NOT NULL,
    decided_on  TEXT NOT NULL,
    PRIMARY KEY (concept_id, language)
);

-- Exact software labels. Kept apart from concepts: copied, never chosen.
CREATE TABLE gui_label (
    id          INTEGER PRIMARY KEY,
    application TEXT NOT NULL,     -- e.g. qgis
    version     TEXT NOT NULL,
    context     TEXT NOT NULL,     -- catalogue context
    source_text TEXT NOT NULL,     -- English string as shown
    language    TEXT NOT NULL,
    translation TEXT NOT NULL,
    source_normalized      TEXT NOT NULL,  -- accents, case and ellipsis removed
    translation_normalized TEXT NOT NULL,
    UNIQUE (application, version, context, source_text, language)
);
CREATE INDEX gui_from_english ON gui_label (language, source_normalized);
CREATE INDEX gui_to_english ON gui_label (language, translation_normalized);

-- Candidate translations of a concept, best evidence first.
CREATE VIEW candidate_term AS
SELECT c.id AS concept_id, c.label, c.ambiguous, t.language, t.text, t.term_type,
       t.status, e.source_id, ce.method, ce.status AS link_status
FROM concept c
JOIN concept_entry ce ON ce.concept_id = c.id AND ce.status <> 'rejected'
JOIN entry e ON e.id = ce.entry_id
JOIN term t ON t.entry_id = e.id
WHERE t.status NOT IN ('deprecated', 'superseded');
