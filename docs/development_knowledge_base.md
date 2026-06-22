# Development Knowledge Base

## 1. Overview

This document consolidates the technical knowledge extracted during the INIS metadata integration and repository cleanup work. It captures four classes of truth that should remain stable for future development:

1. Domain contracts already embedded in MARISCO must be mirrored, not bypassed.
2. External metadata sources are noisy and must be normalized at the boundary.
3. In an nbdev repository, notebook structure is the source of truth and generated artifacts are only projections.
4. Windows and Anaconda environments introduce infrastructure behaviors that must be handled explicitly rather than treated as accidental failures.

The material below combines two viewpoints:

- Human learnings: architectural and domain-level principles clarified during the integration effort.
- AI agent learnings: toolchain, AST, export, indexing, filesystem, and network behaviors that were discovered during implementation and debugging.

## 2. Human Learnings: Design and Domain Principles

### 2.1 Mirror the `GlobAttrsFeeder` Contract Instead of Inventing a Parallel Path

The correct way to add a new metadata source to MARISCO is to conform that source to the existing `GlobAttrsFeeder` callback contract. The real downstream contract is the global-attribute surface, not any single upstream provider.

The practical implication is:

- `id`, `title`, `summary`, and `creator_name` are the canonical core fields.
- `references` and `metadata_link` are also canonical when the metadata source can provide them.
- The output shape and types are more important than the shape of the upstream API.
- `creator_name` is not a Python list in the final contract; it is a JSON string.

This means INIS should be adapted into the shared `obj.attrs` semantics instead of teaching the rest of the pipeline about INIS-specific payload structures.

### 2.2 Put a Defensive Parser Wall at the External API Boundary

InvenioRDM payloads are structurally unstable from the point of view of a downstream data pipeline. They may contain:

- nested multilingual dictionaries instead of plain strings
- personal and organizational creators mixed in the same array
- partially malformed creator entries
- DOI fields represented in more than one place
- API links and HTML links in different keys

The correct engineering response is not to trust the payload and not to let its irregularity leak into the rest of the codebase.

The parser layer should therefore:

- normalize multilingual title and description fields at the boundary
- prefer canonical fields but include safe fallbacks for DOI and URL extraction
- keep creator serialization stable for NetCDF storage
- emit stable strings for all final attribute values

This is technical hospitality: the boundary layer absorbs external ugliness so downstream code can remain simple.

### 2.3 Preserve Non-ASCII Safety Explicitly

Bibliographic metadata routinely contains accented characters and other non-ASCII content. If the boundary layer emits raw Python structures or inconsistent encodings, downstream storage and interchange become fragile.

The concrete rule established here is:

- serialize `creator_name` with `json.dumps(..., ensure_ascii=True)`

This does two things:

1. It preserves semantic content while keeping the serialized attribute stable for storage in systems such as NetCDF global attributes.
2. It keeps the INIS output behavior aligned with the serialized contract expected by the rest of the MARISCO pipeline.

### 2.4 Protect Git History and the Single Source of Truth

Exploration noise, environment-specific breakage, and half-working exports should not be forwarded into the canonical branch history. A clean branch created from the correct upstream base is the safest way to prevent accidental contamination.

This effort reconfirmed the value of:

- doing experimental debugging away from the final PR branch
- rebuilding a clean feature branch from the authoritative parent commit
- treating notebook cells as the only legitimate place for production logic

In an nbdev repository, clean history is not cosmetic. It is part of protecting the correctness of generated code and symbol indexes.

## 3. AI Agent Learnings: Infrastructure, Tools, and OS Constraints

### 3.1 nbdev3 Source of Truth Is a Structural Contract, Not a Preference

The strongest technical constraint discovered in this work is that nbdev does not merely export code; it derives Python modules and documentation indexes from the structural integrity of the notebook.

This has several consequences:

- `nbs/` is the source of truth.
- `marisco/*.py` is generated output and must not be manually edited as a normal workflow.
- `_modidx.py` reflects the exported symbol graph and can become inconsistent if notebook structure is damaged or generated files drift away from their notebook source.

Direct edits to generated modules create two kinds of risk:

1. The immediate code may appear correct locally.
2. The next export can silently overwrite it while leaving the developer with a false sense of completion.

### 3.2 `_modidx.py` Is an Early Warning Surface for AST and Export Integrity

The `_modidx.py` index is not incidental metadata. It is a concrete signal that nbdev successfully discovered and indexed the exported API surface.

When symbols are added for INIS integration, the expected indexed entries should match the actual exported API surface. In the current implementation that includes:

- retrieval helpers such as `fetch_inis` and `find_curl`
- the facade `INISClient`
- callback methods such as `InisCB.__call__`

If these do not appear correctly in `_modidx.py`, the likely causes include:

- notebook cell corruption
- broken export directives
- stale generated files
- symbol definitions no longer discoverable by nbdev's AST walk

The operational lesson is that `_modidx.py` should be audited whenever notebook-exported architecture changes in a non-trivial way.

### 3.3 Windows File Locking Can Break Normal nbdev Rewrite Paths

On Windows, file replacement or unlink behavior is more brittle than on Unix-like systems, especially when Python, editors, or indexing tools still hold handles on generated files.

The specific failure mode encountered in this class of work is `PermissionError` during rewrite or unlink operations. The important lesson is that this is not necessarily a logical error in the code being exported; it can be a filesystem-handle issue at the OS layer.

The robust response pattern is:

- first confirm the notebook and exported code are logically correct
- then treat the write failure as a file-handle problem, not as a parser problem
- if needed, bypass fragile replacement behavior by writing the desired content through a direct stream-based overwrite path

The deeper lesson is that tooling on Windows should be designed with handle retention and delayed release in mind.

### 3.4 Direct Index Regeneration Is Sometimes Safer Than Replaying a Broken Rewrite

When symbol indexing becomes inconsistent or a normal rewrite path is blocked by Windows file-lock behavior, a direct regeneration strategy is safer than repeated ad hoc file surgery.

The principle established here is:

- regenerate from the notebook-derived symbol model
- then write the resulting index content cleanly
- avoid manual patching of `_modidx.py` values unless doing a one-off recovery with full awareness that the notebook remains the upstream truth

This preserves the intended AST-derived relationship between notebook code, exported module, and index artifact.

### 3.5 Python TLS Transport Can Fail Even When the Remote Service Is Healthy

Another important technical truth surfaced during live INIS testing: successful HTTPS access at the infrastructure level does not guarantee that Python's standard transport stack will behave correctly in the local Windows/Anaconda environment.

The actual observed failure class included:

- `TLS/SSL connection has been closed (EOF)`
- connection reset / forced remote close during handshake or response retrieval

These failures occurred even though the target INIS QA endpoint was publicly reachable and returned valid JSON when accessed through the system `curl.exe`.

The lesson is precise:

- network failure symptoms must be localized before changing application logic
- a failing `urlopen()` does not imply a failing API
- transport fallback can be the correct fix, not a hack

### 3.6 `curl.exe` via `subprocess.run` Is the Current INIS Retrieval Path on Windows

The current exported INIS retrieval path is `fetch_inis()`, which shells out to system `curl.exe` through `subprocess.run(...)`.

This pattern has several advantages:

- it decouples business logic from local TLS instability
- it preserves real integration testing against the actual endpoint
- it keeps network adaptation at the retrieval boundary rather than leaking it into encoders or decoders

The broader repository rule about Python TLS failures and `curl.exe` fallback still applies, but richer retry or mock semantics should not be described as current exported behavior unless they are actually present in the client.

### 3.7 Test Design Must Prove Real Retrieval, Not Merely Local Parsing

Mock-based tests are necessary to stabilize contract behavior, but they are insufficient to validate boundary conditions of an external service.

A meaningful live integration test must prove all of the following:

- multiple real record IDs are fetched
- the parser tolerates structural variation across those records
- the final callback output preserves the same type contract as other `GlobAttrsFeeder` metadata callbacks
- optional fields such as `references` and `metadata_link` are well-typed when present

The INIS live bulk validation therefore asserted:

- the existence of the four canonical keys
- strict `str` typing for injected values
- JSON-array validity for `creator_name`
- semantic plausibility of the retrieved metadata payload

This pattern should be reused whenever a new source is integrated behind an existing pipeline contract.

## 4. Lessons for Future Development in MARISCO and Maltilabeler

### 4.1 Normalize New Inputs to Existing Stable Contracts

When a system already has a reliable internal contract, new sources should be adapted to that contract rather than forcing downstream code to learn multiple dialects.

This applies to:

- MARISCO metadata ingestion
- MARISCO data-handler outputs
- Maltilabeler import/export boundaries
- any plugin or callback-oriented architecture

### 4.2 Build Parser Layers as Fault-Containing Boundaries

External data is not trustworthy. The correct place to handle missing keys, malformed records, mixed schemas, and encoding issues is the boundary parser, not the orchestration layer.

Keep the architecture split as follows:

- orchestration layer: sequence and coordination
- adaptation layer: output-shape conversion
- retrieval layer: external IO
- projection layer: injection into the final pipeline contract

This separation keeps failures localized and testable.

### 4.3 Treat Generated Artifacts as Views, Not Authoring Surfaces

Whenever a project uses notebook-driven generation, code generation, AST indexing, or schema-derived artifacts, generated files should be treated as views of an upstream source model.

The rule generalizes beyond nbdev:

- never make a generated file the primary editing surface
- always verify that the upstream generator still owns the final output
- inspect the generated index or manifest as part of integration review

### 4.4 Design Tests That Distinguish Logic Failure from Environment Failure

Tests should separate:

- parser correctness
- callback contract correctness
- export/index correctness
- live transport behavior

If these are mixed into a single opaque test, debugging becomes slow and misleading. Distinct layers of tests make it possible to see whether a failure belongs to:

- the payload
- the parser
- the callback
- the generation toolchain
- the operating system or network stack

### 4.5 Windows-Specific Operational Reality Must Be Planned, Not Ignored

Development workflows that work on Linux or macOS cannot be assumed to behave identically on Windows, especially in Python-heavy environments using notebooks, generated code, and external HTTPS calls.

Two recurring realities must be planned for:

- file-handle and rewrite sensitivity
- TLS stack inconsistency between Python transport and native tools

For future cross-platform development, fallback and recovery paths should be designed intentionally rather than added only after failures occur.

### 4.6 Preserve Technical Knowledge as an Explicit Artifact

Many of the most expensive lessons in this work did not come from algorithm design. They came from invisible operational contracts:

- how the repository really expects new features to be added
- which outputs are canonical
- how to recognize AST/index corruption
- how to tell real network failure from local TLS failure

Those lessons are easy to forget because they are rarely encoded in function signatures. The practical response is to preserve them in durable project documentation so future contributors do not need to rediscover them through destructive trial and error.
