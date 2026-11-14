"""Fetch the public description of a few LinkedIn job postings (guest page, no login).

    python -I tools\\linkedin_jd.py 4472255632 4480940430 ...

Writes discovery\\linkedin_jd_<date>.json (id, title, company, location, criteria,
description). Paced at one request every 4 seconds; keep the list short (15 or so).
LinkedIn's terms may restrict automated access; this reads only public guest pages.
"""
import datetime as dt
import json
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

OUT = Path(__file__).resolve().parent.parent / "discovery"
URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{}"
HEAD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}


def text(node):
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)) if node else ""


def main(ids):
    OUT.mkdir(exist_ok=True)
    rows = []
    for i, job_id in enumerate(ids):
        if i:
            time.sleep(4)
        try:
            r = requests.get(URL.format(job_id), headers=HEAD, timeout=20)
        except requests.RequestException as exc:
            rows.append(dict(id=job_id, error=type(exc).__name__))
            continue
        if r.status_code != 200:
            rows.append(dict(id=job_id, error=f"HTTP {r.status_code}"))
            print(f"{job_id}: HTTP {r.status_code}")
            if r.status_code == 429:
                break
            continue
        s = BeautifulSoup(r.text, "html.parser")
        crit = {text(li.find("h3")): text(li.find("span")) for li in s.select("li.description__job-criteria-item")}
        row = dict(id=job_id,
                   title=text(s.select_one(".top-card-layout__title")),
                   company=text(s.select_one(".topcard__org-name-link")) or text(s.select_one(".topcard__flavor")),
                   location=text(s.select_one(".topcard__flavor--bullet")),
                   posted=text(s.select_one(".posted-time-ago__text")),
                   applicants=text(s.select_one(".num-applicants__caption")),
                   criteria=crit,
                   description=text(s.select_one(".show-more-less-html__markup"))[:6000])
        rows.append(row)
        print(f"{job_id}: {row['title'][:60]} | {row['company'][:30]} | {len(row['description'])} chars"
              .encode("ascii", "replace").decode())
    path = OUT / f"linkedin_jd_{dt.date.today().isoformat()}.json"
    old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    keep = {r["id"]: r for r in old + rows}
    path.write_text(json.dumps(list(keep.values()), ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Saved {len(rows)} to {path}")


if __name__ == "__main__":
    main([a for a in sys.argv[1:] if a.isdigit()])
