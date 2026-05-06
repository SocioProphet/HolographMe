# HolographMe Governance Model

## Governance objective

HolographMe exists to let a person own and govern their agentic work representation. Governance is therefore not an afterthought. It is the product boundary.

The system must prevent a human digital twin from becoming a platform-owned dossier, an unbounded surveillance profile, or an agentic proxy that can act beyond the person’s intent.

## Non-negotiable rules

1. The person is the subject and owner of the twin.
2. External parties receive scoped projections, not unrestricted access.
3. Consent must be purpose-bound, time-bound, revocable, and auditable.
4. Agentic delegation must declare authority limits.
5. Capability claims must preserve evidence, confidence posture, and event history.
6. Major state transitions must emit receipts or decision logs.
7. High-impact actions require human approval unless explicitly pre-authorized.
8. Revocation must be a first-class operation.
9. Sensitive fields require explicit exposure rules.
10. Governance failures must be inspectable after the fact.

## Consent policy fields

A consent policy should minimally define:

- policy identifier;
- subject identifier;
- allowed recipients;
- allowed purposes;
- allowed fields or projection templates;
- forbidden fields;
- expiration;
- revocation path;
- retention rule;
- delegation permissions;
- audit requirements;
- dispute contact or process.

## Projection discipline

A projection is a bounded view of the twin. It should answer a particular operational need without exposing the entire underlying record.

Examples:

- `mission_fit_projection`: shows capabilities, evidence summaries, availability, and constraints relevant to one mission.
- `assessment_projection`: shows only the fields needed to conduct a competency interview.
- `client_delivery_projection`: shows role, capability, credentials, and engagement-specific identity details.
- `agent_delegate_projection`: shows only the fields an authorized agent needs to represent the person under a specific delegation.

Every projection attempt should have an auditable decision record. A successful projection records allowed, denied, missing, and forbidden fields. A rejected projection records request-level denial reasons such as expired consent, mismatched subject, unapproved recipient, or unapproved purpose.

## Agentic delegation

Delegation should be explicit and granular.

| Delegated action | Default posture |
| --- | --- |
| Read consented fields | Allowed only inside projection scope. |
| Summarize or classify evidence | Allowed with audit logging. |
| Recommend missions or training | Allowed with explanation. |
| Schedule interviews | Allowed if the person authorizes calendar/availability use. |
| Answer screening questions | Allowed only from approved fields or scripted authority. |
| Negotiate rate or terms | Human review required unless pre-authorized. |
| Accept work | Human approval required by default. |
| Disclose sensitive attributes | Explicit approval required. |

Delegation is executable, not merely descriptive. A delegated agent must be listed on the twin, the requested action must be allowed, the delegation must be unexpired, and the granted authority band must satisfy the required action band.

## Capability claim lifecycle

Capability claims are not permanent truth. They are current-state summaries derived from event history.

A claim can move through these statuses:

- `self_attested`: the subject asserted the capability.
- `evidence_attached`: evidence exists, but it is not yet verified.
- `verified`: an authorized review has accepted the claim for bounded use.
- `disputed`: a subject, reviewer, client, or governance actor challenged the claim.
- `expired`: evidence or verification aged out and needs renewal.
- `retired`: the subject or governance process removed the claim from active use.

Status transitions should be recorded as capability claim events. Events include claim creation, evidence attachment, review, status change, expiration, and retirement. Retired claims are terminal: they may remain in history, but they should not be revived silently for mission-fit use.

This rule prevents old assessments from becoming permanent automated scars and prevents stale claims from being treated as fresh capability.

## Transition receipts

Control-grade changes should produce receipts. A receipt should include:

- receipt identifier;
- twin identifier;
- action type;
- actor;
- timestamp;
- policy version;
- previous state hash;
- new state hash;
- evidence links;
- approval band;
- rollback or compensation path;
- replay hints.

## Sensitive data posture

The schema should treat the following as sensitive by default:

- legal identity;
- government identifiers;
- health and disability data;
- immigration or work-authorization data;
- precise home location;
- compensation floor and hardship constraints;
- protected class attributes;
- private references;
- raw interview transcripts;
- psychological, biometric, or behavioral inference data.

A projection should include sensitive fields only when the purpose and recipient justify it and the person has explicitly consented.

## Dispute and correction

The person must be able to challenge, correct, suppress, or contextualize claims and evidence. A false or stale assessment should not become a permanent automated scar.

## Audit posture

The governance layer should be capable of answering:

- Who saw what?
- Why were they allowed to see it?
- Which policy version applied?
- Which agent or human acted?
- What changed?
- What evidence supported the change?
- Can the decision be replayed?
- Can the state be corrected or revoked?

## First conformance target

The initial repo conformance target is modest: schemas, examples, validation, event logs, and bounded runtimes. A valid HolographMe object must be parseable, consent-scoped, and auditable enough to support a mission-fit projection without leaking the full twin.
