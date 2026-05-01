# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice

---

## [LRN-20260427-001] correction

**Logged**: 2026-04-27T08:26:27+00:00
**Priority**: high
**Status**: pending
**Area**: infra

### Summary
Long experiment monitoring in this project must use cron-based wakeups, not process polling loops.

### Details
During MyGoogleAlertPapers replay/experiment work, I fell back to `process poll` to monitor a background run. The user explicitly corrected this as the wrong pattern. In this environment, long-running experiment monitoring should use OpenClaw `cron` with current-session wakeups or monitor-only handoff flow, rather than interactive polling.

### Suggested Action
Before starting any long experiment or replay, create a task-state file and schedule a `cron(sessionTarget=current, delivery.mode=none)` follow-up for sparse monitoring / completion handoff. Avoid process polling except for immediate debugging or one-off intervention.

### Metadata
- Source: user_feedback
- Related Files: /home/ewan/.openclaw/workspace-deepblue/TOOLS.md, /home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/.learnings/LEARNINGS.md
- Tags: cron, monitoring, openclaw, experiments

---
