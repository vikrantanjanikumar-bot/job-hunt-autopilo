"""Find fresh job postings for the candidate and write a ranked shortlist.

Run with the JobSpy environment (outside OneDrive):
    python -I tools\\discover.py

Options:
    --hours N         look back N hours (default: hours_old in discover_config.json)
    --sites a,b       only these sites (indeed, naukri, linkedin)
    --max-searches N  stop after N searches (for a quick test)
    --all             list postings already shown in an earlier shortlist too

What it does: runs the searches in tools\\discover_config.json through JobSpy, drops
titles that are clearly not project/programme/planning roles, gives each posting a
rough 0-100 pre-score (title, location, employer, domain words, freshness), removes
postings that look like rows already in the tracker (tools\\tracker_index.csv) and
writes discovery\\shortlist_<date>.md and .csv.

The pre-score only orders the reading list. "Fit above 50" is still decided by
reading the job description. Sites' terms may restrict automated searching, so the
search list is kept small and paced; do not raise the volume.
"""
import argparse
import csv
import datetime as dt
import difflib
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
OUT = ROOT / "discovery"
STOP = {"ltd", "limited", "pvt", "private", "india", "inc", "llc", "group", "the", "co",
        "company", "corporation", "corp", "and", "llp", "plc", "gmbh"}


def say(text):
    print(str(text).encode("ascii", "replace").decode(), flush=True)


def norm(text):
    text = re.sub(r"[^a-z0-9 ]+", " ", str(text or "").lower())
    return re.sub(r"\s+", " ", text).strip()


def norm_company(text):
    return " ".join(w for w in norm(text).split() if w not in STOP)


def clean(value):
    """Turn NaN/None into an empty string."""
    if value is None:
        return ""
    text = str(value)
    return "" if text.lower() in ("nan", "nat", "none") else text.strip()


def hits(words, padded):
    return [w for w in words if w in padded]


MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def parse_posted(text, today):
    """'2026-11-10', '10 Nov', 'Posted 9 days ago', '18 hrs ago', 'today' -> date or None."""
    t = text.lower()
    if not t:
        return None
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", t)
    if m:
        return dt.date(int(m[1]), int(m[2]), int(m[3]))
    if re.search(r"today|just now|\d+\s*(hr|hour|min)", t):
        return today
    m = re.search(r"(\d+)\+?\s*day", t)
    if m:
        return today - dt.timedelta(days=int(m[1]))
    m = re.search(r"(\d+)\+?\s*week", t)
    if m:
        return today - dt.timedelta(weeks=int(m[1]))
    m = re.search(r"(\d{1,2})\s*([a-z]{3})", t)
    if m and m[2] in MONTHS:
        d = dt.date(today.year, MONTHS[m[2]], int(m[1]))
        return d if d <= today else d.replace(year=today.year - 1)
    return None


def load_tracker():
    rows = []
    path = TOOLS / "tracker_index.csv"
    if path.exists():
        with path.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh, delimiter="|"):
                rows.append((row["job"], norm_company(row["employer"]), norm(row["role"])))
    return rows


def in_tracker(company, title, tracker):
    comp, ttl = norm_company(company), norm(title)
    if not comp or not ttl:
        return ""
    for job, t_comp, t_ttl in tracker:
        same_comp = comp == t_comp or (
            min(len(comp), len(t_comp)) >= 3
            and (f" {comp} " in f" {t_comp} " or f" {t_comp} " in f" {comp} "))
        if not same_comp:
            continue
        if ttl == t_ttl or (min(len(ttl), len(t_ttl)) >= 8 and (ttl in t_ttl or t_ttl in ttl)) \
                or difflib.SequenceMatcher(None, ttl, t_ttl).ratio() >= 0.8:
            return job
    return ""


def score(title, company, location, description, posted, cfg, today):
    """Return (score, reasons) or (None, why_dropped)."""
    t = f" {title.lower()} "
    c = f" {company.lower()} "
    loc = f" {location.lower()} "
    if hits(cfg["current_employer"], c):
        return None, "current employer"
    bad = hits(cfg["title_exclude"], t)
    if bad:
        return None, f"excluded title word: {bad[0].strip()}"
    reasons = []
    if hits(cfg["title_core"], t):
        pts = 40
        reasons.append("core title")
    elif hits(cfg["title_adjacent"], t):
        pts = 25
        reasons.append("adjacent title")
    else:
        return None, "title not a project/programme/planning role"
    if hits(cfg["title_junior"], t):
        pts -= 15
        reasons.append("junior wording")
    elif hits(cfg["title_senior"], t):
        pts += 8
    for value, places in cfg["location_scores"]:
        if hits(places, loc):
            pts += value
            if value >= 20:
                reasons.append("Home area" if value >= 25 else "Gujarat")
            elif value >= 14:
                reasons.append("Mumbai/Pune/Gulf")
            break
    if hits(cfg["priority_employers"], c):
        pts += 12
        reasons.append("priority employer")
    words = hits(cfg["domain_words"], f" {title.lower()} {description[:4000].lower()} ")
    if words:
        pts += min(12, 3 * len(words))
        reasons.append("domain: " + ", ".join(words[:3]))
    if posted:
        age = (today - posted).days
        pts += 8 if age <= 1 else 5 if age <= 3 else 2 if age <= 7 else 0
    return max(0, min(100, pts)), "; ".join(reasons)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int)
    ap.add_argument("--sites", default="")
    ap.add_argument("--max-searches", type=int, default=0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--extra", action="append", default=[],
                    help="JSON list of postings read by Firecrawl (Foundit, NaukriGulf); "
                         "keys site, title, company, location, posted, url, description")
    ap.add_argument("--extra-only", action="store_true", help="skip the JobSpy searches")
    ap.add_argument("--international", action="store_true",
                    help="also run international_searches (Nordics, Netherlands, Switzerland, ...)")
    args = ap.parse_args()

    import pandas as pd
    from jobspy import scrape_jobs

    cfg = json.loads((TOOLS / "discover_config.json").read_text(encoding="utf-8"))
    hours = args.hours or cfg["hours_old"]
    sites = {s.strip().lower() for s in args.sites.split(",") if s.strip()}
    pool = cfg["searches"] + (cfg.get("international_searches", []) if args.international else [])
    searches = [s for s in pool if not sites or s["site"] in sites]
    if args.max_searches:
        searches = searches[:args.max_searches]
    if args.extra_only:
        searches = []
    today = dt.date.today()
    tracker = load_tracker()
    OUT.mkdir(exist_ok=True)
    seen_path = OUT / "seen.json"
    seen = json.loads(seen_path.read_text(encoding="utf-8")) if seen_path.exists() else {}

    found, failures, fails_by_site = {}, [], {}
    for i, s in enumerate(searches, 1):
        site = s["site"]
        if fails_by_site.get(site, 0) >= 2:
            failures.append(f"{site}: skipped '{s['term']}' / {s['location']} (site failed twice)")
            continue
        kw = dict(site_name=[site], search_term=s["term"], location=s["location"],
                  results_wanted=cfg["results_per_search"], hours_old=hours, verbose=0)
        if site in ("indeed", "glassdoor"):
            kw["country_indeed"] = s.get("country", "india")
        try:
            df = scrape_jobs(**kw)
            fails_by_site[site] = 0
        except Exception as exc:  # noqa: BLE001 - keep going with the other searches
            fails_by_site[site] = fails_by_site.get(site, 0) + 1
            failures.append(f"{site}: '{s['term']}' / {s['location']}: {type(exc).__name__}: {str(exc)[:120]}")
            say(f"[{i}/{len(searches)}] {site:8} {s['term']} / {s['location']}: FAILED")
            time.sleep(cfg["pause_seconds"])
            continue
        say(f"[{i}/{len(searches)}] {site:8} {s['term']} / {s['location']}: {len(df)} rows")
        for _, r in df.iterrows():
            url = clean(r.get("job_url"))
            if url and url not in found:
                posted = pd.to_datetime(r.get("date_posted"), errors="coerce")
                found[url] = dict(
                    site=site, url=url, title=clean(r.get("title")), company=clean(r.get("company")),
                    location=clean(r.get("location")), description=clean(r.get("description")),
                    posted=None if pd.isna(posted) else posted.date(), search=f"{s['term']} / {s['location']}")
        time.sleep(cfg["pause_seconds"])

    for extra in args.extra:
        rows = json.loads(Path(extra).read_text(encoding="utf-8"))
        say(f"extra {Path(extra).name}: {len(rows)} postings")
        for r in rows:
            url = clean(r.get("url"))
            if url and url not in found:
                found[url] = dict(site=clean(r.get("site")) or "extra", url=url, title=clean(r.get("title")),
                                  company=clean(r.get("company")), location=clean(r.get("location")),
                                  description=clean(r.get("description")),
                                  posted=parse_posted(clean(r.get("posted")), today),
                                  search=clean(r.get("search")) or Path(extra).name)

    kept, dropped, dupes, seen_before, by_key = [], {}, [], 0, set()
    for job in found.values():
        pts, why = score(job["title"], job["company"], job["location"], job["description"],
                         job["posted"], cfg, today)
        if pts is None:
            dropped[why.split(":")[0]] = dropped.get(why.split(":")[0], 0) + 1
            continue
        key = (norm_company(job["company"]), norm(job["title"]))
        if key in by_key:
            continue
        by_key.add(key)
        job.update(score=pts, why=why)
        match = in_tracker(job["company"], job["title"], tracker)
        if match:
            job["tracker"] = match
            dupes.append(job)
            continue
        if not args.all and seen.get(job["url"], str(today)) != str(today):
            seen_before += 1
            continue
        seen.setdefault(job["url"], str(today))
        kept.append(job)
    kept.sort(key=lambda j: (-j["score"], j["company"].lower()))
    seen_path.write_text(json.dumps(seen, indent=0), encoding="utf-8")

    stamp = today.isoformat()
    with (OUT / f"shortlist_{stamp}.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["score", "title", "company", "location", "posted", "site", "why", "url", "found by search"])
        for j in kept:
            w.writerow([j["score"], j["title"], j["company"], j["location"], j["posted"] or "",
                        j["site"], j["why"], j["url"], j["search"]])

    # Descriptions (Naukri and Indeed supply them; LinkedIn does not) for the fit-ranking read.
    (OUT / f"descriptions_{stamp}.json").write_text(json.dumps(
        [dict(score=j["score"], title=j["title"], company=j["company"], location=j["location"],
              site=j["site"], url=j["url"], posted=str(j["posted"] or ""), description=j["description"])
         for j in kept], ensure_ascii=False, indent=1), encoding="utf-8")

    top = kept[:cfg["shortlist_size"]]
    lines = [f"# Discovery shortlist - {stamp}", "",
             f"{len(searches)} searches, last {hours} hours: {len(found)} postings found, "
             f"{len(kept)} new and relevant by title, {len(dupes)} probably already in the tracker, "
             f"{seen_before} shown in an earlier shortlist.", "",
             "The score only orders the reading list (title, location, employer, domain words, "
             "freshness). Read the job description before deciding fit above 50.", "",
             "| Score | Role | Employer | Location | Posted | Site | Why |", "|---|---|---|---|---|---|---|"]
    for j in top:
        role = j["title"].replace("|", "/")
        lines.append(f"| {j['score']} | [{role}]({j['url']}) | {j['company'].replace('|', '/') or '-'} | "
                     f"{j['location'].replace('|', '/') or '-'} | {j['posted'] or '-'} | {j['site']} | {j['why']} |")
    if len(kept) > len(top):
        lines += ["", f"{len(kept) - len(top)} more, lower-scored, are in shortlist_{stamp}.csv."]
    if dupes:
        lines += ["", "## Probably already in the tracker (check the Job ID row before skipping)", ""]
        lines += [f"- {j['tracker']}: {j['title']} - {j['company']} ({j['site']})" for j in dupes[:30]]
    if dropped:
        lines += ["", "## Dropped by title", ""] + [f"- {k}: {v}" for k, v in sorted(dropped.items())]
    if failures:
        lines += ["", "## Searches that failed", ""] + [f"- {f}" for f in failures]
    (OUT / f"shortlist_{stamp}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    say(f"\n{len(found)} found, {len(kept)} new and relevant, {len(dupes)} in tracker, "
        f"{seen_before} seen before, {len(failures)} failed searches")
    for j in top[:15]:
        say(f"  {j['score']:3} | {j['title'][:55]} | {j['company'][:28]} | {j['location'][:28]} | {j['site']}")
    say(f"Shortlist: {OUT / ('shortlist_' + stamp + '.md')}")


if __name__ == "__main__":
    main()
