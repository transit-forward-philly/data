# Security

This repo holds public data and small scripts. We still want it to be safe to use and to contribute to.

## How changes get in

- Nobody pushes straight to `main`. Every change goes through a pull request that a person reviews and approves.
- Some contributors use AI tools, including Claude, which is connected to this repo through the Claude GitHub App. Its access is limited to this repository, and commits it helps write are labeled `Co-Authored-By: Claude` so anyone can see and audit them. AI-assisted changes go through the same review as everything else.
- Reviewers check sourcing, correctness, and anything that runs code: scripts, workflows, and dependencies.

## What never goes in this repo

- Passwords, API keys, tokens, or other secrets. Use GitHub Actions secrets if a script needs one.
- Personal information: names, emails, phone numbers, or home addresses of private individuals.
- Anything internal or not yet approved for public release.

## Automated checks

- GitHub secret scanning and push protection, to catch credentials before they land.
- Dependabot alerts for vulnerable dependencies in `pipelines/`.
- GitHub Actions workflows run with read-only permissions unless a job needs more, and that need is noted in the workflow.

## Reporting a problem

If you find a security issue (a leaked secret, a script that does something unexpected, personal data that shouldn't be here), please don't open a public issue. Use GitHub's **Report a vulnerability** button on the Security tab, or contact a maintainer directly. We'll respond as soon as we can.
