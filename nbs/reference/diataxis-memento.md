# Diataxis Memento For MARISCO

Use this note as a classifier before writing documentation, notebooks, or explanatory prompts.

The purpose is not to explain Diataxis in the abstract. The purpose is to stop MARISCO artifacts from mixing incompatible modes.

## The four artifact modes

### Tutorial

Goal: help a newcomer learn by doing.

- Focus on a guided path with a deliberate teaching sequence.
- Minimize branches and alternatives.
- Optimize for confidence, not completeness.

In MARISCO:

- A future "hello world" handler walkthrough belongs here.
- A minimal onboarding notebook belongs here.
- Typical home: onboarding-focused material under `nbs/reference/` or a deliberately pedagogical notebook.

### How-to

Goal: help a competent user accomplish a real task.

- Problem-centred, action-centred, and verifiable.
- Show what was done to data and the evidence that it worked.
- Avoid long design digressions.

In MARISCO:

- Handler notebooks are primarily how-to artifacts.
- [handler-doc-guide.md](handler-doc-guide.md) is the operational style guide for this mode.
- Typical home: `nbs/handlers/*.ipynb` and narrowly task-focused workflow notes.

### Reference

Goal: provide stable facts, contracts, and lookup surfaces.

- Be explicit, browsable, and non-narrative.
- Prefer definitions, mappings, field tables, and API surfaces.
- Do not hide facts inside a story.

In MARISCO:

- [docs/architecture.md](../../docs/architecture.md)
- [field-definition.ipynb](field-definition.ipynb)
- enum and rules notebooks when used as canonical facts
- Typical home: stable field, schema, enum, and architecture surfaces that other artifacts link to.

### Explanation

Goal: explain why the design is the way it is.

- Surface tradeoffs, abstractions, and design reasoning.
- Make the architecture more legible.
- Do not turn this into step-by-step instructions.

In MARISCO:

- [sicp-design-memento.md](sicp-design-memento.md)
- [callback-group-dispatch.md](callback-group-dispatch.md)
- Typical home: short design notes that explain tradeoffs without becoming procedures.

## Classification rule

Before writing an artifact, state which one of the four modes it is.

If you cannot classify it, stop and decide before drafting.

## Anti-mixing rule

Common failure modes:

- Tutorial that assumes expert background
- How-to that turns into architecture philosophy
- Reference that hides facts inside prose
- Explanation that quietly becomes a procedure

If two modes are both needed, pick one as the primary artifact and link to the other instead of blending them together.

## MARISCO default mapping

- Handler notebook: `How-to`
- Reference note about fields, enums, or architecture: `Reference`
- Design rationale note about abstraction, callback factoring, or audit trails: `Explanation`
- Beginner walkthrough or intentionally pedagogical notebook: `Tutorial`
