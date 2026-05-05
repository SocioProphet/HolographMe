# Security Policy

HolographMe handles concepts that can become sensitive even before implementation: identity, capability, consent, reputation, agent delegation, and work history.

## Reporting

For now, report security or privacy concerns to:

security@socioprophet.ai

Do not include live personal data, credentials, secrets, or private keys in public issues.

## Sensitive areas

Treat the following as security- and privacy-relevant:

- consent policy bypass;
- unauthorized projection of twin fields;
- agent delegation escalation;
- sensitive field leakage;
- replay or transition-receipt tampering;
- false credential or evidence injection;
- reputation poisoning;
- irreversible action without approval;
- retention or revocation failure.

## Default posture

The default posture is deny-by-default for sensitive fields, approve-by-default only for low-risk recommendations, and receipt-by-default for control-grade changes.
