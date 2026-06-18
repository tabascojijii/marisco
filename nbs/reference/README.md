# Reference Dispatch

This folder is the thin reference harness for MARISCO contributors and AI agents.

Read this folder as a dispatch table, not as a linear manual:

1. Read [docs/architecture.md](../../docs/architecture.md) first to identify the target layer.
2. Read [layer-application-guide.md](layer-application-guide.md) if you need to know whether a rule is repository-wide or specific to one layer.
3. Then read only the smallest reference note that matches the task.
4. Before implementation, state the target layer, public contract, references loaded, and one constraint extracted from them.

## MARISCO engineering canon

When a task mentions fastcore style, literate programming, SICP, or "the Franck way", treat that as a request for the MARISCO engineering canon and use the following compressed reading:

- Repository-wide kernel: abstraction barriers, small public surfaces, explicit contracts, and boundary-scoped defenses. Start with [layer-application-guide.md](layer-application-guide.md) and [sicp-design-memento.md](sicp-design-memento.md).
- Single responsibility in transformation code: prefer one transformation concern per callback, section, or helper. Start with [callback-group-dispatch.md](callback-group-dispatch.md).
- Defensive programming, but not too far: keep robustness at boundary surfaces and explicit contract checks, not as speculative branching in core logic. Start with [docs/architecture.md](../../docs/architecture.md).
- Handler-specific expression style: tests near example cells, `How-to` narration, and visible evidence are strong rules for notebook-driven pipeline layers, not for every artifact. Start with [handler-doc-guide.md](handler-doc-guide.md), [diataxis-memento.md](diataxis-memento.md), and [layer-application-guide.md](layer-application-guide.md).

After reading, state the target layer, the public contract, and the smallest proof you expect to produce.

## Task routing

### I need to decide where code belongs

- Read [docs/architecture.md](../../docs/architecture.md).
- Read [layer-application-guide.md](layer-application-guide.md) if you are unsure whether the style rule is global or layer-specific.
- Then read [sicp-design-memento.md](sicp-design-memento.md) for abstraction barriers and naming the `what`.

### I need to reproduce or review a Franck-style refactor

- Read this `MARISCO engineering canon` section first.
- Then read [sicp-design-memento.md](sicp-design-memento.md), [handler-doc-guide.md](handler-doc-guide.md), and [callback-group-dispatch.md](callback-group-dispatch.md).
- Use [docs/architecture.md](../../docs/architecture.md) to confirm the target layer and contract before comparing implementations.

### I need to add or refactor a handler notebook

- Read [guide.ipynb](guide.ipynb) for handler anatomy and completion criteria.
- Read [handler-doc-guide.md](handler-doc-guide.md) for notebook layout, callback presentation, and tests-as-usage-examples.
- If the change may promote a shared callback abstraction, also read [callback-group-dispatch.md](callback-group-dispatch.md).

### I need to refactor callbacks or shared transformation logic

- Read [callback-group-dispatch.md](callback-group-dispatch.md).
- Then read [sicp-design-memento.md](sicp-design-memento.md) to keep the abstraction barrier explicit.

### I need to work outside handlers but still follow the design kernel

- Read [layer-application-guide.md](layer-application-guide.md) first.
- Then read [docs/architecture.md](../../docs/architecture.md) to confirm the target layer and contract.
- Apply the repository-wide kernel even if the artifact is not a handler notebook.

### I need to work on metadata or encoding without forcing handler notebook style

- Read [layer-application-guide.md](layer-application-guide.md).
- Then read [docs/architecture.md](../../docs/architecture.md) and follow the layer route it defines.
- Keep `obj.attrs`, canonical NetCDF, or compatibility projection as the contract surface rather than copying handler presentation rules.

### I need to work on config or registry surfaces

- Read [layer-application-guide.md](layer-application-guide.md) first.
- Treat the artifact primarily as `Reference`, not as a handler-style walkthrough.
- Prove lookup, schema, naming, or reference-surface integrity without forcing usage-cell formatting onto the registry.

### I need to work on utils or infrastructure without forcing handler notebook style

- Read [layer-application-guide.md](layer-application-guide.md) first.
- Then read [sicp-design-memento.md](sicp-design-memento.md) to keep the helper boundary and public surface explicit.
- Prove the extracted responsibility or helper behavior on the smallest natural verification surface for that utility.

### I need to confirm the public contract before changing code

- Read [docs/architecture.md](../../docs/architecture.md) first.
- Then read the smallest task note that describes the behavior surface you are changing.
- State the contract in user-visible terms and name the proof you will produce.

### I need to write or restructure documentation

- Read [diataxis-memento.md](diataxis-memento.md) first to classify the artifact.
- Then read the relevant task note:
  - Tutorial: start from [guide.ipynb](guide.ipynb)
  - How-to: start from [handler-doc-guide.md](handler-doc-guide.md)
  - Explanation: start from [sicp-design-memento.md](sicp-design-memento.md) or [callback-group-dispatch.md](callback-group-dispatch.md)
  - Reference: start from the authoritative schema or architecture source

### I need field, enum, or data-rule facts

- Read [field-definition.ipynb](field-definition.ipynb).
- Read [data-curation-rules.ipynb](data-curation-rules.ipynb) or [enum_rules.ipynb](enum_rules.ipynb) if the task is rule-specific.

### I need sample identity or uniqueness guidance

- Read [sample-id-coverage.ipynb](sample-id-coverage.ipynb).
- Read [sample-uniqueness.ipynb](sample-uniqueness.ipynb).

## Usage rule

Do not read everything in this folder by default. Use this page to select one or two references that match the task, then stop.
