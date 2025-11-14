# ADR-004: Migrate from Poetry to uv Package Manager

**Status**: Accepted
**Date**: 2025-01-14
**Impact**: Medium

---

## Problem
Poetry dependency resolution and installation was slow (2-5 minutes), especially in CI/CD pipelines and Docker builds. This slowed down development iteration and deployment times.

---

## Decision
Migrate from Poetry to **uv** as the Python package manager for all dependency management, building, and installation tasks.

**Key Changes:**
- Replace `pyproject.toml` Poetry format with standard PEP 621 format
- Update Dockerfile to use `uv` instead of Poetry (10-100x faster installs)
- Update Makefile: `poetry run` → `uv run`, `poetry install` → `uv sync`
- Remove `poetry.lock`, use uv's dependency resolution
- Keep all tool configurations (ruff, mypy, black, etc.) unchanged

---

## Why
- **10-100x Faster**: uv is written in Rust, installs dependencies in seconds vs minutes
- **Standards-Based**: Uses PEP 621 (standard Python packaging format)
- **Simpler**: No separate Poetry installation needed
- **Better Caching**: Aggressive caching across projects
- **Modern**: Made by Astral (creators of ruff), actively developed
- **Drop-in Replacement**: Minimal code changes required
- **Smaller Docker Images**: Faster builds, smaller layer sizes

---

## Alternatives Rejected
- **Keep Poetry**: Too slow for large dependency trees (50+ packages)
- **Plain pip**: Lacks dependency resolution, lock file support
- **pip-tools**: Good but slower than uv, less feature-rich
- **pdm**: Similar to Poetry, not as fast as uv

---

## Impact

**Changed Components:**
- `pyproject.toml` - Converted from `[tool.poetry]` to `[project]` format
- `Dockerfile` - Uses `uv pip install` instead of `poetry install`
- `Makefile` - All `$(POETRY)` replaced with `$(UV)`
- `CLAUDE.md` - Updated documentation

**Deleted:**
- `poetry.lock` - uv handles lock file differently

**Breaking Changes:** No (commands remain the same via Makefile)

**Migration Required:** Yes
- Team members need to install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Run `uv sync` to install dependencies (replaces `poetry install`)
- CI/CD pipelines updated automatically via Dockerfile

---

## Notes
- **Install uv**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Dev install**: `uv sync --extra dev` or `make install-dev`
- **Run commands**: `uv run <command>` or `make <target>`
- **Speed improvement**: Dependencies install in ~10-30 seconds vs 2-5 minutes
- **Compatibility**: 100% compatible with existing code, only tooling changes
- **Documentation**: https://github.com/astral-sh/uv
- **Build time improvement**: Docker builds 5-10x faster
