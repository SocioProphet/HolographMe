# HolographMe Product Brief

## One-line description

HolographMe is a self-owned human digital twin for agentic work: a governed, portable, agent-readable representation of a person’s capabilities, proofs, preferences, consent rules, reputation, and work trajectory.

## Problem

Labor platforms typically solve for platform control. They own the profile, own the marketplace state, own the matching surface, and reduce the person to a searchable record. Consulting firms solve for client delivery, but their talent systems remain internally fragmented across resumes, interviews, staffing spreadsheets, manager knowledge, credentials, and project histories.

Agentic work makes this worse if it is not governed. A person can be represented by agents, assessed by agents, routed by agents, and supervised by agents without a coherent model of ownership, consent, authority, audit, and compensation.

HolographMe exists to prevent that failure mode.

## Product thesis

Every person should own a governed work-self that can safely participate in an agentic economy.

That work-self is not a resume. It is a human digital twin with:

- verified capability claims;
- evidence and provenance;
- consent and revocation rules;
- preferred work modes, constraints, and compensation posture;
- credential and portfolio links;
- assessment and interview outputs;
- reputation and mission outcomes;
- delegated agents and authority limits;
- audit receipts for control-grade changes.

## Primary users

### Individual worker

The person who owns the twin. They use HolographMe to represent themselves, prove competence, govern how agents act on their behalf, and participate in meaningful work without surrendering their identity to a platform.

### Agentic consulting agency

The organization that uses consent-scoped twin projections to evaluate, staff, supervise, and improve human-agent consulting teams.

### Client or mission sponsor

The party that needs trusted capability, governed delivery, explainable staffing, and auditable outcomes.

### Governance operator

The person or agent responsible for policy enforcement, dispute handling, consent integrity, audit review, and conformance evidence.

## Product boundary

HolographMe is not the entire labor market. It is the individual-owned primitive and governance object. It can plug into marketplaces, consulting agencies, enterprise staffing systems, public-good missions, training platforms, and workgraph coordination layers.

## Non-goals for the first slice

The first slice should not attempt to automate employment, compensation, tax, labor-law classification, or global workforce compliance. Those are downstream governance domains. The first slice should establish the governed identity object, consent projection, capability evidence, and auditable transition model.

## Initial capabilities

1. Create a human digital twin record.
2. Add capability claims with evidence.
3. Define consent-scoped projections.
4. Record assessment or interview events.
5. Generate mission-fit views without exposing the full twin.
6. Record state-transition receipts.
7. Validate core objects against public schemas.

## Strategic wedge

The wedge is agentic consulting intake and staffing. Candidates arrive through an agentic interview flow. The system builds or updates their HolographMe twin. The consulting agency receives a governed projection rather than unrestricted ownership of the person’s profile. Missions are staffed from verified, consented capability.

## Success criteria for v0.1

- A person can create and export a valid human digital twin document.
- A consent policy can express who may see what, for what purpose, for how long, and under which revocation rules.
- A mission-fit object can be produced without leaking the full twin.
- Every control-grade state change can emit a receipt with actor, timestamp, policy version, source evidence, previous state hash, and new state hash.
- CI validates schemas and examples.
