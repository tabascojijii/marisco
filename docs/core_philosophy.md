# Core Philosophy

## Purpose

This document defines the highest-level principles that guide design, implementation, review, and workflow decisions in `marisco`.

`C:\dev\marisco3\marisco_clean\marisco_repo\docs\requirements.md` defines what must be delivered.
`C:\dev\marisco3\marisco_clean\marisco_repo\docs\reference_standards.md` defines the operational rules.
This document explains the value system behind those rules so that maintainers can make consistent decisions when details are unclear or tradeoffs appear.

## Status

- This document is informative guidance, not a normative workflow contract.
- Audit pass/fail, escalation, evidence, and acceptance decisions must be derived from `docs/requirements.md` and `docs/reference_standards.md`, not from this document alone.
- If this document conflicts with a normative rule in `docs/requirements.md` or `docs/reference_standards.md`, the normative rule takes precedence.

## Project Identity

`marisco` is not just a collection of conversion scripts.
It is a MARIS standardization pipeline for heterogeneous marine radioactivity data.

Its core job is to:

- accept provider-specific and often imperfect input data
- normalize that data into MARIS-compatible structures
- produce reproducible NetCDF and CSV outputs
- preserve enough evidence, metadata, and processing context to explain how those outputs were produced

## Priority Order

When goals conflict, the project should generally prefer:

1. correctness and auditability over convenience
2. explicit contracts over implicit assumptions
3. reproducible outputs over ad hoc local fixes
4. notebook source-of-truth integrity over generated-code convenience
5. user clarity over terse internal-facing behavior
6. controlled commonization over premature abstraction

## Notebook-First Philosophy

This repository uses notebook-first development as a maintainability strategy, not as a stylistic preference.

The notebooks under `nbs/` are expected to serve three roles at once:

- implementation source of truth
- durable technical explanation
- communication surface for provider-specific transformation logic

Generated Python modules under `marisco/` exist for execution and packaging, but they are downstream artifacts.
When behavior changes, the notebook should be treated as the canonical place to express and explain that change.

## Standardization Philosophy

The product is not raw ingestion.
The product is standardization into MARIS-compatible outputs.

Provider data may vary widely in structure, naming, units, metadata quality, and completeness.
That variability is expected.
The system should therefore be designed to absorb provider-specific differences where possible, while still converging toward a strict output contract.

This means:

- inputs may be flexible
- normalization may be provider-specific
- outputs must be standardized

## Data Reality Philosophy

This project operates on messy real-world external data.
That reality should be acknowledged directly rather than designed away on paper.

We should not assume:

- stable upstream layouts
- complete metadata
- consistent naming
- uniform units
- perfect lookup coverage
- always-available remote services

Instead, the code should clearly separate:

- what can be normalized
- what can be warned about
- what must stop the workflow

## Boundary And Normalization Philosophy

Boundaries and transformations serve different purposes.

At boundaries, the system should declare minimum contracts.
Inside handlers and callbacks, the system should perform normalization and provider-specific adaptation.

In practice, that means:

- boundary validation should catch invalid commands, missing prerequisites, and broken workflow contracts early
- handlers should absorb provider-specific structure and naming differences
- callbacks should express reusable transformation steps
- encoders and decoders should enforce output-side consistency

The project should not confuse “valid enough to begin processing” with “already standardized.”

## Fail-Fast Philosophy

Fail fast does not mean rejecting all imperfect data.
It means making contract-breaking conditions visible as early and explicitly as possible.

This repository should fail fast for:

- invalid workflow state
- missing required runtime prerequisites
- invalid audit contracts
- missing required evidence
- user input that is known to be invalid at the CLI boundary

It should not use fail-fast as an excuse to eliminate legitimate provider-side flexibility that handlers are designed to absorb.

## Evidence Philosophy

Evidence is part of correctness.

A result is not trustworthy only because code ran without crashing.
It is trustworthy when:

- the workflow path is known
- the requirements mapping is explicit
- the metadata is attached
- the transformation steps are reconstructable
- the validation outputs are inspectable

This is why audit contracts, artifacts, global attributes, and post-process logs matter in this repository.
They are not secondary documentation; they are part of the product’s reliability model.

## Workflow Philosophy

Automation is welcome only when it remains governable.

The post-commit workflow exists to ensure that:

- role boundaries remain explicit
- state transitions remain inspectable
- invalid downstream routing is prevented
- unresolved loops do not continue indefinitely
- requirements-level defects are escalated instead of being silently pushed downward

The workflow is therefore intentionally contract-driven rather than personality-driven.
It should remain stoppable, inspectable, and evidence-based.

## Escalation Philosophy

Escalation is a safety mechanism, not a process failure.

When the system detects that:

- the requirements are contradictory
- the audit interface is invalid
- the same root problem is cycling repeatedly
- the current role cannot repair the issue without changing upstream intent

the correct action is to escalate clearly rather than continue ambiguously.

The philosophy here is simple:
upstream problems should move upstream.

## User-Facing Philosophy

User confidence is part of quality.

A technically correct pipeline that leaves users confused about:

- what is happening
- whether it succeeded
- what failed
- what to do next

is incomplete.

For that reason, public-facing commands and workflows should aim to:

- validate obvious mistakes early
- communicate progress during non-trivial work
- explain failures with context
- identify produced outputs clearly

## Operational Reality Philosophy

This repository is not “pip install and done.”

Successful operation depends on a combination of:

- Python dependencies
- local initialization through `maris_init`
- runtime assets under `~/.marisco/`
- lookup tables and NetCDF templates
- provider-specific local or remote input data
- external services such as Zotero and GitHub-hosted resources

Operational readiness should therefore be treated as a first-class concern, not as incidental setup trivia.

## Commonization Philosophy

Commonization is valuable when it removes repetition without erasing meaning.

This project should not pursue abstraction merely because multiple handlers look similar.
It should commonize only when the shared behavior is genuinely stable, understandable, and reusable across providers.

The preferred sequence is:

1. document the current pattern accurately
2. identify recurring structure and recurring pain
3. isolate stable shared behavior
4. refactor deliberately

This is why current-state descriptive templates come before broad handler refactoring.

## Maintainer Mindset

When making decisions in this repository, maintainers should think in the following order:

- What contract is being protected?
- What evidence will remain after this change?
- Is the notebook source of truth preserved?
- Is this a boundary problem or a normalization problem?
- Does this make user outcomes clearer or more obscure?
- Does this commonize responsibly, or merely hide complexity?

If those questions are answered well, the implementation is usually moving in the right direction.
