# Security Policy

## Supported versions

The repository is under active development. Security fixes are applied to the current branch.

## Reporting a vulnerability

Report suspected vulnerabilities privately to the repository owner. Do not open a public issue
with secrets, exploit details, or live Discord/PostgreSQL/Redis configuration.

## Secret handling

- Never commit `.env`, Discord tokens, database passwords, Redis credentials, or API keys.
- Use `.env.example` as the only environment template.
- Discord replies and application logs must not include tokens or internal stack traces.
- Rotate any credential immediately if it may have been exposed.
