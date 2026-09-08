---
type: draft
title: deepseek-harness-docs
status: proposed
tags: [docs-site-macos, output-report]
timestamp: 2026-08-18
---

# 180826-deepseek-harness-docs
**Type:** draft
**Status:** proposed
**Tags:** docs-site-macos, output-report
**Proposed:** 2026-08-18

## What
Rebuilt the deepseek-harness research report (originally a hand-rolled mermaid+svg-pan-zoom
HTML that failed to render zoom for the user) as a `docs-site-macos` page: 5 core models of
`deepseek-ai/deepseek-harness` (Cordis kernel, agent turn loop, subagent, sandbox,
persistence & compaction), each with a hand-authored draggable/zoomable SVG topdown diagram
and a step-flow sequence diagram, plus a numbered linear walkthrough under each sequence
diagram, plus a closing section mapping findings onto `demo_agents/weather_agent/harness.py`.

## Output
Single self-contained HTML file with liquid-glass macOS design system, sidebar nav with
scroll-spy, collapsible mind map, draggable/pannable/zoomable node-graph diagrams (own
pointer/wheel handling — no external JS libraries), light/dark theme toggle. Verified via
headless Chrome (zero console errors, all 10 diagram-boxes got their draggable viewport +
node groups attached) before handing off.

## Files
| File | Action |
|------|--------|
| `llmwiki/html/180826-deepseek-harness-report.html` | rewritten (replaces mermaid-based version) |

## Notes
- Invoked via: `/docs-site-macos` skill, after two prior attempts at a hand-rolled
  mermaid + svg-pan-zoom version failed to give the user working zoom (root cause found via
  headless Chrome: one diagram's raw angle-bracket text broke Mermaid's parser and silently
  killed pan-zoom setup for all 10 diagrams — fixed once, but user asked to just rebuild with
  this skill instead of continuing to patch the hand-rolled version).
- Content (file:line citations, code snippets, recommendations) carried over faithfully from
  the prior version — not re-derived.

## Origin
- **Draft:** `wiki/sources/draft/180826-deepseek-harness-docs.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
