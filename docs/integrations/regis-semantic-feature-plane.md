# Regis Semantic Feature Plane Integration

This document defines the bridge from HolographMe consent-scoped projections into the Regis Semantic Feature Plane.

HolographMe remains the self-owned human digital twin root. Regis consumes only generated projection artifacts and their decision logs. Regis does not own the person, the full twin, or raw private twin state.

## Flow

Prime Identity -> HolographMe Human Digital Twin -> Consent-Scoped Projection -> Regis Semantic Feature Plane -> GAIA World Model Surface -> Agent or mission workflow.

## HolographMe responsibilities

HolographMe owns the twin state, consent policies, missions, projections, projection decision logs, transition receipts, capability claim lifecycle, and delegated authority checks.

## Regis responsibilities

Regis owns downstream twin projection features, feature assertions, embedding cards, graph indexing, promotion decisions, revocation propagation, tombstones, and retention enforcement.

## Export adapter

The export adapter reads a Projection and ProjectionDecisionLog, with optional ConsentPolicy, Mission, and TransitionReceipt inputs. It emits TwinProjectionFeature records.

Each exported feature preserves projection identity, twin identity, subject identity, mission context, recipient context, consent scope snapshot, mission governance snapshot, transition receipt reference, projection decision log reference, source field path, source field decision, retention rule, revocation state, effective authority band, and policy state.

## Invariants

1. No raw twin state is exported outside generated projections.
2. Policy-blocked fields are not emitted as features.
3. Every feature references the projection decision log that allowed its source field.
4. Consent purpose, recipient, expiry, retention, revocation, delegation, and audit rules travel downstream.
5. Mission authority, human approval, audit, and conformance context travel downstream.
6. Effective authority is downgraded to the lowest available upstream authority band.
7. Revoked or expired consent blocks or restricts downstream use.
8. Regis may index consent-scoped projections, but it does not own the person or the full twin.

## Effective authority

Authority order is observe, recommend, represent, negotiate, commit. The effective authority band is the minimum of consent delegation maximum authority, mission governance authority, delegated-agent authority if known, transition receipt approval band, and downstream policy gate authority if known.

## CLI

Generate a projection with scripts/generate_projection.py. Export Regis features with scripts/export_regis_features.py using projection, decision log, consent policy, mission, and receipt inputs.

## Status

This repository contains the first runtime slice for projection-to-feature export. Canonical Regis schemas should live in SocioProphet/prophet-core-contracts. HolographMe exports should stay compatible with those contracts.
