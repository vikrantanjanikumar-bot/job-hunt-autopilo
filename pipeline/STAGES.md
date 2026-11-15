# Job application pipeline

Thirteen stages (0-12). Each has one bot (role brief in `pipeline/roles/`), one input, one output and a
gate that must pass before the next stage. The candidate's facts and standing rules are in
`CLAUDE.md`; the live queue is in `RUN_STATE.md`. Never invent a fact: what is not in
`CLAUDE.md` or the resume is asked once and then written into `CLAUDE.md`.

| # | Stage | Bot | Output | Gate to pass |
|---|---|---|---|---|
| 0 | Set up (once) | main session | `CLAUDE.md` facts, resume content file, tracker sheet, search config | candidate has approved the resume wording |
| 1 | Hunt | `job-hunter` | `discovery/shortlist_<date>.csv`, `descriptions_<date>.json` | postings are new (not in `tools/tracker_index.csv`) |
| 2 | Categorise | `job-hunter` | category per posting: role family, region, seniority, portal type | IT, sales, site-construction and junior titles dropped |
| 3 | Log | main session | one tracker row per kept posting, stage `Discovery - to read` | row checked by Job ID before any later edit |
| 4 | Verify and match score | `fit-scorer` | posting checked on the employer's own site (still open, real employer, not a duplicate of a tracker row, no fee or 'pay to apply'); fit 0-100, blockers, resume variant, JD saved to `discovery/jd/<JobID>_<Employer>.txt` | open and genuine; fit above 50 and no honest blocker; else stage `Skipped` with the reason |
| 5 | Documents | `resume-tailor`, `cover-letter-writer` | `uploads/..._Resume_<slug>_<date>.pdf` (2 pages), `..._Cover_Letter_<date>.pdf` (1 page) | page counts right; no claim outside approved wording |
| 6 | Fill | `form-filler` (the only bot that touches the browser; one at a time) | answer sheet `discovery/answers/<JobID>.md`, then the form filled and saved page by page up to, not including, submit | stops at logins, OTPs, account creation, e-signatures |
| 7 | Review | `application-reviewer` | `tools/review_check.py` on the review page text, then a check by eye of screening answers against the answer sheet | zero mismatches; importer-made rows removed |
| 8 | Apply and update | main session | submit; tracker stage `Submitted (<confirmation text>, <date>)`, resume file in column N, date in column O | a confirmation page or email exists |
| 9 | Monitor | `email-monitor` | replies classified: acknowledgement, rejection, assessment, recruiter, interview; tracker updated; follow-up drafts | a person's reply is told to the candidate first |
| 10 | Interview prep | main session (`interview-prep` skill) | one-file pack: company brief, likely questions, answers as stories, salary line | built the day an interview or recruiter call is confirmed |
| 11 | Learn | `outcome-analyst` | weekly: replies per source, per resume variant, per role family; what to search more or drop | changes to search words or scoring are proposed, not applied silently |
| 12 | Profile refresh (weekly) | `profile-refresher` | job-board and network profiles match the approved text; current resume uploaded; one activity edit per site | every changed section read back; nothing outside approved wording |

## Tracker stage values (column L)

`Discovery - to read` -> `Discovery - scored` -> `Documents ready` -> `In progress - <what is
waiting>` -> `Submitted (...)` -> `Response - <type> (...)` / `Rejected (...)` / `Skipped - <reason>`.

## Commands

```
python -I tools\discover.py --hours 48                      # stages 1-2
python -I tools\linkedin_jd.py <id> <id> ...                # LinkedIn descriptions
python -I tools\tailor_resume.py discovery\jd\<file>.txt <controls|npi|defence> <Employer_Role>
python -I tools\cover_letter.py <letters.json>              # 1 page each
```

## Rules that hold in every stage

- Truthful always. No certificate, tool, degree or domain years the candidate does not hold.
- Resume tailoring only reorders approved skills and bullets. New wording needs approval.
- One browser worker at a time. Search and scoring bots never open the browser.
- A form is "filled" only after every page has been read back (stage 7). Resume importers
  split one employer into fake jobs and mislabel degrees: always open the experience page.
- Consents, account creation, passwords and one-time codes follow the rules in `CLAUDE.md`.
- `Submitted` is written only with a confirmation. Portal acknowledgements are not responses.
- Stage 9 reads mail; it drafts follow-ups and never sends.

## Running it

Whole pipeline: stages 1-4 in parallel bots (no browser), then stages 5-8 one job at a time
in fit order (deadlines first), then stage 9. Stage 11 and stage 12 run once a week;
stage 12 needs the browser, so not while a form is being filled. A single stage can be run alone by naming it.
After a run: append to `RUN_STATE.md`, add new rows to `tools/tracker_index.csv`, commit.

## Token and session rules for stages 6-8 (15 Nov 2026)

Three form runs were lost to the usage limit and expired sign-ins. These rules prevent that.

- **Usage gate.** Before asking the candidate to sign in or starting `form-filler`, read the plan usage (`get_usage`). Start a form only when the 5-hour window is at most 60% used; otherwise do stages 1-5, 9 and 11 (no browser) and queue the form for the next window.
- **Answer sheet first.** `python -I tools/answer_sheet.py <JobID> <Employer> <Role> <portal> <resume.pdf> [cover.pdf] [--abroad] [--consent] [--url <link>]` writes `discovery/answers/<JobID>.md`. The form-filler brief is three lines: Job ID, the sheet's path, the tab id. Do not paste facts into the brief.
- **Never resume a cut-off bot.** Resuming replays its whole history (about 100,000 tokens). Start a fresh `form-filler`; the saved draft and the sheet are its memory.
- **Save every page.** A break then loses one page at most.
- **One sign-in, all jobs on that portal.** Queue forms by portal so each sign-in is used for every waiting job there.
- **Review by script.** `application-reviewer` saves the review page text and runs `python -I tools/review_check.py <JobID> discovery/review/<JobID>.txt`; the model reads only what the script cannot judge.
- **Models.** `job-hunter` and `email-monitor` run on the cheaper model (set in their files). Scoring, letters and review stay on the strongest. `form-filler` on the cheaper model is a trial: pass `model: sonnet` for one form and compare the reviewer's result before making it the default.
- Facts live twice: prose in `CLAUDE.md`, machine copy in `tools/form_facts.json`. A new answer from the candidate goes into both.
