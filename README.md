# NRP Platform Acceptance Testing

This repository contains acceptance tests for the NRP InvenioRDM platform.
The tests verify platform behavior independently of documentation claims and
are intentionally design-agnostic — they do not depend on any particular
application schema.

## Prerequisites

- **Docker** — [Get Docker](https://docs.docker.com/get-started/get-docker/)
  (Windows and Mac users: install Docker Desktop, which includes everything
  needed; Linux users: install Docker Engine and check that the Compose plugin
  is available with `docker compose version` — install `docker-compose-plugin`
  via your package manager if the command is not found; see
  [Install the Compose plugin](https://docs.docker.com/compose/install/linux/))

## Quick start

```bash
# Build the patched image (required for all tests except PLT-021-a)
docker build -f Dockerfile.patched -t testing-patched .

# Build the cold image (required only for PLT-021-a)
docker build -f Dockerfile.cold -t testing-cold .

# Start backing services (Postgres, Redis, OpenSearch, RabbitMQ, MinIO)
docker compose -f docker/docker-compose.yml up -d

# Run the test suite (test runner not yet implemented — see docs/acceptance_testing/)
```

## Key files

| Path | Purpose |
|------|---------|
| `Dockerfile.patched` | Image with minimal upstream patches applied; target for all tests except PLT-021-a |
| `Dockerfile.cold` | Pristine upstream NRP release, no patches; used only by PLT-021-a |
| `pyproject.patched.toml` | Dependency overrides for the patched build — see [The patch](#the-patch) below |
| `docs/specifications/platform_spec.csv` | Platform requirements (PLTREQ-001–024) |
| `docs/acceptance_testing/acceptance_tests.md` | Test designs and environment strategy |
| `docs/acceptance_testing/requirements.csv` | Test case table (machine-readable) |
| `scripts/render_table.py` | Renders `requirements.csv` as a Markdown table for injection into the test design doc |
| `test_record/metadata.yaml` | oarepo-model schema for the minimal test record — see [Test model](#test-model) below |
| `common/workflows/default.py` | Community workflow and permission policies |
| `fixtures/` | Vocabulary fixtures loaded at test setup (hierarchical vocab, languages, rights, etc.) |
| `docker/docker-compose.yml` | Backing services (database, search, cache, object storage) |

## Two-image strategy

Tests run against two pre-built Docker images.

**`patched`** is the normal test target. It applies a minimal set of patches
on top of the official NRP release to work around upstream bugs. All tests
except PLT-021-a run against this image.

**`cold`** is the pristine upstream release with no patches. It is used only
by PLT-021-a, which checks whether the upstream circular-import bug is still
present. A **FAIL** on PLT-021-a means the current patch set is still
required; a **PASS** means the upstream has fixed the issue and the
corresponding patch can be retired.

PLT-021-a should be re-run against each new NRP upstream release. The
long-term expectation is that the patch set converges to zero as upstream
issues are resolved.

## The patch

`pyproject.patched.toml` replaces `pyproject.toml` during the patched image
build. It overrides the `oarepo-model` package with the
[billyziege fork](https://github.com/billyziege/oarepo-model),
branch `zerbe_patching_to_get_dantec_working`.

The fork adds `LazyPIDFieldProxy` — a deferred resolver for pid-relation
`record_cls` references that fixes a circular import triggered by
self-referential pid-relations (a record type that references itself).
Upstream `oarepo-model` resolves `record_cls` eagerly during model
construction, before the module has finished loading.

One non-obvious uv behavior: `[tool.uv.sources]` overrides only apply to
packages listed as **direct** dependencies. If the target package arrives
only as a transitive dependency, uv silently installs from PyPI instead.
`pyproject.patched.toml` therefore lists `oarepo-model` explicitly in
`dependencies` even though no version constraint beyond what `oarepo-app`
already requires is needed.

## Test model

`test_record` is a minimal, application-neutral InvenioRDM record type
designed to exercise specific platform features:

- `vocab_item` — vocabulary reference to a 3-level hierarchical vocabulary
  (exercises PLT-024 hierarchical vocabulary tests)
- `parent_test_record` — self-referential pid-relation to `TestRecordRecord`
  (exercises PLT-019 record-linking tests and is the trigger for the
  circular-import bug that PLT-021-a documents)
- DataCite export wired via the CCMM production preset
  (exercises PLT-006 metadata export tests)
- `TitleRequiredOnPublish` pre-publish validator
  (exercises PLT-011 validation tests)

Do not simplify the model. Each field exists to support a specific test.

## Known blockers

- **PLT-021-a on `cold`** — expected to fail with a circular import error.
  This is the intended behavior; it documents the upstream bug.
- **DataCite sandbox** — tests that verify DOI assignment (PLT-002) require
  a DataCite sandbox account. These tests are currently blocked pending
  account setup.
