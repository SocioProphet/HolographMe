# HolographMe Agent Operating Instructions

## Mission boundary

HolographMe is the self-owned human digital twin governance layer for agentic work. Agents working in this repository must preserve that boundary.

Do not turn the project into a platform-owned profile system, a generic recruiting app, or an unbounded autonomous staffing agent.

## Non-negotiable constraints

- The person owns the twin.
- External parties receive consent-scoped projections, not raw unrestricted twin access.
- Capability claims must preserve evidence, confidence, and reviewability.
- Agent delegation must be explicit, scoped, expiring, and revocable.
- Sensitive fields must be denied by default.
- State changes that affect identity, consent, delegation, capability, projection, reputation, or mission status require auditable receipts or decision logs.
- Do not invent evidence, credentials, assessments, customers, legal claims, benchmarks, or production status.
- Keep examples synthetic unless explicitly importing real data under a documented consent boundary.

## Required validation for code changes

Run or preserve CI coverage for:

```bash
python scripts/validate_schemas.py
python -m unittest discover -s tests
```

Any new schema must include at least one example. Any new runtime behavior must include tests.

## Schema discipline

When changing schemas:

- preserve explicit `schema_version` behavior;
- keep `additionalProperties: false` unless a clear extension boundary is needed;
- add examples under `examples/`;
- add validation mappings in `scripts/validate_schemas.py`;
- update tests if runtime output changes.

## Governance discipline

When changing consent, projection, or delegation logic:

- add allow and reject tests;
- include clear rejection reasons;
- avoid silent redaction where an auditable decision should exist;
- update docs if the behavior changes user-visible governance semantics.

## Pull request expectations

Every PR should state:

- what changed;
- which governance boundary it affects;
- which schemas/examples/tests were updated;
- how to validate the change;
- what was intentionally left out.

Do not merge behavior-changing work without tests.
