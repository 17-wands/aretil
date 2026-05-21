-- aretil canonical tool layer. See ARCHITECTURE.md section 5.
-- Each macro is a parameterised SELECT that the MCP server and the web
-- app's Node API call with the same signature.

-- search_matters: rank matters by semantic similarity to a query embedding,
-- optionally filtered by structured fields. The counsel filter accepts any
-- name variant (Latham, L&W, Latham & Watkins LLP) and resolves it through
-- party_resolution so all variants find the same matters.
CREATE OR REPLACE MACRO search_matters(
    query_embedding,
    practice_area := NULL,
    industry := NULL,
    deal_type := NULL,
    jurisdiction := NULL,
    min_value := NULL,
    max_value := NULL,
    counsel := NULL,
    result_limit := 10
) AS TABLE (
    SELECT
        m.matter_id,
        m.name,
        m.client_id,
        c.name AS client_name,
        m.practice_area,
        m.deal_type,
        m.jurisdiction,
        m.deal_value,
        m.year,
        m.firm_role,
        m.description,
        array_cosine_similarity(e.embedding, query_embedding::FLOAT[256]) AS similarity
    FROM matters m
    JOIN clients c USING (client_id)
    JOIN matter_embeddings e USING (matter_id)
    WHERE (practice_area IS NULL OR m.practice_area = practice_area)
      AND (industry IS NULL OR c.industry = industry)
      AND (deal_type IS NULL OR m.deal_type = deal_type)
      AND (jurisdiction IS NULL OR m.jurisdiction = jurisdiction)
      AND (min_value IS NULL OR m.deal_value >= min_value)
      AND (max_value IS NULL OR m.deal_value <= max_value)
      AND (counsel IS NULL OR m.matter_id IN (
          SELECT p.matter_id
          FROM parties p
          JOIN party_resolution pr USING (party_id)
          WHERE pr.canonical_party_id = (
              SELECT pr2.canonical_party_id
              FROM parties p2
              JOIN party_resolution pr2 USING (party_id)
              WHERE p2.raw_name = counsel
              LIMIT 1
          )
      ))
    ORDER BY similarity DESC
    LIMIT result_limit
);

-- find_relevant_timekeepers: rank timekeepers by depth of relevant matter
-- experience for the query. Top relevance is the timekeeper's single most
-- similar matter, with average relevance as a tiebreaker by overall depth.
CREATE OR REPLACE MACRO find_relevant_timekeepers(
    query_embedding,
    result_limit := 10
) AS TABLE (
    WITH matter_sim AS (
        SELECT
            m.matter_id,
            array_cosine_similarity(e.embedding, query_embedding::FLOAT[256]) AS sim
        FROM matters m
        JOIN matter_embeddings e USING (matter_id)
    )
    SELECT
        t.timekeeper_id,
        t.name,
        t.title,
        t.practice_group,
        count(DISTINCT mt.matter_id) AS matter_count,
        max(ms.sim) AS top_relevance,
        avg(ms.sim) AS avg_relevance
    FROM timekeepers t
    JOIN matter_timekeepers mt USING (timekeeper_id)
    JOIN matter_sim ms USING (matter_id)
    GROUP BY t.timekeeper_id, t.name, t.title, t.practice_group
    ORDER BY top_relevance DESC, avg_relevance DESC
    LIMIT result_limit
);

-- get_timekeeper_history: a timekeeper's full matter history with roles.
CREATE OR REPLACE MACRO get_timekeeper_history(timekeeper_name) AS TABLE (
    SELECT
        t.timekeeper_id,
        t.name,
        m.matter_id,
        m.name AS matter_name,
        m.practice_area,
        m.deal_type,
        m.year,
        m.deal_value,
        mt.role_on_matter,
        m.description
    FROM timekeepers t
    JOIN matter_timekeepers mt USING (timekeeper_id)
    JOIN matters m USING (matter_id)
    WHERE t.name = timekeeper_name
    ORDER BY m.year DESC, m.matter_id
);

-- get_client_history: matters of the named client plus matters of any
-- subsidiary (a client whose parent_client_id points at the named client).
-- via_subsidiary distinguishes the two so the caller can group them.
CREATE OR REPLACE MACRO get_client_history(client_name) AS TABLE (
    WITH target AS (
        SELECT client_id FROM clients WHERE name = client_name LIMIT 1
    ),
    in_scope AS (
        SELECT client_id, FALSE AS via_subsidiary FROM target
        UNION ALL
        SELECT c.client_id, TRUE
        FROM clients c
        WHERE c.parent_client_id IN (SELECT client_id FROM target)
    )
    SELECT
        m.matter_id,
        m.name AS matter_name,
        c.client_id,
        c.name AS client_name,
        s.via_subsidiary,
        m.practice_area,
        m.deal_type,
        m.jurisdiction,
        m.deal_value,
        m.year,
        m.firm_role,
        m.description
    FROM matters m
    JOIN clients c USING (client_id)
    JOIN in_scope s USING (client_id)
    ORDER BY m.year DESC, m.matter_id
);

-- get_market_terms: aggregate "what's market" stats over comparable matters
-- for a given deal type, optionally narrowed by practice area or jurisdiction.
CREATE OR REPLACE MACRO get_market_terms(
    deal_type,
    practice_area := NULL,
    jurisdiction := NULL
) AS TABLE (
    SELECT
        deal_type AS deal_type,
        count(*) AS matter_count,
        min(m.year) AS earliest_year,
        max(m.year) AS latest_year,
        min(m.deal_value) AS min_value,
        approx_quantile(m.deal_value, 0.25) AS p25_value,
        median(m.deal_value) AS median_value,
        approx_quantile(m.deal_value, 0.75) AS p75_value,
        max(m.deal_value) AS max_value,
        avg(m.deal_value) AS mean_value
    FROM matters m
    WHERE m.deal_type = deal_type
      AND (practice_area IS NULL OR m.practice_area = practice_area)
      AND (jurisdiction IS NULL OR m.jurisdiction = jurisdiction)
);

-- assemble_pitch_context: one bundle for pitch drafting — top matters by
-- semantic similarity, top relevant timekeepers, and market terms for the
-- deal type (if one is supplied). Returns a single row with three nested
-- columns so the caller can pull everything in one query.
CREATE OR REPLACE MACRO assemble_pitch_context(
    query_embedding,
    q_practice_area := NULL,
    q_industry := NULL,
    q_deal_type := NULL,
    q_jurisdiction := NULL,
    q_min_value := NULL,
    q_max_value := NULL,
    matter_limit := 5,
    timekeeper_limit := 5
) AS TABLE (
    SELECT
        (SELECT list(struct_pack(
                matter_id, name, client_name, practice_area, deal_type,
                jurisdiction, deal_value, year, similarity
            ) ORDER BY similarity DESC)
         FROM search_matters(
            query_embedding,
            practice_area := q_practice_area,
            industry := q_industry,
            deal_type := q_deal_type,
            jurisdiction := q_jurisdiction,
            min_value := q_min_value,
            max_value := q_max_value,
            result_limit := matter_limit
         )) AS matters,
        (SELECT list(struct_pack(
                timekeeper_id, name, title, practice_group,
                matter_count, top_relevance, avg_relevance
            ) ORDER BY top_relevance DESC)
         FROM find_relevant_timekeepers(
            query_embedding,
            result_limit := timekeeper_limit
         )) AS timekeepers,
        CASE WHEN q_deal_type IS NOT NULL THEN (
            SELECT struct_pack(
                matter_count, median_value, mean_value,
                p25_value, p75_value, earliest_year, latest_year
            )
            FROM get_market_terms(
                q_deal_type,
                practice_area := q_practice_area,
                jurisdiction := q_jurisdiction
            )
        ) ELSE NULL END AS market_terms
);
