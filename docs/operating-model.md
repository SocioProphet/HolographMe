# HolographMe Operating Model

## Operating thesis

HolographMe supports agentic consulting by turning intake, assessment, staffing, delivery, and learning into a governed loop. The person owns the twin. The consulting agency receives consent-scoped projections. Missions receive verified capability. Outcomes update the twin only through auditable transitions.

## Lifecycle

### 1. Intake

A person arrives through the website, referral, partner surface, or internal invitation. An intake agent explains the product boundary: the person is creating or updating a self-owned work twin, not surrendering a profile to a marketplace.

Outputs:

- subject record;
- consent policy;
- initial capability claims;
- intake transcript receipt;
- requested projection scopes.

### 2. Competency interview

An interview agent assesses capabilities against role archetypes, mission types, and practice-area requirements. The interview should separate claim, evidence, inference, and confidence.

Outputs:

- assessment event;
- capability claim updates;
- evidence references;
- confidence posture;
- correction/review path.

### 3. Twin formation

The system composes the person’s owned digital twin from declared claims, verified artifacts, credentials, preferences, constraints, and assessment outputs.

Outputs:

- valid HumanDigitalTwin object;
- state hash;
- transition receipt;
- export path.

### 4. Mission-fit projection

A staffing or workgraph system requests a scoped projection for a mission. The consent layer checks purpose, recipient, fields, expiration, and delegation rules before exposing data.

Outputs:

- projection document;
- policy decision log;
- mission-fit explanation;
- exposure receipt.

### 5. Team formation

The consulting agency forms teams by composing consented twin projections with agent capabilities, client constraints, governance requirements, and practice-area staffing rules.

Outputs:

- proposed team;
- role-capability mapping;
- gaps and training recommendations;
- approval path.

### 6. Delivery oversight

During delivery, agents and human leads observe work artifacts, milestones, quality signals, client feedback, and governance exceptions.

Outputs:

- mission event log;
- delivery evidence;
- quality signals;
- exception records;
- learning recommendations.

### 7. Outcome update

Mission outcomes may update reputation, capability confidence, portfolio evidence, and future recommendations. Updates require transition receipts and person-visible review.

Outputs:

- outcome summary;
- twin update proposal;
- approval or correction path;
- transition receipt;
- new state hash.

## Consulting-agency workflow

1. Define practice areas and role archetypes.
2. Publish mission templates and capability requirements.
3. Run intake interviews.
4. Generate governed twin projections.
5. Form teams from verified capability.
6. Supervise delivery through mission events.
7. Update twins from outcomes with evidence and review.
8. Improve role archetypes and assessments from observed performance.

## First practice-area archetypes

Initial archetypes should be implementation-oriented rather than purely advisory:

- Agentic Systems Consultant
- Governance and Policy Fabric Analyst
- Data / Ontology Engineer
- AI Product Operator
- Research Synthesist
- Platform Integration Engineer
- Client Delivery Lead
- Evaluation and Audit Operator

## Feedback loops

HolographMe should establish explicit cybernetic loops:

| Loop | Signal | Correction |
| --- | --- | --- |
| Capability loop | Assessment vs mission performance | Update confidence, training, and role-fit model. |
| Consent loop | Projection requests vs revocation/correction events | Tighten defaults and improve consent UX. |
| Staffing loop | Mission requirements vs team outcomes | Improve archetypes and matching weights. |
| Governance loop | Exceptions, disputes, audit failures | Update policy, approvals, and conformance tests. |
| Learning loop | Gaps found in delivery | Recommend training, apprenticeships, and next missions. |

## v0.1 acceptance test

A complete v0.1 demo should show:

1. a person creates a twin;
2. an interview adds capability evidence;
3. a consent policy limits sharing;
4. a mission asks for a projection;
5. the projection contains only authorized fields;
6. a transition receipt records what changed;
7. schema validation passes in CI.
