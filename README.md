# HolographMe

**HolographMe** is the self-owned human digital twin governance layer for agentic work.

The product gives each person a portable, consent-governed, agent-readable representation of their capability, reputation, preferences, credentials, work history, proofs, and delegated agent permissions. The goal is not to create another recruiting profile or staffing marketplace. The goal is to let people own and govern their agentic work-self while participating in a holographic labor system that can form teams, staff missions, verify competence, supervise delivery, and improve from outcomes.

## Core thesis

The old labor market reduces people to resumes, job titles, and platform-owned profiles. HolographMe treats the worker as the owner of a governed human digital twin.

A HolographMe twin can:

- represent a person's verified capabilities, credentials, portfolio artifacts, preferences, and constraints;
- participate in competency-based interviews and assessments;
- expose consent-scoped views to consulting agencies, clients, agents, and institutions;
- negotiate or recommend work under explicit delegation limits;
- produce provenance, replay, and audit evidence for major state changes;
- preserve individual agency while enabling world-scale work coordination.

## Architectural position

HolographMe is designed as the individual-owned primitive inside the broader SocioProphet work stack.

| Layer | Role |
| --- | --- |
| HolographMe | Self-owned human digital twin for agentic work identity and consent governance. |
| Human Digital Twin | The governed object: capability graph, proofs, preferences, credentials, reputation, constraints, and delegated permissions. |
| Workgraph / HoloWorks | Coordination layer for missions, staffing, teams, clients, delivery, and learning loops. |
| Governance Mesh | Policy, consent, audit, conformance, review, rollback, dispute handling, and provenance. |

## Design principles

1. **Self-ownership first.** The person owns the twin. The platform may host, index, verify, or route consented projections, but it must not treat the twin as platform property.
2. **Consent-scoped projection.** Every external use of the twin must be mediated by explicit scope, purpose, duration, revocation, and evidence rules.
3. **Competence over credentials alone.** Credentials matter, but the system must also model demonstrated ability, proofs of work, simulations, references, tests, and mission outcomes.
4. **Agentic delegation with limits.** A twin may be represented by agents, but those agents require bounded authority, review bands, and revocation paths.
5. **Holographic composition.** Each person carries a portable local whole: capability, context, governance, and evidence. Larger teams and institutions are composed from these governed local wholes.
6. **Replayable governance.** Control-grade state transitions must be reconstructable from source evidence, policy version, actor authority, and transition rules.
7. **No magical autonomy.** The system must earn authority through bounded runtime slices, explicit approvals, and safe degraded modes.

## Repository contents

```text
.github/workflows/validate.yml      Schema, runtime, and CLI validation workflow
holographme/projection.py           Consent-scoped projection runtime
holographme/delegation.py           Delegated-agent permission checks
holographme/capability.py           Capability-claim event lifecycle runtime
scripts/generate_projection.py      CLI wrapper for mission-fit projections
scripts/capability_event.py         CLI wrapper for capability-claim events
scripts/validate_schemas.py         JSON Schema/example validator
scripts/validate_projection_loss_profile.py  Projection-loss profile invariant validator
tests/test_projection.py            Projection runtime tests
tests/test_delegation.py            Delegation runtime tests
tests/test_capability.py            Capability event runtime tests

docs/product-brief.md               Product and market framing
docs/architecture.md                System architecture and bounded-control posture
docs/governance.md                  Consent, ownership, audit, and agentic delegation model
docs/operating-model.md             Intake-to-mission lifecycle and consulting-agency workflow
docs/projection-loss-profiles.md    Projection source-basis, loss-profile, and allowed-use doctrine

schemas/human-digital-twin.schema.json
schemas/consent-policy.schema.json
schemas/mission.schema.json
schemas/projection.schema.json
schemas/projection-decision-log.schema.json
schemas/capability-claim-event.schema.json
schemas/labor-coordination-record.schema.json
schemas/transition-receipt.schema.json

examples/human-digital-twin.example.json
examples/consent-policy.example.json
examples/mission.example.json
examples/projection.example.json
examples/projection-decision-log.example.json
examples/projection-decision-log.rejected.example.json
examples/projection-loss-profile.example.json
examples/capability-claim-event.example.json
examples/capability-claim-event.append.example.json
examples/labor-coordination-record.example.json
examples/transition-receipt.example.json
```

## Executable slices

### Mission-fit projection

The projection slice:

1. reads a human digital twin, consent policy, and mission;
2. generates only fields allowed by consent;
3. denies and explains unauthorized, missing, forbidden, or request-level rejected fields;
4. emits a mission-fit projection;
5. emits a projection decision log;
6. emits a transition receipt.

The generated projection includes only consented fields. In the example, `assessments.summary` is requested by the mission but denied because the consent policy does not allow it.

### Projection loss profile

Projection loss profiles describe what a projection is based on, what it omits, how it compresses the source, and what decisions it may or may not support.

The first profile lane lives at:

- `docs/projection-loss-profiles.md`
- `examples/projection-loss-profile.example.json`
- `scripts/validate_projection_loss_profile.py`

The example records source refs, channel refs, selection criteria, denied fields, loss modes, freshness posture, consent policy refs, evidence refs, allowed uses, disallowed uses, repair requirements, and non-claims.

The projection-loss profile is enforced by a schema-light invariant validator that is called by `scripts/validate_schemas.py`. Formal JSON Schema for this profile remains deferred because the schema write was blocked by the connector safety layer.

### Capability-claim lifecycle

The capability slice:

1. reads a human digital twin, capability event log, and new capability event;
2. validates legal lifecycle transitions;
3. rejects illegal status changes and duplicate event ids;
4. appends the event to the event log;
5. optionally writes an updated twin copy with derived claim status;
6. emits a transition receipt with claim id, event id, previous status, and new status.

Capability claims are not permanent truth. They are current-state summaries derived from auditable event history.

## Local validation

```bash
python3 -m pip install --user jsonschema
python3 scripts/validate_schemas.py
python3 -m unittest discover -s tests
```

## Generate a mission-fit projection

```bash
python3 scripts/generate_projection.py \
  --twin examples/human-digital-twin.example.json \
  --consent examples/consent-policy.example.json \
  --mission examples/mission.example.json \
  --out generated/projection.json \
  --receipt-out generated/receipt.json \
  --decision-log-out generated/decision-log.json \
  --now 2026-05-04T18:30:00Z \
  --receipt-id tr_projection_001 \
  --decision-log-id pdl_projection_001
```

## Append a capability-claim event

```bash
python3 scripts/capability_event.py \
  --twin examples/human-digital-twin.example.json \
  --event-log examples/capability-claim-event.example.json \
  --event examples/capability-claim-event.append.example.json \
  --out generated/capability-event-log.json \
  --receipt-out generated/capability-receipt.json \
  --twin-out generated/capability-twin.json \
  --receipt-id tr_ccev_claim_expired_001
```

## License

Apache-2.0. See `LICENSE`.

## Status

The repo has crossed from inception docs into an executable bridge: schemas, examples, validation, consent-scoped projection, projection decision logs, delegation checks, capability-claim event lifecycle, transition receipts, tests, and CI. Projection-loss profile doctrine, an example profile, and schema-light invariant validation are now present; formal JSON Schema enforcement for that profile remains deferred.
