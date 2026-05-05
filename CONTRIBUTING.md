# Contributing to HolographMe

HolographMe is public because the ownership and governance model must be inspectable.

## Contribution priorities

The early project priority order is:

1. schema correctness;
2. consent and governance clarity;
3. replayable transition receipts;
4. narrow executable slices;
5. product surfaces and UX;
6. integrations with workgraph, agent, credential, and consulting workflows.

## Ground rules

- Do not add platform-owned profile assumptions.
- Do not add unbounded agent authority.
- Do not expose sensitive personal fields by default.
- Do not treat assessment inference as permanent truth.
- Prefer explicit schemas, examples, tests, and receipts over narrative-only changes.
- Any feature that changes twin state, consent state, delegation authority, or reputation must describe its transition receipt behavior.

## Pull request checklist

- [ ] The change preserves self-ownership and consent-scoped projection.
- [ ] New or changed JSON examples validate locally.
- [ ] New fields are documented in the relevant schema or doc.
- [ ] Sensitive data behavior is explicit.
- [ ] Transition, replay, rollback, or correction behavior is described where relevant.

## Local validation

```bash
python -m pip install jsonschema
python scripts/validate_schemas.py
```
