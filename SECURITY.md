# Security Policy

Status: ACTIVE | Tier: 1 | Created: 2026-04-13
Edit policy: Structural changes require Andrew approval

## Supported Versions

This repository is a documentation archive. No executable code is deployed. Security policy applies to:
- YAML recipe templates (potential injection risks if values are interpolated without sanitization)
- Agent system prompts (potential prompt injection surface)
- Future: Solidity contracts, Python quantum circuits, React Native mobile code (when scaffolded)

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

To report a vulnerability:
1. Email: [Andrew Pappas — contact via smtp.eth ENS or GitHub @fuzzywigg]
2. Include: description, affected files, reproduction steps, suggested fix
3. Expected response: acknowledgment within 48 hours

## Security Standards for This Ecosystem

When code is scaffolded into this repo, it must comply with:

| Domain | Standard |
|---|---|
| Cryptography | NIST post-quantum standards (ML-KEM/FIPS 203, ML-DSA/FIPS 204, SLH-DSA/FIPS 205) |
| Smart contracts | Slither audit pass (0 critical vulnerabilities) |
| Mobile | Apple/Google security guidelines compliance |
| Secrets | Never commit secrets; use `.env` files excluded by `.gitignore` |
| Keys | Never expose plaintext keys in RAM, logs, or code |

## Known Non-Issues

- AGENTS-v2.2.md references "CRYSTALS-Kyber" and "CRYSTALS-Dilithium" by their pre-finalization names. These map to ML-KEM (FIPS 203) and ML-DSA (FIPS 204) respectively. The underlying algorithms are correct; the naming will be updated in a future issue.
