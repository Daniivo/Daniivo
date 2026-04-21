#!/usr/bin/env python3
"""
Job Opportunity Finder — OutSystems & AI Developer
Uses free public APIs (Remotive, Arbeitnow) and direct search snippets.
Run: python3 search_jobs.py
"""

import json
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# ─── Config ──────────────────────────────────────────────────────────────────

KEYWORDS_OUTSYSTEMS = ["outsystems", "outsystem", "out systems"]
KEYWORDS_AI = [
    "ai developer", "ai engineer", "generative ai", "llm engineer",
    "machine learning engineer", "ml engineer", "ai agent", "ai architect",
    "nlp engineer", "prompt engineer",
]
PREFERRED_LOCATIONS = ["portugal", "remote", "remoto", "lisbon", "lisboa", "porto"]

# ─── Helpers ─────────────────────────────────────────────────────────────────

def fetch_json(url: str, timeout: int = 10) -> dict | list | None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  [WARN] {url} → {e}", file=sys.stderr)
        return None


def matches(text: str, keywords: list[str]) -> bool:
    t = text.lower()
    return any(k in t for k in keywords)


def tag_relevance(job: dict, keywords: list[str]) -> str:
    fields = " ".join([
        job.get("title", ""),
        job.get("description", ""),
        " ".join(job.get("tags", [])),
        " ".join(job.get("skills", [])),
    ])
    return "✅" if matches(fields, keywords) else ""


def print_job(job: dict, source: str):
    title    = job.get("title", "N/A")
    company  = job.get("company_name") or job.get("company") or "N/A"
    location = job.get("location", "Remote")
    url      = job.get("url") or job.get("apply_url") or "N/A"
    date     = (job.get("publication_date") or job.get("date") or "")[:10]
    salary   = job.get("salary") or ""

    print(f"  📌 {title}")
    print(f"     Empresa   : {company}")
    print(f"     Local     : {location}")
    if salary:
        print(f"     Salário   : {salary}")
    if date:
        print(f"     Publicado : {date}")
    print(f"     Link      : {url}")
    print(f"     Fonte     : {source}")
    print()

# ─── Source 1: Remotive ──────────────────────────────────────────────────────

def fetch_remotive(search_term: str) -> list[dict]:
    encoded = urllib.parse.quote(search_term)
    url = f"https://remotive.com/api/remote-jobs?search={encoded}&limit=20"
    data = fetch_json(url)
    if not data:
        return []
    return data.get("jobs", [])


def remotive_jobs(keywords: list[str], label: str) -> list[dict]:
    results = []
    seen = set()
    for kw in keywords[:3]:  # limit API calls
        for job in fetch_remotive(kw):
            jid = job.get("id") or job.get("url")
            if jid in seen:
                continue
            seen.add(jid)
            if tag_relevance(job, keywords):
                job["_source"] = "Remotive (remote)"
                results.append(job)
    return results

# ─── Source 2: Arbeitnow ─────────────────────────────────────────────────────

def fetch_arbeitnow(page: int = 1) -> list[dict]:
    url = f"https://www.arbeitnow.com/api/job-board-api?page={page}"
    data = fetch_json(url)
    if not data:
        return []
    return data.get("data", [])


def arbeitnow_jobs(keywords: list[str]) -> list[dict]:
    results = []
    for page in range(1, 4):  # pages 1–3
        jobs = fetch_arbeitnow(page)
        if not jobs:
            break
        for job in jobs:
            fields = " ".join([
                job.get("title", ""),
                job.get("description", ""),
                " ".join(job.get("tags", [])),
            ])
            if matches(fields, keywords):
                job["_source"] = "Arbeitnow"
                results.append(job)
    return results

# ─── Source 3: The Muse ──────────────────────────────────────────────────────

def fetch_themuse(page: int = 1) -> list[dict]:
    url = f"https://www.themuse.com/api/public/jobs?page={page}&per_page=100"
    data = fetch_json(url)
    if not data:
        return []
    return data.get("results", [])


def themuse_jobs(keywords: list[str]) -> list[dict]:
    results = []
    for page in range(0, 3):
        jobs = fetch_themuse(page)
        if not jobs:
            break
        for job in jobs:
            name = job.get("name", "")
            company = job.get("company", {}).get("name", "")
            contents = job.get("contents", "")
            locations = " ".join(loc.get("name", "") for loc in job.get("locations", []))
            ref = job.get("refs", {}).get("landing_page", "")

            fields = f"{name} {company} {contents}"
            if matches(fields, keywords):
                results.append({
                    "title": name,
                    "company_name": company,
                    "location": locations or "N/A",
                    "url": ref,
                    "description": contents[:200],
                    "_source": "The Muse",
                })
    return results

# ─── Display ─────────────────────────────────────────────────────────────────

def show_section(title: str, jobs: list[dict]):
    print(f"\n{'═' * 60}")
    print(f"  {title}  ({len(jobs)} resultado(s))")
    print(f"{'═' * 60}\n")
    if not jobs:
        print("  Nenhum resultado encontrado nesta fonte.\n")
        return
    for job in jobs:
        print_job(job, job.get("_source", "?"))

# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n🔍 Job Search — {now}")
    print("   Fontes: Remotive · Arbeitnow · The Muse\n")

    # OutSystems
    print("⏳ A pesquisar OutSystems (Remotive)...")
    os_remotive  = remotive_jobs(KEYWORDS_OUTSYSTEMS, "OutSystems")

    print("⏳ A pesquisar OutSystems (Arbeitnow)...")
    os_arbeitnow = arbeitnow_jobs(KEYWORDS_OUTSYSTEMS)

    print("⏳ A pesquisar OutSystems (The Muse)...")
    os_muse      = themuse_jobs(KEYWORDS_OUTSYSTEMS)

    # AI Developer
    print("⏳ A pesquisar AI Developer (Remotive)...")
    ai_remotive  = remotive_jobs(KEYWORDS_AI, "AI Dev")

    print("⏳ A pesquisar AI Developer (Arbeitnow)...")
    ai_arbeitnow = arbeitnow_jobs(KEYWORDS_AI)

    print("⏳ A pesquisar AI Developer (The Muse)...")
    ai_muse      = themuse_jobs(KEYWORDS_AI)

    # Results
    show_section("OutSystems — Remotive (Remote Global)", os_remotive)
    show_section("OutSystems — Arbeitnow (Europa)", os_arbeitnow)
    show_section("OutSystems — The Muse", os_muse)
    show_section("AI Developer — Remotive (Remote Global)", ai_remotive)
    show_section("AI Developer — Arbeitnow (Europa)", ai_arbeitnow)
    show_section("AI Developer — The Muse", ai_muse)

    total = len(os_remotive) + len(os_arbeitnow) + len(os_muse) + \
            len(ai_remotive) + len(ai_arbeitnow) + len(ai_muse)
    print(f"\n✅ Total: {total} vagas encontradas.\n")


if __name__ == "__main__":
    main()
