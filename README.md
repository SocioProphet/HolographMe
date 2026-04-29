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
.github/workflows/validate.yml      Schema validation workflow
docs/product-brief.md               Product and market framing
docs/architecture.md                System architecture and bounded-control posture
docs/governance.md                  Consent, ownership, audit, and agentic delegation model
docs/operating-model.md             Intake-to-mission lifecycle and consulting-agency workflow
schemas/human-digital-twin.schema.json
schemas/consent-policy.schema.json
schemas/mission.schema.json
scripts/validate_schemas.py
```

## Initial runtime slice

The first implementation slice should be narrow:

1. create a human digital twin record;
2. attach capability claims and evidence;
3. define a consent policy;
4. run a competency interview or assessment;
5. generate a governed mission-fit projection;
6. emit an auditable state-transition receipt.

This slice is intentionally smaller than the full labor coordination system. It gives the repository an executable bridge without pretending to run the world on day one.

## Status

This repository is at inception. The immediate objective is to codify the product thesis, governance model, schemas, and first validation harness so implementation can proceed from a clean foundation.
