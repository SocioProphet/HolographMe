# Home Privacy Boundaries

## Purpose

Home Privacy Boundaries extend HolographMe from agentic work identity into person-centered governance for smart-home-derived signals.

The boundary is intentionally narrow: HolographMe does not become a raw smart-home telemetry warehouse. It records the governed human and household impact layer: consent, sensitivity, retention, sharing, delegation, audit, and projection limits.

## Position in the stack

Ontogenesis owns the shared vocabulary for smart-home privacy claims, device types, data attributes, physical contexts, evidence records, coverage findings, and risk inferences.

GAIA owns the physical world model: home, room, zone, device, capability, observation, and provenance.

HolographMe owns the human digital twin and consent-governed projection layer: subject, household, role, sensitivity, sharing boundary, retention boundary, delegated-agent authority, and transition receipts.

This keeps the stack from collapsing into uncontrolled surveillance. GAIA can know that a baby monitor emits audio/video in a nursery. HolographMe can know that nursery audio/video is a critical-sensitivity human boundary. Policy Fabric or a downstream runtime decides whether a proposed action is allowed, denied, local-only, or review-required.

## New artifact

This tranche adds:

- `schemas/home-privacy-boundary.schema.json`
- `examples/home-privacy-boundary.example.json`
- validation wiring in `scripts/validate_schemas.py`

## Boundary shape

A Home Privacy Boundary declares:

- the governed subject and optional household;
- physical contexts such as nursery, bedroom, bathroom, entryway, or shared area;
- device types such as baby monitor, camera, door lock, thermostat, water sensor, smart plug, or motion sensor;
- data attributes such as video stream, audio stream, lock status, occupancy signal, water flow, energy use, and connectivity status;
- allowed and forbidden purposes;
- retention posture, including local versus cloud retention;
- sharing posture, including forbidden recipients;
- delegated-agent authority;
- risk posture and evidence bindings;
- audit requirements and transition receipts.

## Example policy posture

For a baby monitor in a nursery:

- default action for audio/video is `local_only`;
- cloud retention is denied by default;
- sharing is denied by default;
- insurers, landlords, employers, advertising networks, and unscoped third parties are forbidden recipients;
- agents may observe policy posture and recommend settings but may not share, retain, or grant third-party access without human review;
- sensitivity tier is `critical`.

## Relationship to existing HolographMe schemas

`human-digital-twin.schema.json` remains the root governed object for subject identity, capability claims, consent-policy IDs, and transition receipts.

`consent-policy.schema.json` remains the general consent projection mechanism.

`home-privacy-boundary.schema.json` is a domain-specific consent boundary for smart-home-derived signals. It should be referenced by consent policy IDs or export bundles once the runtime slice is added.

## Runtime direction

The next executable slice should:

1. read a Home Privacy Boundary, a requested home-signal projection, and the relevant Ontogenesis smart-home privacy references;
2. decide whether each requested field/action is allowed, denied, local-only, or review-required;
3. emit a decision log and transition receipt;
4. preserve evidence bindings without storing raw telemetry by default.

## Guardrail

Home Privacy Boundaries protect people and households from inferred behavioral exposure. They are not permission to collect more home data.
