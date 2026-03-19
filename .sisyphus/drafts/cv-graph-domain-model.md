# Draft: CV Graph Domain Model & UI Design

## Business Process (as understood from user)

### The Matching Pipeline

1. **Requirements** arrive from job postings — they are essentially required skills/competencies
2. **Evidence** lives in the CV profile — it comes from *events*: jobs held, education/formation, publications, projects, and potentially other types we don't know yet
3. Each piece of evidence (event) **implies a set of skills**
   - Example: "Developed ETL pipeline using Airflow" implies → `developing`, `ETL`, `Airflow` skills
   - Skills are NOT just keywords listed in the JSON — they are *demonstrated* by the event's narrative
4. Each **skill** has its own categories and dimensions:
   - Type/domain: programming, language, soft-skill (managing groups, coordinating people), etc.
   - Level of expertise (implied by depth/recency of evidence)
   - Essential vs. optional
   - Possibly more dimensions TBD
5. **Matching**: requirements from job → matched against skills → traced back to evidence events
6. **Ranking & Selection**: matched events are ranked and selected to build a *story* — why this person is a match
7. **Output documents**:
   - **Motivation letter**: the narrative story woven from selected evidence
   - **CV summary**: targeted highlight reel

### CV Composition (beyond the story)

The full CV has two layers:

- **Essential elements** (always present, standard structure):
  - Job listing (chronological experience entries)
  - Education section
  - Personal data (name, contact, legal)
  - "Unavoidable" skills (core competencies that appear regardless)
  - Each has a *standard description* that **can be reframed** if a specific skill needs proving

- **Skills listing**: should map back to the events/evidence that demonstrate them
  - Not a flat dump — each skill in the listing connects to where it was exercised

### Key Insight: Skills Are a Cross-Cutting Dimension

Skills are NOT children of events. They are an **independent entity type** that is
*referenced by* events. Multiple events can demonstrate the same skill.
A skill exists once but has many evidence links.

---

## Confirmed Requirements

- [user] Skills must be a distinct node type with their own rich properties
- [user] Events are the primary evidence unit — jobs, education, publications, projects, etc.
- [user] Each event has internal data: date, type/group, related skills, essential flag, **and more TBD**
- [user] Each skill→event relationship has its own metadata (not just "references")
- [user] Skill categories: programming, language, soft-skill, essential, type, level of expertise, etc.
- [user] Shape is NOT final — extensibility matters heavily
- [user] The graph must support the full pipeline: requirements → evidence matching → ranking → story → documents

### Round 2 Decisions

- [user] Graph scope: **CV-only**. Requirements/matching live separately, connect at query time.
- [user] Event vs Evidence: **same node, different role**. "Event" on the CV side, "Evidence" during matching.
  - An Event *becomes* Evidence when matched against a requirement. It's a role, not a type.
- [user] EssentialElement: **NOT a separate node type**. It's a *flag* on Event or Skill.
  - "Essential" = must appear on the final document regardless of matching emphasis.
- [user] Event categories: determined by "where on the CV it appears" + event type (job, internship, publication, etc.).
- [user] Event descriptions: must support *variant descriptions* per context — one for CV, one for motivation letter,
  and these can change depending on which requirements need fulfilling.
- [user] Skill→Event relationship: **both** — store what's statically known (e.g., this event explicitly mentions this skill),
  derive the rest during matching (strength, relevance scoring).
- [user] Requirements and Events are conceptually related: both "are composed of" skills.
  Requirements demand skills, Events demonstrate skills. Skill is the bridge.

## Technical Decisions

- (none yet — discussing domain model first)

### Round 3 Decisions

- [user] Personal data/contact/legal: **same node type as events**, not a separate class.
  - "Event" name should probably change to something more general (it's not really an "event").
  - Category handles the distinction: `personal_data`, `contact`, `legal_status`.
- [user] Achievements: **can be nodes inside a node** (children of an Event).
  - BUT user is confused about the boundary between "achievement" and "description".
  - Need to clarify: what is the "description" of an event vs. its "achievements"?
- [user] Languages: **Both Skill AND Event**.
  - The language itself (Spanish C2) is a Skill with category=language.
  - The fact of being native / having a cert is an Event that proves that skill.

### Round 4 Decisions

- [user] General node type name: **Entry** (replaces "Event").
- [user] Rename "achievements" to **descriptions** everywhere in the domain.
  - "Description" is the universal term — applies to jobs, education, projects, personal data, everything.
  - Each Entry has a collection of descriptions (bullet points).
  - Each description has a *key* and *styling metadata* associated with it.
  - Keywords/skills are **extracted from descriptions** and mapped into Skill nodes.
- [user] Descriptions are a **list property** on the Entry, NOT child nodes.
  - But there must be logic to **map a specific skill back to the specific description(s)** that prove it.
  - So when we need to prove a skill, we can "rescue" the relevant description bullet.
  - This implies: Skill→Entry DEMONSTRATES edge needs to reference WHICH descriptions are relevant.
- [user] "Achievement" is **deleted from the domain vocabulary**. Use "description" everywhere.

### Round 5 Decisions

- [user] Description keys: **content-derived slug** (auto-generated from text).
  - Stable across reordering, avoids manual effort.
  - Must handle collisions (append suffix if two descriptions slug to the same key).
- [user] Description styling = **semantic weight**, not visual formatting.
  - Values like: `headline`, `primary_detail`, `supporting_detail`, `footnote`
  - Determines importance/role of the bullet within the Entry, not how it renders.

### Round 6 Decisions

- [user] Skill→description mapping: **Both layers**.
  - Base graph stores obvious/explicit links (from keywords in the profile).
  - Matching adds finer-grained description→skill links at runtime.
- [user] Source schema: **Evolve the JSON** to match the domain model.
  - But **save the migration/transformation logic** so it can be reused for other people's profiles.
  - Target: profile JSON uses new vocabulary (entries, descriptions, weights).
  - Adapter/builder serves as documented migration path.
- [user] Skill level: refers to **mastery level** — e.g., "C1" for English, "advanced" for Python.
  - **Absolutely optional**. Many skills won't have a level.
  - Stored as a property on the Skill node (not on the edge).

## Open Questions

- How do "essential" flags interact with matching — always included even if unmatched?
- (No other blocking questions on domain model — complete per user confirmation)

---

## UI REDESIGN (2026-03-18)

Plan generated at `.sisyphus/plans/cv-graph-editor-redesign.md`

Key decisions recorded:
- No Tailwind — plain CSS with custom properties
- Side panel removed entirely — editing happens inside expanded entry nodes
- Skills as small colored circles (40-48px), visible only when entry selected
- Skill linking via React Flow `onConnect` drag-from-handle (no checkboxes)
- Custom node components: EntryNode, SkillBallNode, DescriptionNode, GroupNode
- Zoom-contextual rendering (less detail at low zoom)
- dagre re-layout on expand/collapse
- 3-wave execution: components → integration → polish

---

## FORMAL SCHEMA (Canonical Reference)

### Node: Entry

A unit of the CV profile. Everything on the CV is an Entry.

```
Entry {
  id:           str           # content-derived slug, collision-safe
  category:     str           # "job_experience" | "internship" | "education" | "publication" |
                              # "project" | "language_fact" | "personal_data" | "contact" |
                              # "legal_status" | ... (extensible)
  essential:    bool          # must appear on final CV regardless of matching emphasis
  fields:       dict[str,any] # extensible, type-specific:
                              #   job: { role, organization, location, start_date, end_date }
                              #   education: { degree, institution, specialization, location, start_date, end_date, level_reference, equivalency_note }
                              #   publication: { title, year, venue, url }
                              #   project: { name, role }
                              #   personal_data: { full_name, preferred_name, birth_date, nationality }
                              #   contact: { email, phone, addresses[], links{} }
                              #   legal_status: { visa_type, visa_status, work_permission_germany }
                              #   language_fact: { name, level, note }
                              #   ... (new categories add new field shapes)
  descriptions: list[Description]  # bullet points describing what happened / what this is
}
```

### Embedded: Description

A bullet point within an Entry. Not a graph node — a list item on the Entry.

```
Description {
  key:    str       # content-derived slug (auto-generated, collision-safe with suffix)
  text:   str       # raw description text
  weight: str       # semantic weight: "headline" | "primary_detail" | "supporting_detail" | "footnote"
}
```

### Node: Skill

A capability demonstrated by Entries, demanded by Requirements.

```
Skill {
  id:         str           # content-derived slug (e.g., "python", "team_management")
  label:      str           # display name: "Python", "Team Management"
  category:   str           # "programming" | "language" | "soft_skill" | "domain_knowledge" |
                            # "tool" | "methodology" | ... (extensible)
  essential:  bool          # must appear in skills listing regardless of matching
  level:      str | null    # mastery level, optional: "C1", "advanced", "expert", null
  meta:       dict[str,any] # extensible additional properties
}
```

### Edge: DEMONSTRATES

Links an Entry to a Skill it proves.

```
DEMONSTRATES {
  id:               str        # deterministic: "{entry_id}:demonstrates:{skill_id}"
  source:           str        # entry_id
  target:           str        # skill_id
  description_keys: list[str]  # which Description keys within the Entry are evidence (base graph layer)
  # --- Derived during matching (NOT stored in base profile graph) ---
  # strength:  float | null
  # relevance: float | null
}
```

### Payload Envelope

```
CvProfileGraph {
  profile_id:       str       # "profile:{owner_slug}"
  snapshot_version: str       # from source JSON
  captured_on:      str       # from source JSON
  entries:          list[Entry]
  skills:           list[Skill]
  demonstrates:     list[DEMONSTRATES]
}
```

### Profile JSON → Graph Mapping

| Profile JSON path                | → Node type | Category          | Essential |
|----------------------------------|-------------|-------------------|-----------|
| owner.full_name/preferred_name   | Entry       | personal_data     | yes       |
| owner.birth_date/nationality     | Entry       | personal_data     | yes       |
| owner.contact.*                  | Entry       | contact           | yes       |
| owner.links.*                    | Entry       | contact           | yes       |
| owner.legal_status.*             | Entry       | legal_status      | yes       |
| education[n]                     | Entry       | education         | context   |
| experience[n]                    | Entry       | job_experience/internship | context |
| experience[n].achievements → descriptions | Description[] on Entry | — | —  |
| experience[n].keywords           | → Skill nodes + DEMONSTRATES edges | —  | — |
| publications[n]                  | Entry       | publication       | context   |
| projects[n]                      | Entry       | project           | context   |
| languages[n]                     | Entry (language_fact) + Skill (language) | — | context |
| skills.{category}[n]            | Skill       | per dict key      | context   |
| cv_generation_context            | NOT a node — generation metadata only | — | — |

### Migration Strategy

- Target: evolve profile_base_data.json to use Entry/Skill/Description vocabulary natively
- Preserve current builder as documented adapter (reusable for migrating other profiles)
- Save transformation logic in a standalone migration module

## Scope Boundaries

- INCLUDE: CV-profile graph domain model, node types, relationship semantics
- EXCLUDE: UI rendering concerns (discuss separately after model is settled)
- EXCLUDE: Job/requirements graph (separate concern, connects at query time)

---

## UI REDESIGN Round 2 — User Corrections (2026-03-18)

### Preserved: Box-in-box layout
- Group→Entry nesting via `parentId` + `extent: "parent"` MUST NOT change
- Entry positions: `{ x: 14, y: 50 + idx * 78 }` relative to group

### Changed from Round 1:
- USE Tailwind (add to project)
- Side panel REPURPOSED (not deleted) — becomes skill palette / unconnected skill pool
- Description is NOT a separate node — it's a property inside EntryNode (visible when expanded)
- Entry expand goes TO THE RIGHT (adjacent panel), not in-place height change
- SkillBall: name always visible, category color, mastery = color intensity + name + number
- Need mastery "scale database" mapping levels to numerical values
- "+" button at bottom of each box to add new contained items
- Skills are circles now but shape should be polymorphic for future
- Free to use new npm dependencies

### Mastery Scale Database (from research)
5-level unified scale (covers programming, languages, soft skills, domain knowledge):

| Value | Tag | Label | CEFR | Dreyfus | Intensity |
|-------|-----|-------|------|---------|-----------|
| 1 | novice | Novice | A1 | Novice | 0.17 |
| 2 | beginner | Beginner | A2 | Adv. Beginner | 0.33 |
| 3 | intermediate | Intermediate | B1-B2 | Competent | 0.50 |
| 4 | advanced | Advanced | C1 | Proficient | 0.75 |
| 5 | expert | Expert | C2 | Expert | 1.0 |

Color intensity = category hue at varying lightness (darker = more proficient).
Each skill ball shows: category color * mastery intensity + visible label + level tag.
