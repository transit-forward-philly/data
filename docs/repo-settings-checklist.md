# Repo Settings Checklist

For organization owners. Work through this once, then review access every few months.

## Access

| Role | Who | How many |
|---|---|---|
| Owner | Committee lead, TFP director, one backup | 2–3 |
| Write (maintainers) | Regulars who review and merge | 3–5 |
| Triage | Active volunteers who label and assign issues | Any |
| Everyone else | Contribute by pull request, issue, or the routes in CONTRIBUTING.md | Unlimited |

- [ ] Give write access after a few reviewed contributions, not on joining
- [ ] Review access every few months and remove inactive members
- [ ] Review installed GitHub Apps, including the Claude app, and keep each limited to the repos it needs

## Organization settings

- [ ] Require two-factor authentication for all members (Settings → Authentication security)
- [ ] Base member permission: Read (Settings → Member privileges)
- [ ] Only owners can create repositories
- [ ] Only owners can invite outside collaborators
- [ ] Third-party application access requires owner approval

## Repository settings

**Protect `main`** (Settings → Rules → Rulesets, or Branches → Add rule)
- [ ] Require a pull request before merging
- [ ] Require at least 1 approval
- [ ] Dismiss stale approvals when new commits are pushed
- [ ] Require review from Code Owners (uses `.github/CODEOWNERS`)
- [ ] Require conversation resolution before merging
- [ ] Block force pushes and branch deletion

**Security** (Settings → Code security)
- [ ] Secret scanning and push protection
- [ ] Dependabot alerts
- [ ] Private vulnerability reporting

**Actions** (Settings → Actions → General)
- [ ] Workflow permissions: read repository contents only
- [ ] Require approval to run workflows for first-time contributors

**General**
- [ ] Allow squash merging only
- [ ] Automatically delete head branches after merge
- [ ] Turn on Issues; add labels `good-first-task`, `data-request`, `new-dataset`, `correction`
