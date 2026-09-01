# ADR 0003: PyPI Trusted Publishing workflow

## Status

Accepted for the v1.0 distribution path. PyPI-side publisher registration remains a maintainer action.

## Context

The project already has a published GitHub Release and a stable Python package. The remaining distribution risk is installation friction and long-lived credential handling. A PyPI API token would add a secret to the release path and would require rotation and exposure controls.

## Decision

Use PyPI Trusted Publishing through GitHub Actions OIDC:

- trigger only from a published, non-prerelease GitHub Release whose tag starts with `v`;
- check out the exact released tag and require the tag to equal `v<project.version>`;
- build and validate the wheel and source distribution in a restricted build job;
- pass only the validated distributions to a separate Ubuntu publish job;
- grant `id-token: write` only to that publish job and do not configure a username, password, or API token;
- bind the publish job to the GitHub environment `pypi`.

The workflow pins its third-party actions to immutable commit SHAs and validates the downloaded artifact again immediately before publication.

## Consequences

- The maintainer must register the exact GitHub owner, repository, workflow filename, and `pypi` environment on PyPI before a release can publish.
- A non-`v*` or prerelease GitHub Release cannot enter either job, and a version/tag mismatch fails before artifact upload.
- Trusted Publishing removes a long-lived PyPI credential from source control, workflow YAML, and GitHub repository secrets.
- The workflow prepares future formal releases; it does not recreate or mutate the existing `v1.0.0` tag or release.
