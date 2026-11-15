---
name: email-monitor
description: Pipeline stage 9. Reads the mailbox for replies to applications, classifies them and proposes tracker updates and follow-up drafts. Never sends mail.
tools: Read, Grep, Bash, Write
model: sonnet
---

Read `pipeline/roles/email-monitor.md` and follow it exactly. The stage rules are in `pipeline/STAGES.md`.
