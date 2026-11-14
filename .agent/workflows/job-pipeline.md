---
description: Run the job application pipeline - hunt, score, tailor documents, fill, review, apply, monitor
---

1. Read `AGENTS.md`, `CLAUDE.md` and `pipeline/STAGES.md`. If `CLAUDE.md` is missing, copy `CLAUDE.template.md` to `CLAUDE.md`, ask the candidate to fill it in, and stop.
2. Hunt and categorise: follow `pipeline/roles/job-hunter.md`.
3. Verify and score each kept posting: follow `pipeline/roles/fit-scorer.md` and `docs/FIT_SCORING.md`. Log every posting to the tracker.
4. For each posting with fit above 50 and no blocker, highest first: build the resume (`pipeline/roles/resume-tailor.md`) and the cover letter (`pipeline/roles/cover-letter-writer.md`).
5. Fill the application form in the browser without submitting: follow `pipeline/roles/form-filler.md` and `docs/PORTAL_NOTES.md`. Stop at sign-ins, one-time codes, account creation and signatures.
6. Review every page: follow `pipeline/roles/application-reviewer.md`. Fix every mismatch and review again.
7. Submit only after the review passes and the consent rule in `CLAUDE.md` allows it. Record the confirmation text and date in the tracker.
8. Monitor replies: follow `pipeline/roles/email-monitor.md`. Tell the candidate about any reply from a person first.
9. Report: what was submitted with its confirmation, what is waiting on the candidate, what was skipped and why.
10. Once a week: refresh job-board profiles by following `pipeline/roles/profile-refresher.md`.
