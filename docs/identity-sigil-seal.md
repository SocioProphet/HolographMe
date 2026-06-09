# Identity Sigil Seal v0.1

## Status

Design and executable contract target for HolographMe identity presentation, signing authority, delegation, and contextual reputation.

This document adapts the useful part of Urbit-style sigils: a human-recognizable emblem for an otherwise abstract cryptographic identity. It does not adopt the ship/runtime model.

## Purpose

A person needs a recognizable identity presentation that can be cryptographically bound to a governed human digital twin without reducing the person to a wallet, account, portrait, score, agent, or platform profile.

The Identity Sigil Seal is the bridge between:

- a subject-owned HolographMe twin;
- a visual sigil;
- an optional portrait;
- scoped signing authorities;
- consent policy references;
- agent delegation references;
- contextual reputation references;
- transition receipts and graph/proof materialization.

## Doctrine

A sigil is a human-recognizable emblem.

A seal is a cryptographic commitment.

A signing authority is a scoped controller.

A delegation is bounded agency.

A reputation record is contextual evidence.

A portrait is optional presentation, not biometric truth by default.

A person is never reduced to any of these.

## Position in HolographMe

HolographMe already has the governed twin, consent-scoped projection, delegated-agent checks, transition receipts, capability evidence, and projection-loss profile discipline.

The Identity Sigil Seal adds the missing presentation/control binding:

```text
HumanDigitalTwin
  -> IdentitySigilSeal
  -> SigningAuthorityBinding
  -> AgentDelegationSeal / delegated_agents
  -> TransitionReceipt / action receipts
  -> ContextualReputationCredential
  -> Projection / SigilProjectionProfile
```

The seal should remain a bridge object. It must not become a universal identity database.

## Minimum object family

The first implementation tranche should include:

- `IdentitySigilSeal`
- `SigningAuthorityBinding`
- `AgentDelegationSeal`
- `ContextualReputationCredential`
- `SigilProjectionProfile`

The current v0.1 schema starts with `IdentitySigilSeal` and embeds lightweight signing authority, portrait policy, delegation, and reputation refs. Later tranches can split those into standalone schemas once the record family stabilizes.

## Required boundaries

The following must remain non-negotiable:

- the seal must reference a HolographMe subject and twin;
- the sigil artifact must be hash-bound;
- portrait linkage must declare whether biometric identity is claimed;
- signing authorities must have explicit scopes;
- delegations must be referenced, scoped, expiring, or revocable;
- reputation references must be contextual;
- transition receipts must record control-grade changes;
- non-claims must explicitly reject person/account/wallet/portrait/agent/reputation collapse.

## Positive example

A valid seal may say:

```text
This subject-owned twin presents this sigil, optionally presents this portrait under a non-biometric policy, uses these scoped signing authorities, delegates these bounded actions to named agents, and exposes these contextual reputation references under consent.
```

## Forbidden examples

A seal must be rejected when it says or implies:

- wallet equals person;
- portrait equals biometric proof by default;
- agent action equals direct human action without delegation;
- reputation equals global human worth;
- one public projection links every context;
- signing authority has no scope;
- delegation has no expiry or revocation posture;
- transition history can be erased.

## Cross-repo alignment

- `identity-is-prime-reference`: formal identity-prime decomposition, policy-vetoed merges, proof artifact posture.
- `regis-entity-graph`: graph materialization of sigil, seal, authority, delegation, projection, and reputation relations with epistemic edge typing.
- `human-digital-twin`: Ω readiness and policy gating for exporting sigil/projection/reputation artifacts.
- `HolographMe`: product-facing twin, consent, projection, delegation, reputation, and transition receipt implementation.

## Non-claims

This document does not define personhood.

This document does not authorize biometric identification.

This document does not make a wallet, account, portrait, agent, score, or reputation record equivalent to a person.

This document does not implement production cryptography.

This document defines the first governed contract surface so implementation does not become identity soup in a trench coat.
