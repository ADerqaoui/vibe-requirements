# Requirements — Requirement Review Dashboard

## Document Control

| Field | Value |
|---|---|
| Project | Requirement Review Dashboard |
| Version | v1 — Requirements Baseline |
| Date | 2026-05-29 |
| Status | Draft for review |
| Hosting | Self-hosted on user's Debian 13 server (LAN-only, single-user) |
| Hardware | NVIDIA RTX 3080, Ollama at `0.0.0.0:11434` |
| Cloud providers | Anthropic, OpenAI, Deepseek (extensible) |

## Document Overview

A web application that helps a single engineer generate, inspect, refine, and export software/electronic/mechanical specifications from user Needs using a configurable mix of local (Ollama) and cloud LLMs. The system follows V-model decomposition, supports multi-discipline tagging, manages prompts and models in a database, tracks per-call cost in SEK, and exports finished specs to Markdown with embedded Mermaid diagrams.

---

## 1. Project Management

| ID | Requirement | Notes |
|---|---|---|
| REQ-PROJ-001 | The system shall allow the user to create a new project by providing a project name. | Name = only required field in v1 |
| REQ-PROJ-002 | The system shall display a list of all existing projects in the Projects column. | |
| REQ-PROJ-003 | The system shall allow the user to select a project, which loads its Needs and all descendant specs. | |
| REQ-PROJ-004 | The system shall visually highlight the currently selected project. | |
| REQ-PROJ-005 | The system shall allow the user to rename a project. | |
| REQ-PROJ-006 | The system shall allow the user to delete a project, after a confirmation prompt. | Cascading delete of all Needs + specs |
| REQ-PROJ-007 | The system shall reject project creation if a project with the same name already exists in the database. | Names unique |
| REQ-PROJ-008 | The system shall persist all project data in the database. | |

---

## 2. Need Management

| ID | Requirement | Notes |
|---|---|---|
| REQ-NEED-001 | The system shall allow the user to create a Need under the selected project by providing three fields: Statement, Context, Constraints. | Statement required; Context and Constraints optional |
| REQ-NEED-002 | The system shall allow the user to edit any of the three Need fields after creation. | |
| REQ-NEED-003 | The system shall not associate a Need with any discipline. | Discipline-independent |
| REQ-NEED-004 | When a Need is edited, the system shall clear its complexity classification. | Forces re-classify before next generation |
| REQ-NEED-005 | The system shall require a Need to have a complexity classification before allowing requirement generation under that Need. | See Section 5 |
| REQ-NEED-006 | The system shall display all Needs of the selected project in the Needs column. | |
| REQ-NEED-007 | The system shall visually highlight the currently selected Need. | |
| REQ-NEED-008 | The system shall allow the user to delete a Need after a confirmation prompt. | |
| REQ-NEED-009 | When a Need is deleted, the system shall cascade-delete all descendant specs under that Need. | |
| REQ-NEED-010 | When a Need is deleted, the system shall also delete the blacklist associated with that Need. | See Section 7 |
| REQ-NEED-011 | The system shall persist all Need fields and their classification in the database. | |
| REQ-NEED-012 | The system shall display a visual indicator on any Need that has no complexity classification set. | Nudges user to classify |

---

## 3. Spec Generation

| ID | Requirement | Notes |
|---|---|---|
| REQ-GEN-001 | The system shall allow the user to generate specs under either a selected Need (producing top-level specs) or under a selected Accepted spec (producing children). | Same action, different parent types |
| REQ-GEN-002 | The system shall require the parent to be Accepted before allowing child-spec generation. | |
| REQ-GEN-003 | The system shall require the parent (Need or Spec) to have a complexity classification before allowing generation under it. | See Section 5 |
| REQ-GEN-004 | The system shall let the user choose the target layer at generation time, defaulting to one V-model step deeper than the parent. | |
| REQ-GEN-005 | The system shall let the user choose one or more disciplines at generation time, when the target layer is multi-discipline-capable. | Discipline-locked layers auto-set |
| REQ-GEN-006 | The system shall use the Router to select the LLM provider, model, and prompt for the generation call. | See Section 8 |
| REQ-GEN-007 | The system shall produce N candidate specs per Generate click, where N is configurable (default 3). | |
| REQ-GEN-008 | The system shall set each newly generated spec to status `Pending`. | |
| REQ-GEN-009 | When the user clicks Generate at a location that contains Rejected specs, the system shall hard-delete those Rejected specs and add their text to the blacklist of the parent before producing new candidates. | |
| REQ-GEN-010 | The system shall leave Accepted and Pending specs untouched when Generate is clicked. | |
| REQ-GEN-011 | The system shall provide Accept and Reject actions on every Pending spec. | |
| REQ-GEN-012 | Accepting a spec shall change its status to `Accepted` and persist it permanently until edited. | |
| REQ-GEN-013 | Rejecting a spec shall change its status to `Rejected` and visually grey out / strike through the spec until next Generate click. | |
| REQ-GEN-014 | The system shall provide a description panel that displays the text of the currently selected spec (or Need) and allows the user to edit it. | |
| REQ-GEN-015 | The system shall allow the user to create a spec manually by selecting the target layer + disciplines and entering text in the description panel. | Manually created spec starts as Pending |
| REQ-GEN-016 | A manually created spec shall follow the same Accept / Reject / Inspector workflow as AI-generated specs. | |
| REQ-GEN-017 | When the user edits an Accepted spec, the system shall: (a) snapshot the current version into `spec_revisions` (revision history), (b) add the old text to the parent's blacklist, (c) cascade-delete all descendant specs of the edited spec, (d) auto-Accept the new text, (e) clear the classification. | Old version is preserved as read-only history and still won't be regenerated as a sibling |
| REQ-GEN-018 | When the user edits a Pending or Rejected spec, the system shall replace the text in place, set status to `Pending`, and clear the classification. | Editing a Rejected spec = reconsidering |
| REQ-GEN-019 | The system shall track which model + prompt produced each AI-generated spec, for audit and Inspector second-opinion logic. | |
| REQ-GEN-020 | The system shall mark manually created specs with a `manual` source flag. | Inspector second-opinion uses any model |
| REQ-GEN-021 | The system shall persist all spec fields, status, layer, disciplines, classification, and source in the database. | |
| REQ-GEN-022 | When blacklisting a rejected spec that has an attached diagram, the system shall add only the spec's text to the blacklist (not the diagram source). | |

---

## 4. Discipline & Layer Model

| ID | Requirement | Notes |
|---|---|---|
| REQ-MODEL-001 | The system shall support a fixed set of disciplines for v1: SW, Electronic, Mechanical. | Stored in DB; UI editing deferred |
| REQ-MODEL-002 | The system shall support a fixed set of V-model layers for v1: Need, System Requirement, System Architecture, SW Requirement, SW Architecture, SW Component/Unit, Electronic Requirement, Electronic Architecture, Electronic Component, Mechanical Requirement, Mechanical Architecture, Mechanical Component. | Stored in DB |
| REQ-MODEL-003 | Each layer shall be classified as either Cross-Cutting (Need, System Req, System Architecture) or Discipline-Locked (all SW/Electronic/Mechanical layers). | |
| REQ-MODEL-004 | Specs at a Discipline-Locked layer shall be auto-tagged with that layer's discipline and not editable. | |
| REQ-MODEL-005 | Specs at a Cross-Cutting layer (except Need) shall require the user to choose 1, 2, or 3 disciplines from the set {SW, Electronic, Mechanical}. | At least one required |
| REQ-MODEL-006 | Needs shall have no discipline (empty set). | |
| REQ-MODEL-007 | The system shall define V-model parent-child relationships: each layer has a list of allowed parent layers. | Used for default child layer + traceability |
| REQ-MODEL-008 | When the user creates a spec with a parent layer outside the V-model allowed list, the system shall show a warning but allow the operation. | Advisory, not blocking |
| REQ-MODEL-009 | The system shall display the parent trace of every spec (its parent's ID + layer). | |
| REQ-MODEL-010 | The Needs column shall display Needs as a flat list (no discipline banding). | |
| REQ-MODEL-011 | The Spec columns (Requirements, Children, Grand Children, …) shall display specs in 3 horizontal discipline bands: SW, Electronic, Mechanical. | |
| REQ-MODEL-012 | A spec tagged with multiple disciplines shall be rendered in every band it is tagged with, while remaining a single underlying node in the database. | Duplicated display |
| REQ-MODEL-013 | Editing or deleting a duplicated spec from one band shall reflect across all bands where it appears. | Same node, multiple views |
| REQ-MODEL-014 | Selecting a Need shall display its descendant specs in the Spec columns; selecting a spec shall highlight the spec across all bands where it appears. | |
| REQ-MODEL-015 | The system shall persist disciplines as a set on every spec node (empty for Needs, ≥1 for non-Need specs). | |

---

## 5. Complexity Classification

| ID | Requirement | Notes |
|---|---|---|
| REQ-CLASS-001 | The system shall support a complexity scale of integer 1 (low) to 5 (high). | |
| REQ-CLASS-002 | The system shall provide a Classify action on every Need and every spec. | |
| REQ-CLASS-003 | When Classify is triggered, the system shall query 3 configured local LLM models sequentially via Ollama and request a complexity score for the target item. | Sequential to avoid VRAM pressure |
| REQ-CLASS-004 | The default 3 models shall be: `qwen2.5:7b`, `llama3.1:8b`, `gemma2:9b` (all local, already installed). | Three different training lineages (Alibaba/Meta/Google) for uncorrelated votes |
| REQ-CLASS-005 | The system shall allow the user to change the 3 classifier models in Settings, choosing from any model registered in the Model registry. | See Section 9 |
| REQ-CLASS-006 | Each classifier model shall return an integer score between 1 and 5. | |
| REQ-CLASS-007 | The system shall display all 3 individual model votes to the user. | No auto-aggregation |
| REQ-CLASS-008 | The system shall allow the user to confirm one of the votes as final OR enter their own value (1–5). | |
| REQ-CLASS-009 | The system shall persist both (a) the user-confirmed final complexity value and (b) the individual votes of each model. | Audit trail |
| REQ-CLASS-010 | When a classifier model fails to respond, the system shall display the failure, keep the successful votes, and allow the user to enter the final value manually. | |
| REQ-CLASS-011 | If all 3 classifier models fail, the system shall display an error and allow the user to enter the final value manually. | |
| REQ-CLASS-012 | The system shall allow the user to re-run classification at any time; re-running overwrites the previous result. | |
| REQ-CLASS-013 | Editing a Need or spec shall clear its classification. | |
| REQ-CLASS-014 | The Router shall use the user-confirmed final complexity value as the source of truth when selecting a model for generation under that Need/spec. | |
| REQ-CLASS-015 | The system shall disable generation actions under any Need or spec that has no final complexity value set. | |
| REQ-CLASS-016 | The classification prompt template shall be stored in the Prompt registry and shall be editable. | See Section 9 |

---

## 6. Inspector

| ID | Requirement | Notes |
|---|---|---|
| REQ-INSP-001 | The system shall provide an Inspect action on every spec (not on Needs in v1). | |
| REQ-INSP-002 | The Inspector shall run as a multi-pass check — each category as a separate LLM call — subject to the bounded-call limits in REQ-INSP-021 to REQ-INSP-024 (no unbounded looping). | |
| REQ-INSP-003 | For specs without diagrams, the Inspector shall run these 7 text categories: (1) Ambiguity, (2) Verifiability, (3) Singularity, (4) Implementation-free, (5) Traceability to parent, (6) Hallucination, (7) Standards form (EARS). | |
| REQ-INSP-004 | For specs with an attached diagram, the Inspector shall additionally run 3 diagram categories: (1) Mermaid syntax validity, (2) Text-diagram consistency, (3) Standard conformance for the diagram type. | |
| REQ-INSP-005 | The Inspector shall use the Router to select the model, excluding the model that generated the spec (second-opinion rule) when the spec source is `ai`. | |
| REQ-INSP-006 | For specs with source `manual`, the Inspector shall be free to pick any eligible model via the Router. | |
| REQ-INSP-007 | If the only available eligible model is the original generator, the system shall fall back to using it and display a warning. | |
| REQ-INSP-008 | The Inspector shall use the spec's complexity value to determine the model tier via the Router. | |
| REQ-INSP-009 | Each finding produced shall include: category, severity (critical / major / minor), explanation, and a suggested rewrite. | |
| REQ-INSP-010 | The system shall display a quality score on the spec (e.g., "6/7 passed" or "9/10 passed" with diagrams). | |
| REQ-INSP-011 | The system shall display a color-coded badge on the spec: green (0 critical, 0 major, ≤1 minor), yellow (0 critical, 1–2 major), red (any critical, or ≥3 major). | |
| REQ-INSP-012 | The EARS / standards form check shall be advisory only — finding flagged but not blocking. | |
| REQ-INSP-013 | The Inspector shall be triggered on-demand only — never automatically. | |
| REQ-INSP-014 | The system shall provide an Apply suggested rewrite action per finding. | |
| REQ-INSP-015 | Applying a suggested rewrite shall be treated identically to a manual edit (same cascade rules per REQ-GEN-017 / REQ-GEN-018). | |
| REQ-INSP-016 | The system shall provide a Dismiss action per finding, removing the finding without changing the spec. | |
| REQ-INSP-017 | The system shall persist inspection findings while the spec is in `Pending` status, and retain them as archived evidence thereafter. | |
| REQ-INSP-018 | When the spec's status changes to `Accepted`, the system shall **archive** its findings (stamp `archived_at`, optionally link to the `spec_revision` they judged) rather than delete them. | Revision history: review evidence is preserved, not discarded |
| REQ-INSP-019 | Re-running the Inspector on the same spec shall overwrite the previous findings. | |
| REQ-INSP-020 | Each Inspector category shall have its own prompt template stored in the Prompt registry. | |
| REQ-INSP-021 | The Inspector shall enforce a maximum total number of LLM calls per inspection run (default 15, configurable in Settings). | |
| REQ-INSP-022 | Each category check shall be retried at most M times on failure. Default M = 2. | |
| REQ-INSP-023 | Each LLM call shall have a hard per-call timeout (default 60 s, configurable). | |
| REQ-INSP-024 | When the call limit or retry limit is reached, remaining categories shall be marked `not evaluated`, and the user shall be notified. | |

---

## 7. Blacklist

| ID | Requirement | Notes |
|---|---|---|
| REQ-BL-001 | Each Need and each spec shall have its own blacklist, storing rejected text content scoped to that parent. | Per-parent scope, no inheritance |
| REQ-BL-002 | The system shall add blacklist entries before triggering the next generation call. Triggers: (a) on Generate click, all currently-Rejected specs at the target location are first added to the parent's blacklist, then hard-deleted, then the new generation is launched; (b) on Edit of an Accepted spec, the old text is added to the parent's blacklist before any cascade or re-generation. | |
| REQ-BL-003 | The system shall store only the text content in the blacklist; diagrams and metadata are excluded. | REQ-GEN-022 |
| REQ-BL-004 | The system shall compute and store a vector embedding for every blacklist entry. | |
| REQ-BL-005 | The embedding model shall default to `nomic-embed-text` served via Ollama, configurable in Settings. | |
| REQ-BL-006 | When generating new specs under a parent, the system shall include the parent's blacklist texts in the LLM prompt as an "AVOID" section. | |
| REQ-BL-007 | If the blacklist's token footprint exceeds the prompt token budget, the system shall truncate to the most recent entries that fit. | |
| REQ-BL-008 | After generation, the system shall compute embeddings for each candidate and compare against the parent's blacklist using cosine similarity. | |
| REQ-BL-009 | If cosine similarity exceeds the configured threshold (default 0.85), the candidate shall be treated as a blacklist collision and discarded. | |
| REQ-BL-010 | On collision, the system shall retry generation up to N times (default 3, configurable), regenerating only the colliding candidates. | |
| REQ-BL-011 | If collisions remain after the retry limit, the system shall present the surviving candidates with a "blacklist-collision warning" badge. | |
| REQ-BL-012 | If embedding computation fails, the system shall proceed with generation, skip the similarity check, and display a warning. | |
| REQ-BL-013 | The system shall provide a Blacklist management view, listing all blacklist entries grouped by parent. | |
| REQ-BL-014 | The Blacklist management view shall allow the user to remove an entry, making it available for future generation again. | |
| REQ-BL-015 | The system shall display a small indicator on each Need and spec showing the count of entries in its blacklist (e.g., 🚫 3). | |
| REQ-BL-016 | Deleting a Need or spec shall delete its associated blacklist (cascade). | |
| REQ-BL-017 | The system shall persist blacklist entries with: text, embedding, timestamp added, source flag (`rejected` or `edited-out`). | |
| REQ-BL-018 | The similarity threshold and retry count shall be exposed in Settings, configurable by the user. | |

---

## 8. Router

| ID | Requirement | Notes |
|---|---|---|
| REQ-ROUTER-001 | The system shall provide a Router with two modes: ON (automatic selection) and OFF (manual selection), toggleable from the main UI. | |
| REQ-ROUTER-002 | When the Router is OFF, the user shall select the provider + model and the prompt manually before triggering Generate or Inspect. | |
| REQ-ROUTER-003 | When the Router is ON, the system shall select the provider + model automatically using inputs: (a) task type, (b) target spec's complexity, (c) model cost. | |
| REQ-ROUTER-004 | When the Router is ON, the system shall select the prompt automatically from the Prompt registry using inputs: (a) target layer, (b) task type, (c) target discipline(s). | |
| REQ-ROUTER-005 | The system shall maintain a Model registry in the database. Each entry shall contain: `provider`, `name`, `ollama_tag` or `api_model_id`, `tier` (low / mid / high), `input_cost_per_1k_tokens`, `output_cost_per_1k_tokens`, `enabled` flag. | |
| REQ-ROUTER-006 | The system shall maintain a complexity-to-tier mapping, default: complexity 1–2 → Low, 3 → Mid, 4–5 → High. Editable in Settings. | |
| REQ-ROUTER-007 | The Router ON model selection algorithm shall be: (1) determine required tier from complexity; (2) filter Model registry by required tier and `enabled = true`; (3) apply Inspector exclusion if applicable; (4) pick the cheapest model; (5) break cost ties by preferring local (Ollama) over cloud. | |
| REQ-ROUTER-008 | For Inspector tasks on AI-generated specs, the Router shall exclude the specific model that produced the spec from eligibility. | Model-level second-opinion rule |
| REQ-ROUTER-009 | If the Router exclusion leaves zero eligible models, the system shall fall back to the original generator with a "second-opinion unavailable" warning. | |
| REQ-ROUTER-010 | The Router ON prompt selection algorithm shall be: query Prompt registry where `layer = target_layer` AND `task = target_task` AND `enabled = true`, then pick the highest-version prompt matching discipline (per REQ-ROUTER-021). | |
| REQ-ROUTER-011 | The system shall display the selected provider, model, and prompt on every AI-generated artifact and inspection finding (for transparency). | |
| REQ-ROUTER-012 | For multi-call operations (e.g., Inspector multi-pass), the Router shall use the same model for all sub-calls within one operation. | |
| REQ-ROUTER-013 | If the selected provider returns an error or times out, the system shall retry the same call up to M times (default 2), then fall back to the next eligible model. | |
| REQ-ROUTER-014 | Each LLM call shall have a per-call timeout: default 60 s for cloud, 120 s for local (Ollama). Configurable. | |
| REQ-ROUTER-015 | If no eligible models exist for a given (task, complexity), the system shall display a clear error and prevent the action. | |
| REQ-ROUTER-016 | If no enabled prompt exists for a given (layer, task), the system shall display a clear error and prevent the action. | |
| REQ-ROUTER-017 | The system shall perform a lightweight health check on the selected provider before each call. On failure, treat as REQ-ROUTER-013. | |
| REQ-ROUTER-018 | Cloud-provider API keys shall be read from environment variables (`.env`), never stored in the database or any backup dump. The Settings UI shall display each provider's key status (configured / not configured, masked) but shall not persist keys to the DB. Changing a key is done by editing `.env` and restarting the backend; the app never writes secrets. | Keys never enter the DB, backups, or git |
| REQ-ROUTER-019 | The system shall log every LLM call: timestamp, provider, model, prompt id, input tokens, output tokens, cost, duration, success/failure status. | |
| REQ-ROUTER-020 | Each prompt in the registry shall be tagged with: `layer`, `task`, `discipline_scope` (null / specific discipline / "any"), `version`, `enabled`. | |
| REQ-ROUTER-021 | The Router shall match prompts by (layer, task, discipline) with the following fallback order: (1) exact discipline match → (2) `discipline_scope = "any"` → (3) error if nothing found. | |
| REQ-ROUTER-022 | The system shall inject the following runtime variables into every selected prompt before sending: `{parent_text}`, `{context}`, `{constraints}`, `{target_layer}`, `{target_disciplines}`, `{avoid_list}`, `{n_candidates}`. | |
| REQ-ROUTER-023 | Each prompt template shall include a persona statement at its start, appropriate to the layer + discipline. | |

---

## 9. Prompt Management

| ID | Requirement | Notes |
|---|---|---|
| REQ-PROMPT-001 | The system shall maintain a Prompt registry in the database. | |
| REQ-PROMPT-002 | Each prompt entry shall contain: `id`, `name`, `description`, `layer`, `task`, `discipline_scope`, `version`, `template` (text), `enabled` (boolean), `created_at`, `updated_at`. | |
| REQ-PROMPT-003 | The system shall support the following task types: `generate_requirement`, `generate_child`, `generate_diagram`, `inspect_ambiguity`, `inspect_verifiability`, `inspect_singularity`, `inspect_implementation_free`, `inspect_traceability`, `inspect_hallucination`, `inspect_ears`, `inspect_diagram_syntax`, `inspect_diagram_consistency`, `inspect_diagram_standard`, `classify_complexity`. | 14 task types |
| REQ-PROMPT-004 | Prompt templates shall use simple `{variable_name}` placeholder syntax (no conditional logic in v1). | |
| REQ-PROMPT-005 | Every generation-task prompt template shall begin with a persona statement appropriate to its (layer, discipline) combination. | |
| REQ-PROMPT-006 | The system shall ship with a default set of prompts covering every (layer, task, discipline) combination required for v1. | First-run seed |
| REQ-PROMPT-007 | The system shall provide a Settings UI for Prompt Management with: list view (filterable), create, edit, enable, disable. | |
| REQ-PROMPT-008 | Editing an existing prompt shall create a new version row in the DB; the previous version shall be automatically disabled. | |
| REQ-PROMPT-009 | All historical prompt versions shall be retained in the database (no hard-delete on edit). | |
| REQ-PROMPT-010 | The user shall be able to re-enable an older version; doing so shall automatically disable any currently enabled version of the same (layer, task, discipline) combination. | |
| REQ-PROMPT-011 | The system shall enforce that at most one enabled prompt exists per (layer, task, discipline_scope) tuple at any time. | |
| REQ-PROMPT-012 | The system shall validate, before saving a prompt, that the template contains all required placeholders for its task type. | |
| REQ-PROMPT-013 | The Prompt Management UI shall provide a Preview action that renders the prompt with sample inputs (no LLM call). | Free, no API cost |
| REQ-PROMPT-014 | The Prompt Management UI shall provide a Test action that runs the prompt once via the router with user-supplied inputs and displays the LLM response. | Costs tokens |
| REQ-PROMPT-015 | The system shall provide a "View last sent prompt" action on every AI-generated artifact, showing the fully-rendered prompt that was sent to the LLM. | |
| REQ-PROMPT-016 | If a required (layer, task, discipline) prompt has no enabled entry at runtime, the system shall block the action and display a clear error pointing to Prompt Management. | |
| REQ-PROMPT-017 | The system shall persist a reference to the exact prompt id + version used for each AI-generated artifact. | |

---

## 10. Cost Tracking

| ID | Requirement | Notes |
|---|---|---|
| REQ-COST-001 | The system shall compute and persist the cost of every LLM call. | |
| REQ-COST-002 | Cost shall be computed as: `(input_tokens × input_cost_per_1k / 1000) + (output_tokens × output_cost_per_1k / 1000)` using the model's rates from the Model registry. | |
| REQ-COST-003 | Calls to local (Ollama) models shall be recorded with cost = 0 SEK. | |
| REQ-COST-004 | The cost of each call shall be frozen at the time of the call. Subsequent changes to a model's rates shall not alter historical entries. | |
| REQ-COST-005 | Currency for v1 shall be SEK. Cloud-provider costs (priced in USD) shall be converted at a configurable USD→SEK exchange rate set in Settings. | |
| REQ-COST-006 | The system shall display cumulative cost at five levels: per Project, per Need, per Spec (incl. its inspection + diagram calls), per Prompt, and per Model. | |
| REQ-COST-007 | The system shall provide a Call log view listing every LLM call with: timestamp, project, parent Need/spec, task, provider, model, prompt name + version, input tokens, output tokens, cost, duration, status. | |
| REQ-COST-008 | The Call log shall support filtering by: project, Need, spec, prompt, model, provider, time range, status. | |
| REQ-COST-009 | The system shall provide an Export to CSV action on the Call log view. | |
| REQ-COST-010 | The system shall display cost values formatted to 4 decimal places when below 1 SEK, and 2 decimals otherwise. | |
| REQ-COST-011 | The system shall enforce a soft per-project cost ceiling (default 50 SEK, configurable, set to 0 to disable). When cumulative project cost reaches or exceeds the ceiling, the system shall block the next LLM call and present a modal with three options: (a) Allow this one call, (b) Raise ceiling to a new value, (c) Cancel. | |
| REQ-COST-012 | The system shall provide a top-level Cost dashboard widget showing totals for: today, current week, current month, all time. | |
| REQ-COST-013 | The system shall persist, alongside each call's SEK cost, the USD→SEK exchange rate that was applied at the time of the call. | |
| REQ-COST-014 | When option (a) "Allow this one call" is chosen at the ceiling modal, the ceiling shall trigger again on the next call exceeding the threshold (consent is single-use). | |
| REQ-COST-015 | Settings shall expose: the USD→SEK exchange rate, the per-project ceiling default, and per-project ceiling overrides. | |

---

## 11. Export

| ID | Requirement | Notes |
|---|---|---|
| REQ-EXPORT-001 | The system shall support exporting a project to Markdown (MD) only in v1. PDF export deferred. | |
| REQ-EXPORT-002 | The Export action shall be available from the Project view as a button, opening a modal for export options. | |
| REQ-EXPORT-003 | Export options shall include: status filter (Accepted only / Accepted + Pending / All including Rejected), discipline filter (any subset or all), inspection findings (include / exclude). | |
| REQ-EXPORT-004 | Default export options shall be: status = Accepted only, disciplines = all, inspection findings = excluded. | |
| REQ-EXPORT-005 | The exported MD document shall include: project name, export timestamp, tool version, statistics (total Needs, total specs by status, total project cost in SEK), then the content body. | |
| REQ-EXPORT-006 | The content body shall list each Need with its Statement, Context, and Constraints, followed by the spec tree under it grouped by discipline band (SW / Electronic / Mechanical). | |
| REQ-EXPORT-007 | Each exported spec shall include: spec ID, layer, discipline(s), status, parent ID, text, and (if present) its diagram. | |
| REQ-EXPORT-008 | The exported document shall include a Traceability Matrix section (MD table) mapping Need → System spec → … → leaf spec for all included specs. | |
| REQ-EXPORT-009 | Diagrams shall be preserved as fenced ```` ```mermaid ```` code blocks. | |
| REQ-EXPORT-012 | The user shall be able to export a single Need + its descendant spec tree (subset export) in addition to the full project. | |
| REQ-EXPORT-013 | The exported file shall be served as a browser download with filename `<project_name>_<YYYYMMDD-HHMM>.md`. | |
| REQ-EXPORT-014 | Re-exporting the same project with the same options shall produce content-identical output (modulo timestamp metadata). | |
| REQ-EXPORT-015 | The export shall not include the blacklist content in v1. | |

---

## 12. Diagrams

| ID | Requirement | Notes |
|---|---|---|
| REQ-DIA-001 | The system shall use Mermaid as the diagram format for v1. | |
| REQ-DIA-002 | A spec may optionally contain at most one diagram in v1. | |
| REQ-DIA-003 | For Architecture-layer specs, the system shall auto-generate a diagram alongside the spec text on Generate. | |
| REQ-DIA-004 | For all other layers, diagrams shall be optional and added by the user via an "Add Diagram" action. | |
| REQ-DIA-005 | Each diagram shall store: `title`, `diagram_type`, `mermaid_source`, `created_at`, `updated_at`. | |
| REQ-DIA-006 | The system shall support Mermaid diagram types: flowchart, sequence, state, class, ER, block. | |
| REQ-DIA-007 | The system shall render each diagram in the description panel client-side using `mermaid.js`. | |
| REQ-DIA-008 | The description panel shall offer both a rendered view and a source editor (toggle or split view). | |
| REQ-DIA-009 | The system shall provide a Regenerate Diagram action that re-invokes the LLM with the `generate_diagram` prompt, leaving the spec text unchanged. | |
| REQ-DIA-010 | Before saving any diagram, the system shall validate Mermaid syntax. Invalid syntax shall be flagged; save allowed only with explicit user override. | |
| REQ-DIA-011 | Accept / Reject on a spec shall apply to the text + diagram as a single unit. | |
| REQ-DIA-012 | When a spec is hard-deleted, its diagram shall be deleted with it. | |
| REQ-DIA-013 | When the text of a spec with an attached diagram is edited, the diagram shall be preserved but visually flagged with an "out-of-date" indicator until regenerated or dismissed. | |
| REQ-DIA-014 | When auto-generating a diagram for an Architecture-layer spec, the LLM shall select the most appropriate diagram type. The selected type shall be stored. | |
| REQ-DIA-015 | When the user manually adds a diagram, they shall select the diagram type from the supported list before invoking generation. | |
| REQ-DIA-016 | When Mermaid rendering fails due to syntax errors, the UI shall display the source with the parser's error message (no blank state). | |
| REQ-DIA-017 | Diagrams shall be inspected via the 3 diagram-specific Inspector categories when Inspect is run on a diagram-bearing spec. | |
| REQ-DIA-018 | Diagrams shall not be stored in the blacklist when a spec is rejected. | |
| REQ-DIA-019 | The `generate_diagram` prompt shall receive runtime variables: `{parent_spec_text}`, `{layer}`, `{disciplines}`, `{diagram_type}` (when pre-selected). | |

---

## 13. Non-Functional Requirements

| ID | Requirement | Notes |
|---|---|---|
| REQ-NFR-001 | The system shall run as a web application on the user's Debian 13 server. | |
| REQ-NFR-002 | The system shall not require user authentication in v1 (LAN-trusted, single-user). | |
| REQ-NFR-003 | The system shall integrate with Ollama at a configurable host:port (default `0.0.0.0:11434`). | |
| REQ-NFR-004 | The system shall integrate with cloud providers Anthropic, OpenAI, Deepseek; the provider list shall be extensible via the Model registry. | |
| REQ-NFR-005 | The system shall persist all data in a single relational database. | |
| REQ-NFR-006 | All system state shall survive server restarts; the database is the source of truth. | |
| REQ-NFR-007 | Every multi-step write operation shall be wrapped in a database transaction. | |
| REQ-NFR-008 | UI page load time shall be ≤ 2 seconds over a typical LAN connection. | |
| REQ-NFR-009 | User-facing operations not involving LLM calls shall complete in ≤ 500 ms. | |
| REQ-NFR-010 | The system shall be usable on any modern desktop browser (Chrome, Firefox, Safari, Edge — recent versions) at standard desktop resolutions. No specific minimum versions or screen sizes enforced. | |
| REQ-NFR-012 | The system shall display a clear error message and a recovery option for every recoverable failure. No silent failures. | |
| REQ-NFR-013 | The system shall display a progress indicator for any operation expected to take > 2 seconds. | |
| REQ-NFR-014 | The UI shall remain responsive while long operations run (operations are asynchronous, never block the UI thread). | |
| REQ-NFR-015 | Concurrent LLM calls to cloud providers shall be allowed in parallel. Concurrent calls to Ollama shall be serialized to avoid GPU contention. | |
| REQ-NFR-017 | The system shall log: timestamp, level (DEBUG / INFO / WARN / ERROR), source module, message, correlated with call id. Logs shall be stored in rotating files. | |
| REQ-NFR-018 | The system shall make no outbound network calls beyond configured LLM providers. No telemetry, no analytics, no external CDN at runtime. | |
| REQ-NFR-019 | The system shall expose configurable parameters via a Settings UI, including: cost ceiling default, USD→SEK exchange rate, embedding model, classifier models, similarity threshold, retry counts, timeouts, Ollama host/port, logging level. | |
| REQ-NFR-020 | The system shall provide a Database Backup action that exports the entire DB to a single file for the user to download. | |
| REQ-NFR-021 | The system shall provide a Database Restore action that imports a previously exported backup file, replacing current data after user confirmation. | |
| REQ-NFR-022 | The system shall not impose hard limits on the number of projects, Needs, specs, or descendants per Need in v1; performance degradation acceptable beyond ~10 projects / ~50 needs each. | |

---

## Deferred to v2

| Original ID | Item | Reason |
|---|---|---|
| REQ-NFR-016 | LLM response streaming to the UI | Requires SSE/WebSocket + partial-response UI handling; progress indicator (REQ-NFR-013) is sufficient for v1 |
| (PDF export) | PDF export — diagram SVG embedding, title page, ToC, page numbers | MD-only in v1 (REQ-EXPORT-001) |
| (Layer/discipline UI editing) | UI for editing the layer registry and discipline list | DB seed only in v1 (REQ-MODEL-001, REQ-MODEL-002) |
| (Provider-level Inspector exclusion) | Strict second-opinion mode: exclude same provider, not just same model | Model-level exclusion sufficient for v1 (REQ-ROUTER-008) |
| (Inspector on Needs) | Inspect action on Needs (currently specs only) | REQ-INSP-001 |

---

*End of requirements document.*
