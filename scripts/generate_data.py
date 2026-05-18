"""Build the aretil demo dataset, seeded from public SEC EDGAR filings.

Real, straight from EDGAR (data.sec.gov): the client companies, their
industries (SIC) and states of incorporation, the M&A filing types they filed,
and the filing years. Synthesized deterministically with a fixed seed: the
fictional law firm and its timekeepers, the firm's role on each matter,
illustrative deal values, and the pairing of counsel/advisor firms to matters.

Counsel and financial-advisor names are real, public firm names — used so the
entity-resolution layer (Splink, issue #5) has genuine name variants to
reconcile. The law firm itself and its timekeepers are the only invented
organisation and people in the dataset.

A single M&A deal produces many filings (proxies, amendments, communications),
so filings are collapsed to one matter per company per year.

Output: JSON fixtures in data/fixtures/. The fixtures are committed, so the
build (scripts/build_db.py) and the test suite need no network access.

Run:  python scripts/generate_data.py
"""

from __future__ import annotations

import json
import random
import time
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"

# SEC requires a descriptive User-Agent that includes a contact address.
SEC_USER_AGENT = "aretil-prototype admin@aretil.example.com"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
REQUEST_DELAY_SECONDS = 0.2  # well under SEC's 10 requests/second limit

SEED = 20260518
MAX_MATTERS = 90

# The fictional firm — the only invented organisation in the dataset.
FIRM_NAME = "Hale Brennan & Olufsen LLP"

# Curated real public companies grouped by sector. The sector sets the matter's
# practice area; every other company attribute is taken from EDGAR.
COMPANIES: dict[str, list[str]] = {
    "Healthcare": [
        "PFE", "MRK", "ABBV", "AMGN", "GILD", "BMY", "JNJ", "LLY",
        "TMO", "DHR", "CVS", "UNH", "CI", "MDT", "BDX", "VRTX",
    ],
    "Financial Services": [
        "JPM", "BAC", "MS", "GS", "SCHW", "BLK", "C", "WFC",
        "PNC", "COF", "ICE", "CME", "SPGI", "MET", "AIG", "AON",
    ],
    "Technology": [
        "MSFT", "CRM", "ORCL", "ADBE", "CSCO", "IBM", "AVGO", "INTC",
        "QCOM", "HPQ", "HPE", "NOW", "INTU", "AMD", "TXN", "MU",
    ],
}

# EDGAR M&A-related form types -> deal type. Issuer self-tenders (SC TO-I) are
# excluded: they are buybacks, not acquisitions.
DEAL_FORMS: dict[str, str] = {
    "S-4": "Merger",
    "S-4/A": "Merger",
    "425": "Merger",
    "DEFM14A": "Merger (shareholder vote)",
    "PREM14A": "Merger (shareholder vote)",
    "DEFM14C": "Merger (information statement)",
    "SC 13E3": "Going-private",
    "SC 13E3/A": "Going-private",
    "SC 14D9": "Tender offer",
    "SC 14D9/A": "Tender offer",
    "SC TO-T": "Tender offer",
    "SC TO-T/A": "Tender offer",
}
# When a company-year has several forms, the most representative one wins.
FORM_PRIORITY = [
    "DEFM14A", "PREM14A", "DEFM14C", "S-4", "SC TO-T", "SC 13E3",
    "SC 14D9", "S-4/A", "SC TO-T/A", "SC 13E3/A", "425",
]

# Real law firms with real, commonly used name variants. Splink (issue #5)
# reconciles these; "Latham & Watkins" deliberately carries the most variants.
LAW_FIRMS: list[list[str]] = [
    ["Latham & Watkins LLP", "Latham & Watkins", "Latham", "L&W"],
    ["Skadden, Arps, Slate, Meagher & Flom LLP", "Skadden, Arps", "Skadden"],
    ["Wachtell, Lipton, Rosen & Katz", "Wachtell, Lipton", "Wachtell"],
    ["Cravath, Swaine & Moore LLP", "Cravath, Swaine & Moore", "Cravath"],
    ["Sullivan & Cromwell LLP", "Sullivan & Cromwell", "S&C"],
    ["Davis Polk & Wardwell LLP", "Davis Polk & Wardwell", "Davis Polk"],
    ["Simpson Thacher & Bartlett LLP", "Simpson Thacher & Bartlett", "Simpson Thacher"],
    ["Kirkland & Ellis LLP", "Kirkland & Ellis", "Kirkland", "K&E"],
    ["Weil, Gotshal & Manges LLP", "Weil, Gotshal & Manges", "Weil"],
    ["Gibson, Dunn & Crutcher LLP", "Gibson, Dunn & Crutcher", "Gibson Dunn"],
    ["Paul, Weiss, Rifkind, Wharton & Garrison LLP", "Paul, Weiss", "Paul Weiss"],
    ["Cleary Gottlieb Steen & Hamilton LLP", "Cleary Gottlieb", "Cleary"],
]
FINANCIAL_ADVISORS: list[list[str]] = [
    ["Goldman Sachs & Co. LLC", "Goldman Sachs", "Goldman"],
    ["Morgan Stanley & Co. LLC", "Morgan Stanley"],
    ["J.P. Morgan Securities LLC", "J.P. Morgan", "JPMorgan"],
    ["Centerview Partners LLC", "Centerview Partners", "Centerview"],
    ["Evercore Inc.", "Evercore"],
    ["Lazard Freres & Co. LLC", "Lazard"],
    ["BofA Securities, Inc.", "BofA Securities", "Bank of America"],
    ["Citigroup Global Markets Inc.", "Citigroup", "Citi"],
]

TIMEKEEPER_FIRST = [
    "Alan", "Priya", "Marcus", "Elena", "David", "Sophia", "James", "Wei",
    "Rachel", "Tomas", "Nina", "Daniel", "Grace", "Omar", "Hannah", "Victor",
    "Claire", "Leo", "Maya", "Ethan", "Iris", "Noah",
]
TIMEKEEPER_LAST = [
    "Reyes", "Caldwell", "Okafor", "Petrov", "Nakamura", "Schwartz",
    "Donnelly", "Bianchi", "Mensah", "Kowalski", "Vance", "Ferreira",
    "Lindqvist", "Abernathy", "Cho", "Ruiz", "Whitfield", "Banerjee",
    "Stafford", "Delgado", "Hartley", "Osei",
]
TIMEKEEPER_TITLES = ["Partner", "Partner", "Counsel", "Senior Associate",
                     "Associate", "Associate"]
PRACTICE_GROUPS = ["Mergers & Acquisitions", "Corporate", "Healthcare",
                   "Financial Institutions", "Technology Transactions",
                   "Antitrust"]
MATTER_ROLES = ["Lead", "Supporting", "Associate"]
FIRM_ROLES = ["Lead counsel", "Co-counsel", "Advisor"]
DEAL_SIDES = ["buy-side", "sell-side"]


def _get_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": SEC_USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_ticker_index() -> dict[str, dict]:
    """Return a ticker -> {cik_str, ticker, title} map from EDGAR."""
    raw = _get_json(COMPANY_TICKERS_URL)
    return {entry["ticker"]: entry for entry in raw.values()}


def harvest_from_edgar(ticker_index: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    """Fetch submissions for the curated companies and harvest M&A matters."""
    clients: list[dict] = []
    raw_matters: list[dict] = []
    for sector, tickers in COMPANIES.items():
        for ticker in tickers:
            entry = ticker_index.get(ticker)
            if entry is None:
                print(f"  skip {ticker}: not in EDGAR ticker index")
                continue
            cik = entry["cik_str"]
            time.sleep(REQUEST_DELAY_SECONDS)
            try:
                submissions = _get_json(SUBMISSIONS_URL.format(cik=cik))
            except Exception as error:  # noqa: BLE001 - skip unreachable filers
                print(f"  skip {ticker}: {error}")
                continue
            recent = submissions["filings"]["recent"]
            by_year: dict[int, list[dict]] = defaultdict(list)
            for index, form in enumerate(recent["form"]):
                if form in DEAL_FORMS:
                    filing_date = recent["filingDate"][index]
                    by_year[int(filing_date[:4])].append({
                        "form": form,
                        "filing_date": filing_date,
                        "accession_number": recent["accessionNumber"][index],
                    })
            if not by_year:
                print(f"  {ticker}: no M&A filings")
                continue
            client_id = f"C{cik:07d}"
            company_name = submissions.get("name") or entry["title"]
            clients.append({
                "client_id": client_id,
                "name": company_name,
                "industry": submissions.get("sicDescription") or None,
                "parent_client_id": None,
            })
            for year, filings in sorted(by_year.items()):
                representative = min(
                    filings,
                    key=lambda f: FORM_PRIORITY.index(f["form"])
                    if f["form"] in FORM_PRIORITY else len(FORM_PRIORITY),
                )
                raw_matters.append({
                    "client_id": client_id,
                    "client_name": company_name,
                    "sector": sector,
                    "jurisdiction": submissions.get("stateOfIncorporation"),
                    "sic": submissions.get("sic"),
                    "year": year,
                    "form": representative["form"],
                    "accession_number": representative["accession_number"],
                    "filing_date": representative["filing_date"],
                    "cik": cik,
                    "filings_in_year": len(filings),
                })
            print(f"  {ticker}: {len(by_year)} matter-year(s)")
    return clients, raw_matters


def finalize_matters(raw_matters: list[dict], rng: random.Random) -> list[dict]:
    """Select up to MAX_MATTERS, assign ids and the synthesized fields."""
    selected = raw_matters
    if len(selected) > MAX_MATTERS:
        selected = rng.sample(selected, MAX_MATTERS)
    selected.sort(key=lambda m: (m["client_id"], m["year"]))
    matters: list[dict] = []
    for index, raw in enumerate(selected, start=1):
        # Illustrative deal value, log-uniform across roughly $50M..$80B.
        deal_value = round(10 ** rng.uniform(7.7, 10.9), -6)
        matters.append({
            "matter_id": f"M{index:04d}",
            "name": f"{raw['client_name']} — {DEAL_FORMS[raw['form']]} ({raw['year']})",
            "client_id": raw["client_id"],
            "practice_area": f"{raw['sector']} M&A",
            "deal_type": DEAL_FORMS[raw["form"]],
            "jurisdiction": raw["jurisdiction"],
            "deal_value": deal_value,
            "year": raw["year"],
            "firm_role": rng.choice(FIRM_ROLES),
            "description": (
                f"{raw['client_name']} {DEAL_FORMS[raw['form']].lower()} matter; "
                f"sourced from SEC EDGAR form {raw['form']} "
                f"filed {raw['filing_date']}."
            ),
            "attributes": {
                "edgar_cik": raw["cik"],
                "edgar_form": raw["form"],
                "accession_number": raw["accession_number"],
                "filing_date": raw["filing_date"],
                "filings_in_year": raw["filings_in_year"],
                "sic_code": raw["sic"],
            },
        })
    return matters


def build_timekeepers(rng: random.Random, count: int = 22) -> list[dict]:
    """Generate the fictional firm's timekeepers."""
    pairs = [(first, last) for first in TIMEKEEPER_FIRST for last in TIMEKEEPER_LAST]
    chosen = rng.sample(pairs, count)
    timekeepers: list[dict] = []
    for index, (first, last) in enumerate(chosen, start=1):
        title = TIMEKEEPER_TITLES[index % len(TIMEKEEPER_TITLES)]
        experience = rng.randint(18, 32) if title == "Partner" else rng.randint(2, 14)
        timekeepers.append({
            "timekeeper_id": f"T{index:03d}",
            "name": f"{first} {last}",
            "title": title,
            "practice_group": rng.choice(PRACTICE_GROUPS),
            "years_experience": experience,
        })
    return timekeepers


def build_matter_timekeepers(
    matters: list[dict], timekeepers: list[dict], rng: random.Random,
) -> list[dict]:
    """Staff each matter with two to five timekeepers."""
    rows: list[dict] = []
    for matter in matters:
        team = rng.sample(timekeepers, rng.randint(2, 5))
        for position, member in enumerate(team):
            rows.append({
                "matter_id": matter["matter_id"],
                "timekeeper_id": member["timekeeper_id"],
                "role_on_matter": MATTER_ROLES[min(position, len(MATTER_ROLES) - 1)],
            })
    return rows


def build_parties(
    matters: list[dict], client_names: list[str], rng: random.Random,
) -> list[dict]:
    """Attach real counsel and advisor firms (and a counterparty) per matter.

    Counsel/advisor names are cycled through every real variant so the
    entity-resolution demo has full coverage to reconcile.
    """
    counsel_variants = [(firm[0], variant) for firm in LAW_FIRMS for variant in firm]
    advisor_variants = [
        (firm[0], variant) for firm in FINANCIAL_ADVISORS for variant in firm
    ]
    rng.shuffle(counsel_variants)
    rng.shuffle(advisor_variants)
    parties: list[dict] = []
    party_seq = 0
    counsel_pos = 0
    advisor_pos = 0
    for matter in matters:
        for _ in range(rng.randint(1, 2)):
            _, variant = counsel_variants[counsel_pos % len(counsel_variants)]
            counsel_pos += 1
            party_seq += 1
            parties.append({
                "party_id": f"P{party_seq:04d}",
                "matter_id": matter["matter_id"],
                "raw_name": variant,
                "party_type": "opposing_counsel",
                "side": rng.choice(DEAL_SIDES),
            })
        _, advisor = advisor_variants[advisor_pos % len(advisor_variants)]
        advisor_pos += 1
        party_seq += 1
        parties.append({
            "party_id": f"P{party_seq:04d}",
            "matter_id": matter["matter_id"],
            "raw_name": advisor,
            "party_type": "advisor",
            "side": rng.choice(DEAL_SIDES),
        })
        counterparty = rng.choice(client_names)
        party_seq += 1
        parties.append({
            "party_id": f"P{party_seq:04d}",
            "matter_id": matter["matter_id"],
            "raw_name": counterparty,
            "party_type": "counterparty",
            "side": rng.choice(DEAL_SIDES),
        })
    return parties


def build_tags(
    clients: list[dict], raw_matters: list[dict], matters: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Derive tags (real SIC, jurisdiction, deal form) and matter links."""
    sic_by_client = {m["client_id"]: m["sic"] for m in raw_matters}
    registry: dict[tuple[str, str], str] = {}
    tags: list[dict] = []

    def tag_id(tag_type: str, value: str) -> str:
        key = (tag_type, value)
        if key not in registry:
            registry[key] = f"TAG{len(registry) + 1:03d}"
            tags.append({"tag_id": registry[key], "tag_type": tag_type, "value": value})
        return registry[key]

    matter_tags: list[dict] = []
    for matter in matters:
        links = []
        sic = sic_by_client.get(matter["client_id"])
        if sic:
            links.append(tag_id("industry_code", str(sic)))
        if matter["jurisdiction"]:
            links.append(tag_id("governing_law", matter["jurisdiction"]))
        links.append(tag_id("deal_subtype", matter["attributes"]["edgar_form"]))
        for tid in links:
            matter_tags.append({"matter_id": matter["matter_id"], "tag_id": tid})
    return tags, matter_tags


def write_fixtures(name: str, rows: list[dict]) -> None:
    path = FIXTURES_DIR / f"{name}.json"
    path.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"  wrote {path.relative_to(REPO_ROOT)} ({len(rows)} rows)")


def main() -> None:
    rng = random.Random(SEED)
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Fictional firm: {FIRM_NAME}")
    print("Fetching EDGAR ticker index...")
    ticker_index = fetch_ticker_index()
    print("Harvesting M&A filings from EDGAR submissions...")
    clients, raw_matters = harvest_from_edgar(ticker_index)
    matters = finalize_matters(raw_matters, rng)
    timekeepers = build_timekeepers(rng)
    matter_timekeepers = build_matter_timekeepers(matters, timekeepers, rng)
    client_names = [c["name"] for c in clients]
    parties = build_parties(matters, client_names, rng)
    tags, matter_tags = build_tags(clients, raw_matters, matters)

    print("Writing fixtures:")
    write_fixtures("clients", clients)
    write_fixtures("matters", matters)
    write_fixtures("timekeepers", timekeepers)
    write_fixtures("matter_timekeepers", matter_timekeepers)
    write_fixtures("parties", parties)
    write_fixtures("tags", tags)
    write_fixtures("matter_tags", matter_tags)

    practice_areas = sorted({m["practice_area"] for m in matters})
    print(f"\nDone: {len(clients)} clients, {len(matters)} matters, "
          f"{len(practice_areas)} practice areas {practice_areas}.")


if __name__ == "__main__":
    main()
