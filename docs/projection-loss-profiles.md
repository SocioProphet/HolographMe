# Projection loss profiles v0.1

## Status

Contract-only companion lane for HolographMe consent-scoped projections.

This tranche consumes ProCybernetica Reciprocal Channel Governance and the Ontogenesis `rcg:` semantic mirror. It does not replace `schemas/projection.schema.json`, `schemas/projection-decision-log.schema.json`, the projection runtime, consent policies, delegation checks, or transition receipts.

## Purpose

A projection is a lossy rendering of a larger state for a human, agent, client, institution, dashboard, or runtime consumer. A mission-fit projection, dashboard panel, graph slice, summary, memory card, agent handoff, or export bundle can feel complete while omitting evidence, denied fields, source channels, uncertainty, stale context, and intended use limits.

HolographMe already enforces consent-scoped field inclusion. Projection loss profiles add the missing interpretability layer: what this projection is based on, what it omitted, how it compressed the source, and what decisions it may or may not support.

## Rule

No projection without source basis and loss profile.

No projection may support high-consequence decisions beyond its declared allowed uses, source coverage, freshness window, and consent/policy basis.

## Projection profile requirements

A projection profile should declare:

1. projection reference;
2. projection kind;
3. source corpus or source object refs;
4. contributing channels;
5. projection method;
6. selection criteria;
7. omitted fields or denied fields;
8. loss modes;
9. freshness window;
10. consent/policy basis;
11. evidence refs;
12. confidence type and level;
13. allowed uses;
14. disallowed uses;
15. repair or revalidation path;
16. non-claims.

## Forbidden projection uses

A projection must be rejected or kept advisory-only when:

- it omits source basis;
- it omits loss profile;
- it presents denied fields as absent rather than withheld;
- it claims whole-twin coverage from a scoped projection;
- it supports hiring, contracting, policy, legal, publication, or agent-action decisions without explicit allowed use;
- it is stale and lacks revalidation;
- it hides model/agent summary compression behind fluent prose;
- it is generated from a graph slice, summary, dashboard, or memory card without declaring projection method and omitted context.

## Runtime non-claim

This document defines contract and validation posture only. It does not implement production projection generation, consent policy evaluation, delegation runtime, model scoring, staffing decisions, or graph traversal.
