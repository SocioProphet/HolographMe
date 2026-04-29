# HolographMe Architecture

## Architectural intent

HolographMe turns the human digital twin into a governed, portable, verifiable work object. The architecture is designed around a machine bridge: typed records, explicit source discipline, transition rules, conformance manifests, bounded authority, replay, rollback, and audit evidence.

## Core objects

### HumanDigitalTwin

The owned representation of a person’s work-self. It contains identity references, capability claims, evidence pointers, credentials, portfolio artifacts, preferences, constraints, reputation, assessment history, delegation rules, and state-transition receipts.

### CapabilityClaim

A claim that the person can perform a defined capability at a defined level under defined conditions. It must be separable from evidence. A claim without evidence may exist, but the system must not treat it as verified.

### EvidenceArtifact

A provenance pointer supporting a claim, assessment, credential, work outcome, reference, or mission result. Evidence should include source type, URI or digest, issuer, collection time, trust posture, legal-use tags, and retention constraints.

### ConsentPolicy

A policy object that governs projection, matching, assessment, delegation, negotiation, sharing, retention, revocation, and audit requirements.

### Projection

A consent-scoped view of a twin. A consulting agency, client, or agent should receive projections, not raw unrestricted access to the full twin.

### Mission

A bounded work opportunity requiring capabilities, roles, constraints, governance posture, compensation posture, and acceptance evidence.

### TransitionReceipt

The audit object for control-grade changes. It records actor, action, previous state hash, new state hash, policy version, evidence pointers, approval band, and replay hints.

## Planes

| Plane | Responsibility |
| --- | --- |
| Identity plane | Person ownership, wallet/account linkage, subject identifiers, portability, and revocation hooks. |
| Capability plane | Claims, skill taxonomies, evidence, credentials, assessments, and mission outcomes. |
| Consent plane | Policies, scopes, projections, allowed purposes, expiration, revocation, and retention. |
| Agent delegation plane | Agents authorized to interview, negotiate, recommend, schedule, represent, or supervise under explicit limits. |
| Workgraph plane | Missions, teams, roles, clients, work packages, outcomes, reputation, and feedback loops. |
| Governance plane | Approval bands, audits, conformance manifests, replay, rollback, dispute handling, exploit controls, and policy versioning. |

## Bounded runtime slice

The first runtime slice should implement a narrow loop:

1. Register or import a human digital twin.
2. Add capability claims and evidence artifacts.
3. Attach a consent policy.
4. Run an interview or assessment event.
5. Produce a mission-fit projection.
6. Emit a transition receipt.
7. Validate the objects and store a signed or hash-linked record.

This slice is deliberately bounded. It proves the bridge between doctrine and implementation without claiming broad autonomous authority.

## State discipline

Control-grade state must declare:

- stable identifier;
- owner or steward;
- source class;
- evidence pointer;
- update cadence or event trigger;
- freshness expectation;
- confidence posture;
- legal-use constraints;
- aggregation or reconciliation rule;
- recovery path if stale, contradictory, or unavailable.

## Authority model

Agents may act on behalf of a twin only through declared delegation. Each delegated action should have an authority band.

| Band | Example | Required control |
| --- | --- | --- |
| Observe | Read consented fields, classify capability evidence, summarize a portfolio. | Consent scope and log entry. |
| Recommend | Suggest missions, training, rates, or interview pathways. | Explanation and reviewability. |
| Represent | Answer constrained screening questions or schedule interviews. | Delegation rule, expiration, and transcript. |
| Negotiate | Propose terms or compensation ranges. | Human approval unless explicitly pre-authorized. |
| Commit | Accept mission, disclose sensitive data, bind compensation. | Human approval or explicit high-authority delegation with receipt. |

## Replay and rollback

Every transition that changes the twin, consent state, mission state, reputation, or delegation authority must be replayable. Where rollback is possible, the rollback path must be recorded. Where rollback is impossible, the system must require explicit irreversible-action acknowledgement.

## Federation model

HolographMe should not assume one global platform owns all worker data. The intended pattern is federated:

- local twins retain source intimacy and ownership;
- projections move through consented envelopes;
- workgraph systems consume bounded summaries and evidence packets;
- governance systems audit action without requiring total centralization.

## Implementation posture

The repository begins with JSON Schemas and validation scripts because schema discipline is the lowest-friction way to prevent uncontrolled narrative drift. Later implementation can add services, APIs, UI, wallets, identity providers, credential standards, graph databases, event logs, and agent runtimes.
