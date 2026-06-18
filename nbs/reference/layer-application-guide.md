# Layer Application Guide For MARISCO

Use this note to decide which design rules are repository-wide and which are specific to notebook-driven pipeline layers.

The purpose is not to spread one writing style everywhere. The purpose is to keep the design kernel consistent while letting each layer use the expression style that fits its job.

## Repository-wide design kernel

Apply these rules across the repository unless a stronger local contract overrides them:

- Preserve the abstraction barrier. Name the user-visible `what`, not the internal `how`.
- Keep interfaces small and responsibilities narrow.
- Preserve or intentionally change the public contract explicitly before implementation.
- Keep defensive programming at boundary surfaces such as file ingress, network retrieval, serialization, and final contract checks.
- Prefer promoting a shared abstraction when the same behavior shape appears repeatedly.
- Treat `nbs/` as SSOT and generated modules as projections.

These are repository-wide because they match the current architecture and exported code across handlers, callbacks, metadata, encoders, configs, and supporting utilities.

## Not repository-wide by default

Do not force the following onto every layer:

- Handler-style `How-to` narration
- Provider-facing prose that explains each data-cleaning step
- Usage cells placed next to every implementation detail
- Callback-per-section notebook presentation as a universal format

These are strong rules for notebook-driven pipeline work, but not for config registries, helper utilities, or projection infrastructure.

## Layer charters

### Handler / Notebook pipeline layers

This is where literate programming is strongest in MARISCO.

- Use `How-to` structure.
- Keep one pipeline concern per section.
- Place evidence near the transformation.
- Let usage cells double as regression tests where that notebook is the natural authoring surface.

Start with [handler-doc-guide.md](handler-doc-guide.md) and [guide.ipynb](guide.ipynb).

### Shared transformation API

This includes shared callbacks, transformer machinery, and parser helpers.

- Prefer small composable callbacks or pure helpers.
- Extract a shared abstraction when multiple handlers repeat the same behavior shape.
- Keep cross-group behavior explicit instead of hiding it behind a per-group abstraction.
- Tests may live in the notebook or shared API surface; they do not need to mimic handler presentation.

Start with [callback-group-dispatch.md](callback-group-dispatch.md) and [sicp-design-memento.md](sicp-design-memento.md).

### Metadata / Overlay layer

- Treat `obj.attrs` as the public contract.
- Keep external retrieval facades thin and contract-driven.
- Keep boundary concerns such as retrieval failures or serialization normalization at the edge.
- Do not force handler-style prose if the main artifact is an API notebook rather than a provider walkthrough.

Start with [docs/architecture.md](../../docs/architecture.md) and the metadata layer section it defines.

### Encoding / Projection layer

- Treat canonical NetCDF output as the primary contract.
- Keep projection helpers small and behavior-specific.
- Verify the canonical surface first; verify CSV only when the compatibility bridge is in scope.
- Prefer structural decomposition over narrative notebook presentation requirements.

Start with [docs/architecture.md](../../docs/architecture.md) and the encoding/projection notebooks it routes to.

### Config / Registry layer

- Favor declarative structure, stable names, and reference-style clarity.
- Optimize for lookup integrity and schema legibility, not step-by-step narration.
- Keep helpers small, but do not force usage-example formatting where the artifact is fundamentally a registry.

Start with [diataxis-memento.md](diataxis-memento.md) and treat this layer primarily as `Reference`.

### Utils / Infrastructure layer

- Avoid kitchen-sink growth.
- Group helpers by boundary or domain when repeated patterns emerge.
- Apply the design kernel strongly, but do not force handler notebook conventions onto generic utilities.

Start with [sicp-design-memento.md](sicp-design-memento.md) for abstraction barriers and interface shape.
