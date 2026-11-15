# Job hunt autopilot

A working setup that lets an AI coding agent run a job search end to end. **Built for and
used with [Claude Code](https://claude.com/claude-code); experimental support for OpenAI
Codex and Google Antigravity.** What it does: find postings, score them against your profile, build a tailored résumé and cover
letter, fill the employer's form, check it, submit, and watch your mailbox for replies.

It was built and used on a real search. Everything personal has been removed; you add your
own facts in two files.

## The stages

| # | Stage | Bot | What you get |
|---|---|---|---|
| 0 | Set up (once) | you + Claude | your facts file, résumé content, tracker sheet, search words |
| 1 | Hunt | `job-hunter` | new postings from Naukri, Indeed, Glassdoor and LinkedIn |
| 2 | Categorise | `job-hunter` | role family, region, seniority; noise dropped |
| 3 | Log | main session | one row per posting in your tracker sheet |
| 4 | Verify and match score | `fit-scorer` | posting confirmed open and genuine; fit out of 100 with honest blockers |
| 5 | Documents | `resume-tailor`, `cover-letter-writer` | 2-page résumé and 1-page letter per job |
| 6 | Fill | `form-filler` | a one-page answer sheet per job, then the portal form filled and saved page by page, stopped before submit |
| 7 | Review | `application-reviewer` | review page text compared with the sheet by script, then a check by eye of the screening answers |
| 8 | Apply and update | main session | submitted, with the confirmation text in the tracker |
| 9 | Monitor | `email-monitor` | replies classified, deadlines flagged, follow-ups drafted |
| 10 | Interview prep | main session | a one-file pack per interview |
| 11 | Learn | `outcome-analyst` | which sources and résumé versions get replies |
| 12 | Profile refresh (weekly) | `profile-refresher` | job-board profiles kept current and "recently active" |

The full rules are in [`pipeline/STAGES.md`](pipeline/STAGES.md).

## Which tools it works with

| Tool | What it reads | Status |
|---|---|---|
| Claude Code | `CLAUDE.md`, `.claude/skills/`, `.claude/agents/` | **supported** - built and used on a real search |
| OpenAI Codex | `AGENTS.md` | **experimental** - written, not yet run by the authors |
| Google Antigravity | `AGENTS.md`, `.agent/rules/`, `.agent/workflows/job-pipeline.md` (run with `/job-pipeline`) | **experimental** - written, not yet run by the authors |

All three follow the same tool-neutral files: `pipeline/STAGES.md` (the stages and gates)
and `pipeline/roles/` (one brief per bot). The Python tools are the same for all three. Where a tool has no sub-agents, browser, sheet
or mail connector, `AGENTS.md` says what to do instead (play the roles in turn, write a fill
sheet for the candidate, keep `tracker.csv`, paste replies). Reports and fixes from Codex and
Antigravity users are welcome as issues.

## What you need

- One agent tool: Claude Code (with the Claude in Chrome extension for stage 6), Codex, or Antigravity.
- Python 3.10+ and: `pip install python-jobspy==1.4.1 reportlab pypdf requests beautifulsoup4`
- Connectors, if you want stages 3 and 9 automated: Google Sheets and Gmail (or do those by hand).
- Windows fonts Tahoma are used by the PDF builders; change the two font lines in
  `tools/resume.py` and `tools/cover_letter.py` on other systems.

## Set up (stage 0)

1. Copy `CLAUDE.template.md` to `CLAUDE.md` and fill in your facts and rules.
2. Copy `tools/resume_content.example.json` to `tools/resume_content.json` and write your
   résumé there: up to three variants (headline, profile, skills) over one shared history.
   Build them: `python -I tools/resume.py tools/resume_content.json uploads _<date>` — each
   must come out at 2 pages.
3. Copy `tools/form_facts.example.json` to `tools/form_facts.json` and fill it in: the machine copy of your form facts. It feeds the per-job answer sheet and the review check. When you give a new answer, record it here and in `CLAUDE.md`.
4. Copy `tools/discover_config.example.json` to `tools/discover_config.json` and set your
   search terms, locations and the words that raise or lower a posting's reading order.
5. Create a tracker sheet with the columns listed in `CLAUDE.template.md`, and an empty
   `tools/tracker_index.csv` (one line per job: `J001|Employer|Role`).
6. Open the folder in your agent tool and say: **run the pipeline** (Antigravity: `/job-pipeline`).

## Keeping token use down

Forms are the expensive stage. These rules came from runs that were cut off by a usage limit:

- **Usage gate:** start a form only when the current usage window has room (the rule uses 60% used as the limit). Do the no-browser stages first.
- **Answer sheet:** `tools/answer_sheet.py` builds one small sheet per job from `tools/form_facts.json`; the form bot reads that, not your whole facts file.
- **Scripted review:** `tools/review_check.py` compares the review page text with the sheet and prints only what is missing, forbidden or worth a look.
- **Fresh bot, never resumed:** resuming a cut-off bot replays its whole history. Save each page as it is verified so a break loses one page at most.
- **Per-portal notes:** a bot reads only its portal's section of the portal notes.
- **Log and budgets:** record every bot run in `tools/bot_usage.csv` and compare with the budgets in `pipeline/STAGES.md`.
- **Cheaper model for mechanical bots:** the hunter and the mail monitor run on a smaller model; scoring, letters and review stay on the strongest.

## Rules built into it

- **Truthful always.** No certificate, tool, degree or years of experience you do not hold.
  A question the facts file cannot answer is asked once, then recorded.
- **Tailoring never invents.** `tailor_resume.py` only reorders skills and bullets you approved,
  and lists the job's keywords your résumé lacks so you can decide what is true.
- **You keep the keys.** The bots never type passwords or one-time codes and never create
  accounts. Consents and signatures are yours unless you say otherwise in `CLAUDE.md`.
- **Checked before sent.** Résumé importers on job portals split one employer into several
  fake jobs and mislabel degrees; stage 7 reads every page back before submit.
- **One browser worker.** Search and scoring run in parallel; form filling runs alone.
- **Polite searching.** Low volume, no retry loops, no getting round blocks. Job sites'
  terms may restrict automated access; check them for the sites you use.

## Files

```
pipeline/STAGES.md                     the pipeline: stages, gates, commands (all tools)
pipeline/roles/*.md                    one brief per bot (all tools)
AGENTS.md                              entry point for Codex, Antigravity and other agents
.agent/                                Antigravity rules and workflow
.claude/                               Claude Code skill and agents (thin wrappers)
tools/discover.py                      search and de-duplicate (JobSpy)
tools/linkedin_jd.py                   read public LinkedIn job descriptions
tools/resume.py                        build 2-page résumé variants (PDF)
tools/tailor_resume.py                 per-job résumé from approved wording
tools/cover_letter.py                  one-page cover letters (PDF)
tools/answer_sheet.py                  per-job answer sheet for the form bot
tools/review_check.py                  scripted comparison of the review page with the sheet
tools/form_facts.example.json          machine copy of your form facts
docs/FIT_SCORING.md                    how the match score is built
docs/PORTAL_NOTES.md                   what each kind of job portal does
CLAUDE.template.md                     your facts and standing rules
```

## Licence

MIT. No warranty: you are responsible for every application sent in your name.
