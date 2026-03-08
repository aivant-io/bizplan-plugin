# Plugin Refactor Brief: Architecture & Standalone DOCX Export

**Date:** 2026-03-08
**Context:** Research session analyzing current bizplan-plugin architecture, Anthropic's financial-services-plugins patterns, and platform features we're not leveraging.

---

## 1. Current Architecture — What We Have

### Pipeline: 5 sequential skills, single Claude context

```
/bizplan (one session, accumulating context)
├── Stage 1: ecommerce-intake        → 26 Q&A turns → intake.json
├── Stage 2: ecommerce-assumptions   → 49 drivers resolved → assumptions.json
├── Stage 3: ecommerce-financial-model → Excel population + optimization → .xlsx + outputs.json
├── Stage 4: ecommerce-business-plan  → web research + 7k word narrative → .md
└── Stage 5: ecommerce-document-export → Pandoc + python-docx → .docx
```

### Problem: Context bloat degrades performance

By Stage 4 (plan writing — the hardest task), context carries:
- All 5 SKILL.md files (~300 lines each)
- 26 conversational intake turns (no longer needed)
- Multiple JSON blobs (intake, assumptions, model outputs)
- 8-15 web search results with snippets
- Estimated 50-80k tokens before the plan is even written

Claude Code's automatic context compression helps but is a safety net, not a design choice. Compression loses fidelity. The plan writer — which needs the most "creative" capacity — gets the worst context conditions.

### No sub-agents, no model routing

All five stages run on whatever model the user's session uses (typically Opus). The "deep-research agent" and "model agent" mentioned in docs are just descriptive labels for Claude at different pipeline stages, not actual sub-agents.

---

## 2. Anthropic's Financial Services Plugins — What They Do

**Repo:** [anthropics/financial-services-plugins](https://github.com/anthropics/financial-services-plugins)

### Structure: 5 plugins, 41 skills, 38 commands, 11 MCP integrations

```
financial-services-plugins/
├── financial-analysis/      # Core (shared tools + all MCP connectors)
├── investment-banking/      # Add-on
├── equity-research/         # Add-on
├── private-equity/          # Add-on
├── wealth-management/       # Add-on
├── partner-built/           # LSEG, S&P Global
└── .mcp.json                # 11 data provider connections
```

### Their most complex command: `/dcf` (5 steps, 2 skills chained)

```
Step 1: Gather company info (ask user or use ticker)
Step 2: Load comps-analysis skill → build trading comps for 4-6 peers
Step 3: Load dcf-model skill → build full DCF valuation
Step 4: Cross-check valuation (implied multiples vs peers)
Step 5: Deliver output (2 Excel files + summary)
```

### Key differences from our pipeline

| Factor | Their /dcf | Our /bizplan |
|--------|-----------|-------------|
| User input | ~1 turn (ticker) | ~26 turns (full questionnaire) |
| Data source | MCP servers (structured, external) | Web search (noisy, in context) |
| Skills loaded | 2 per command | 5 per command |
| Output type | Structured Excel (formulas) | 7,000 words of prose + Excel |
| Context pressure | Moderate | High |

### Why they don't use sub-agents

1. **MCP externalizes data retrieval** — structured JSON returns, not raw search results
2. **No conversational intake** — ticker input, not 26 questions
3. **Commands are more atomic** — even `/dcf` only chains 2 skills
4. **No long-form generation** — Excel formulas, not 7k words of narrative

**Note:** MCP still adds to context (tool call responses land in conversation), but returns are more context-efficient (clean structured data vs. noisy web snippets). Their SKILL.md files are also massive (DCF skill is 1,500+ lines), so they likely hit context pressure too on complex runs.

---

## 3. Platform Features We're Not Using

### `context: fork` — Isolated skill execution

Available in SKILL.md frontmatter:

```yaml
---
name: ecommerce-document-export
description: Convert markdown to styled DOCX
context: fork    # Runs in isolated subagent — clean context
---
```

- Forked skill gets **no conversation history** — just its SKILL.md as prompt
- Executes independently, returns a summary to the main conversation
- Perfect for skills that don't need prior context (DOCX export, validation)

### `model` — Per-skill model selection

```yaml
---
name: ecommerce-business-plan
description: Write business plan narrative
model: claude-opus-4-6
---
```

Allows right-sizing the model to the task complexity. Anthropic's plugins don't use this (they don't need to — their commands are simpler), but our pipeline would benefit significantly.

### Recommended model routing for our pipeline

| Skill | Recommended Model | Rationale |
|-------|------------------|-----------|
| ecommerce-intake | Haiku | Structured conversation, no heavy reasoning |
| ecommerce-assumptions | Sonnet | Table lookups, formula application, benchmark resolution |
| ecommerce-financial-model | Sonnet | Python script execution, validation loops |
| ecommerce-business-plan | Opus | Research synthesis, 7k words, citation discipline |
| ecommerce-document-export | Haiku | Run a Python script, minimal reasoning |

---

## 4. Proposed Refactored Architecture

### Sub-agent pipeline with context isolation

```
/bizplan (orchestrator — lightweight, manages handoffs)
│
├── Agent 1: Intake (context: fork, model: haiku)
│   └── Outputs: intake.json (written to disk)
│
├── Agent 2: Assumptions (context: fork, model: sonnet)
│   └── Reads: intake.json
│   └── Outputs: assumptions.json
│
├── Agent 3: Financial Model (context: fork, model: sonnet)
│   └── Reads: assumptions.json
│   └── Outputs: {StoreName}_Financial_Model.xlsx + model_outputs.json
│
├── Agent 4: Business Plan (context: fork, model: opus)
│   └── Reads: intake.json + assumptions.json + model_outputs.json
│   └── Outputs: {StoreName}_Business_Plan.md
│
└── Agent 5: DOCX Export (standalone plugin OR context: fork, model: haiku)
    └── Reads: {StoreName}_Business_Plan.md
    └── Outputs: {StoreName}_Business_Plan.docx
```

### Benefits

1. **Each agent starts with clean context** — just its SKILL.md + JSON inputs from prior stages
2. **Plan writer gets maximum context budget** for research + writing (no stale intake instructions)
3. **Cost reduction** — only Stage 4 uses Opus; others use Haiku/Sonnet
4. **Better instruction following** — less context noise means fewer skipped rules
5. **DOCX export fully decoupled** — can be extracted as standalone plugin

---

## 5. Standalone DOCX Export Plugin

### Rationale

The MD-to-DOCX pipeline is vertical-agnostic. Nothing about heading promotion, citation superscripting, TOC generation, cover page styling, or table border injection is specific to business plans.

### Proposed structure

```
md-to-docx/
├── .claude-plugin/plugin.json
├── commands/
│   └── export-docx.md              # /export-docx slash command
├── skills/
│   └── document-export/
│       ├── SKILL.md                 # context: fork, model: haiku
│       ├── scripts/
│       │   ├── export_docx.py       # Core pipeline (extract from current)
│       │   └── create_reference_doc.py
│       ├── templates/
│       │   ├── reference.docx       # Default template
│       │   └── themes/              # Theme presets (future)
│       │       ├── professional.json
│       │       ├── modern.json
│       │       └── academic.json
│       └── requirements.txt         # python-docx only
└── hooks/hooks.json
```

### What's already portable (no changes needed)

- Heading promotion (strip numbering, promote levels)
- Citation superscripting (`[N]` → `^[N]^`)
- URL auto-linking
- Blank line enforcement before lists
- Horizontal rule removal
- YAML front matter injection
- Static TOC generation
- Cover page styling via python-docx
- Table border injection via python-docx

### What needs parameterization

- **reference.docx template** — currently hardcoded navy/blue/Times New Roman. Should be generated from a theme JSON (colors, fonts, sizes, spacing)
- **Document structure assumptions** — currently expects "Business Plan" subtitle and 7 sections. Make configurable via CLI args or front matter
- **Preprocessing steps** — make each step opt-in via flags:
  - `--promote-headings` (default: on)
  - `--superscript-citations` (default: on)
  - `--dynamic-toc` (default: on)
  - `--cover-page` (default: on, with title/subtitle/date args)
  - `--table-borders` (default: on)

### Usage (standalone)

```bash
/export-docx report.md report.docx --title "Q1 Report" --theme professional
```

### Usage (from bizplan plugin as dependency)

The bizplan plugin would invoke the standalone plugin rather than bundling its own export skill. Each vertical provides its own theme JSON.

**Open question:** The Claude plugin marketplace doesn't have a formal dependency mechanism yet. Options: (a) document it as a prerequisite, (b) bundle both plugins, or (c) duplicate the export skill (least preferred).

### Use cases beyond bizplan

- Consulting reports and proposals
- Academic papers (citation handling already built)
- Internal company docs with brand-specific themes
- Any Claude Code user who writes markdown and wants polished Word output

---

## 6. Investigation Items (Not Yet Resolved)

1. **`context: fork` in practice** — How exactly does data pass in/out? Does the forked agent have file system access? Can it read the JSON files written by prior agents? Need to test this.

2. **`model` field compatibility** — Is this available in Claude Code CLI or only Cowork? Does it work with plugins installed from marketplaces?

3. **Plugin dependency model** — No formal mechanism exists. Need a convention for "this plugin requires md-to-docx."

4. **Pandoc dependency** — System binary, not pip-installable. The standalone plugin needs clear installation guidance or a pure-python fallback.

5. **Theme system scope** — Start with just the current template as default, or ship with 2-3 themes? The `create_reference_doc.py` script already generates the template programmatically — extending it to accept a theme JSON is straightforward.

---

## 7. Key Files Reference

| File | Location | Relevance |
|------|----------|-----------|
| Pipeline orchestrator | `bizplan-ecommerce/commands/bizplan.md` | Defines the 5-step pipeline |
| DOCX export skill | `bizplan-ecommerce/skills/ecommerce-document-export/SKILL.md` | Extract for standalone plugin |
| Export script | `bizplan-ecommerce/skills/ecommerce-document-export/scripts/export_docx.py` | Core conversion logic |
| Reference doc generator | `bizplan-ecommerce/skills/ecommerce-document-export/scripts/create_reference_doc.py` | Template creation |
| Plugin manifest | `bizplan-ecommerce/.claude-plugin/plugin.json` | Current plugin metadata |
| Marketplace manifest | `.claude-plugin/marketplace.json` | Plugin registry |

---

## 8. Recommended Phased Approach

### Phase 1: Extract standalone DOCX plugin
- Pull export skill out of bizplan-ecommerce
- Parameterize hardcoded values (title, subtitle, theme)
- Add `context: fork` to SKILL.md frontmatter
- Register as separate plugin in marketplace
- Update bizplan-ecommerce to reference the standalone plugin

### Phase 2: Add `context: fork` to other skills
- Add to intake, assumptions, financial-model skills
- Test that forked agents can read/write files from disk
- Verify JSON handoffs work across forked contexts

### Phase 3: Add `model` routing
- Assign appropriate models per skill (see table in Section 3)
- Benchmark cost and quality differences
- Adjust model assignments based on results

### Phase 4: Theme system for DOCX plugin
- Define theme JSON schema (colors, fonts, sizes, spacing)
- Ship 2-3 presets (professional, modern, academic)
- Update `create_reference_doc.py` to accept theme input
