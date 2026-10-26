# Development workflow

This repo uses trunk-based development with short-lived feature branches:

1. **`main` is the trunk.** It should always be green (CI passing) and
   deployable. Nobody commits to it directly.
2. **Every change gets its own branch**, cut from the latest `main`:
   ```bash
   git checkout main && git pull
   git checkout -b feature/<short-description>   # or fix/<short-description>
   ```
3. **Commit your work on that branch** and push it:
   ```bash
   git push -u origin feature/<short-description>
   ```
4. **Open a pull request into `main`.** This triggers the `Airflow CI`
   GitHub Actions workflow (`.github/workflows/airflow-ci.yml`), which
   installs Airflow and actually runs the DAGs - a red PR means something
   is genuinely broken, not just "forgot to test."
5. **Merge once CI is green** (and once `main` is configured to require
   it - see below). Prefer "Squash and merge" to keep `main`'s history to
   one commit per feature. Delete the branch after merging.

## One-time repository setup (do this in GitHub's web UI)

These aren't things a bot/API token can safely flip on your behalf, so
they need a manual click once:

- **Settings -> General -> Default branch**: switch it to `main`
  (new repos default to whichever branch is pushed first, which isn't
  always `main`).
- **Settings -> Branches -> Add branch protection rule** for `main`:
  - "Require a pull request before merging" - blocks direct pushes.
  - "Require status checks to pass before merging", and select the
    `validate-and-run` check from the `Airflow CI` workflow - blocks
    merging a PR whose DAGs don't actually run.

With both set, the only way code reaches `main` is: branch -> PR -> CI
green -> merge.

## Branch naming

- `feature/<name>` - new functionality (e.g. `feature/add-sensor-dag`)
- `fix/<name>` - bug fixes
- `chore/<name>` - tooling/CI/docs changes that aren't a feature or a fix
