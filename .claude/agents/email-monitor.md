---
name: email-monitor
description: Pipeline stage 9. Reads the mailbox for replies to applications, classifies them and proposes tracker updates and follow-up drafts. Never sends mail.
tools: Read, Grep, Bash, Write, mcp__97433d8a-3a41-4cbb-a624-1011a89c1c52__search_threads, mcp__97433d8a-3a41-4cbb-a624-1011a89c1c52__get_message, mcp__97433d8a-3a41-4cbb-a624-1011a89c1c52__get_thread, mcp__97433d8a-3a41-4cbb-a624-1011a89c1c52__create_draft
model: sonnet
---

Read `pipeline/roles/email-monitor.md` and follow it exactly. The stage rules are in `pipeline/STAGES.md`.
