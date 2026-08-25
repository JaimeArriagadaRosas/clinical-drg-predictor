# Security Policy

## Reporting a vulnerability

Please do not disclose suspected vulnerabilities in public issues.

Use GitHub's private vulnerability reporting for this repository when available. If that option is unavailable, contact the maintainer privately through the contact information published on the repository owner's GitHub profile.

Include enough information to reproduce and assess the issue without exposing real patient data, credentials, secrets, or other sensitive information.

## Scope

Security reports are especially relevant when they involve:

- authentication or authorization bypass;
- secret or credential exposure;
- unsafe handling of uploaded or clinical data;
- dependency or supply-chain compromise;
- remote code execution or injection;
- unintended exposure of model or API internals.

## Clinical and data safety

This repository is an academic and engineering project. It must not be used as a substitute for clinical diagnosis or professional medical judgment.

Never commit real patient-identifiable data, production credentials, API keys, trained artifacts containing sensitive source data, or local `.env` files.

## Supported versions

Security fixes are applied to the current `main` branch. Historical snapshots and legacy compatibility paths are not maintained as independently supported releases.
