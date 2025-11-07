# Pre-commit Hooks Setup Guide

## 🎯 Overview

This project uses comprehensive pre-commit hooks to ensure code quality, security, and consistency before commits are made. The hooks automatically check and fix various issues, preventing problematic code from entering the repository.

---

## ✨ Features Included

### 🎨 Code Formatting
- **Black** - Python code formatter (PEP 8 compliant)
- **isort** - Import statement organizer
- **Trailing whitespace** - Automatic removal
- **Line endings** - Consistent LF endings

### 🔍 Code Quality
- **Flake8** - Python linting with plugins
  - flake8-bugbear (bug detection)
  - flake8-comprehensions (better comprehensions)
  - flake8-simplify (code simplification)
  - flake8-docstrings (docstring validation)
  - pep8-naming (naming conventions)
- **MyPy** - Static type checking
- **Pylint** - Advanced linting
- **Radon** - Complexity analysis

### 🔐 Security
- **Bandit** - Security vulnerability scanner
- **detect-secrets** - Secret detection
- **Safety** - Dependency vulnerability checker

### 📝 Documentation
- **Interrogate** - Docstring coverage checker
- **Markdown linting** - Ensure consistent markdown

### 🐳 Infrastructure
- **Dockerfile linting** - Hadolint checker
- **YAML validation** - Syntax checking
- **JSON formatting** - Auto-formatting

### 📦 Git Hygiene
- **Commit message validation** - Conventional commits
- **Merge conflict detection** - Prevent broken merges
- **Large file prevention** - Block files > 1MB
- **Protected branch prevention** - No direct commits to main

### 🧪 Custom Checks
- Print statement detection (production code)
- Bare except clause detection
- TODO/FIXME detection
- Test file naming validation

---

## 🚀 Quick Start

### 1. Install Pre-commit

```bash
# Install pre-commit tool
poetry install  # Installs all dev dependencies including pre-commit

# OR install separately
pip install pre-commit
```

### 2. Install Git Hooks

```bash
# Install the pre-commit hooks
pre-commit install

# Install commit message hook
pre-commit install --hook-type commit-msg

# Verify installation
pre-commit --version
```

### 3. Test the Installation

```bash
# Run on all files (first time)
pre-commit run --all-files

# This will:
# - Download and install all hook dependencies
# - Run all checks on your codebase
# - Auto-fix issues where possible
```

---

## 📋 Usage

### Automatic Execution

Once installed, hooks run automatically on:
- `git commit` - Runs on staged files
- `git commit -m "message"` - Validates commit message

### Manual Execution

```bash
# Run on all files
pre-commit run --all-files

# Run on specific files
pre-commit run --files src/app/main.py

# Run specific hook
pre-commit run black --all-files
pre-commit run flake8 --all-files
pre-commit run bandit --all-files

# Skip hooks (use sparingly!)
git commit --no-verify -m "Skip hooks"
```

---

## 🎨 Auto-fixing Issues

Many hooks automatically fix issues:

### Auto-fixed Issues
✅ **Black** - Reformats Python code
✅ **isort** - Reorganizes imports
✅ **Trailing whitespace** - Removes trailing spaces
✅ **Line endings** - Converts to LF
✅ **JSON formatting** - Pretty-prints JSON
✅ **Markdown** - Fixes common markdown issues

### Manual Fixes Required
❌ **Flake8** - Must fix linting errors manually
❌ **MyPy** - Must add/fix type hints
❌ **Bandit** - Must address security issues
❌ **Tests** - Must fix failing tests

### Workflow
```bash
# 1. Stage your changes
git add .

# 2. Try to commit
git commit -m "feat: Add new feature"

# 3. Hooks run automatically:
#    - Some auto-fix issues
#    - Some report errors

# 4. If auto-fixed, re-stage and commit
git add .
git commit -m "feat: Add new feature"

# 5. If errors remain, fix manually, then commit
```

---

## 🔧 Configuration

### Hook Levels

Hooks are organized by severity:

**Level 1: Blocking (must pass)**
- Python syntax errors (check-ast)
- Security issues (bandit)
- Merge conflicts (check-merge-conflict)
- Large files (check-added-large-files)

**Level 2: Formatting (auto-fix)**
- Black, isort
- Trailing whitespace
- Line endings

**Level 3: Quality (must fix)**
- Flake8, MyPy
- Docstring coverage
- Complexity checks

### Customization

Edit `.pre-commit-config.yaml` to customize:

```yaml
# Skip specific hooks
- id: black
  stages: [manual]  # Only run manually

# Adjust arguments
- id: flake8
  args:
    - --max-line-length=120  # Increase line length

# Exclude files
- id: mypy
  exclude: ^tests/  # Skip tests
```

---

## 📊 Hook Descriptions

### 🎨 Black (Code Formatter)
```bash
# What it does
- Formats Python code to PEP 8 style
- Line length: 100 characters
- Auto-fixes: Yes

# Manual run
poetry run black src/ tests/

# Config: pyproject.toml [tool.black]
```

### 📦 isort (Import Organizer)
```bash
# What it does
- Sorts and organizes imports
- Compatible with Black
- Auto-fixes: Yes

# Manual run
poetry run isort src/ tests/

# Config: pyproject.toml [tool.isort]
```

### 🔍 Flake8 (Linter)
```bash
# What it does
- Checks code style and quality
- Detects common bugs
- Auto-fixes: No

# Manual run
poetry run flake8 src/ tests/

# Config: pyproject.toml [tool.flake8]
```

### 🔐 Bandit (Security Scanner)
```bash
# What it does
- Scans for security vulnerabilities
- Checks for dangerous patterns
- Auto-fixes: No

# Manual run
poetry run bandit -r src/

# Config: pyproject.toml [tool.bandit]
```

### 🔎 MyPy (Type Checker)
```bash
# What it does
- Validates type hints
- Catches type-related bugs
- Auto-fixes: No

# Manual run
poetry run mypy src/

# Config: pyproject.toml [tool.mypy]
```

### 🕵️ detect-secrets
```bash
# What it does
- Detects hardcoded secrets
- Prevents credential leaks
- Auto-fixes: No

# Manual run
detect-secrets scan

# Update baseline
detect-secrets scan --baseline .secrets.baseline
```

### 📝 Interrogate (Docstring Coverage)
```bash
# What it does
- Checks docstring coverage
- Ensures documentation
- Target: 80% coverage
- Auto-fixes: No

# Manual run
poetry run interrogate src/

# Config: pyproject.toml [tool.interrogate]
```

---

## 🚨 Common Issues & Solutions

### Issue 1: Hooks Taking Too Long

**Problem:** Pre-commit is slow on large repositories

**Solutions:**
```bash
# Option 1: Run only on changed files (default)
git commit

# Option 2: Skip slow hooks
SKIP=mypy,interrogate git commit

# Option 3: Disable specific hooks
# Edit .pre-commit-config.yaml and add:
stages: [manual]  # for hooks you want to run manually
```

### Issue 2: Black and Flake8 Conflict

**Problem:** Black formats code that Flake8 rejects

**Solution:**
```bash
# Already configured in .pre-commit-config.yaml
# Black runs first, Flake8 ignores Black-specific rules:
# - E203 (whitespace before ':')
# - W503 (line break before binary operator)
```

### Issue 3: Secret Detection False Positives

**Problem:** detect-secrets flags non-secrets

**Solution:**
```bash
# Update baseline to exclude false positives
detect-secrets scan --baseline .secrets.baseline

# Or add inline comment
password = "fake-for-testing"  # pragma: allowlist secret

# Or exclude file patterns in .pre-commit-config.yaml
```

### Issue 4: MyPy Errors on Third-Party Libraries

**Problem:** MyPy complains about untyped imports

**Solution:**
```python
# Add to pyproject.toml [tool.mypy]
ignore_missing_imports = true

# Or install type stubs
poetry add --group dev types-requests types-redis
```

### Issue 5: Hooks Fail After Dependency Update

**Problem:** Hooks use outdated dependencies

**Solution:**
```bash
# Update hook dependencies
pre-commit autoupdate

# Clean and reinstall
pre-commit clean
pre-commit install --install-hooks
```

---

## 📈 Best Practices

### 1. Run Hooks Before Push
```bash
# Run all checks before pushing
pre-commit run --all-files
git push
```

### 2. Commit Message Format
Use conventional commits:
```bash
# Format: <type>(<scope>): <subject>

git commit -m "feat(auth): Add OAuth2 authentication"
git commit -m "fix(api): Resolve rate limiting bug"
git commit -m "docs: Update API documentation"
git commit -m "test: Add integration tests for chat"
git commit -m "refactor(db): Optimize query performance"
git commit -m "chore(deps): Update dependencies"
```

**Types:** feat, fix, docs, style, refactor, test, chore, perf, ci

### 3. Handle Large Changes
```bash
# For large refactors, run hooks incrementally
git add src/app/main.py
git commit -m "refactor: Update main.py"

git add src/app/api/
git commit -m "refactor: Update API routes"
```

### 4. Keep Hooks Updated
```bash
# Update weekly/monthly
pre-commit autoupdate

# Review and commit changes
git add .pre-commit-config.yaml
git commit -m "chore: Update pre-commit hooks"
```

---

## 🔧 Advanced Configuration

### Custom Local Hooks

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: custom-check
      name: Custom validation
      entry: python scripts/custom_check.py
      language: system
      files: ^src/.*\.py$
```

### Skip Specific Files

```yaml
- id: mypy
  exclude: |
    (?x)^(
      src/app/migrations/.*|
      tests/fixtures/.*|
      scripts/.*
    )$
```

### Environment-Specific Hooks

```yaml
- id: pytest-check
  stages: [push]  # Only run on git push
```

---

## 📊 Monitoring Hook Performance

### View Hook Execution Time
```bash
# Run with verbose output
pre-commit run --all-files --verbose

# Shows:
# - Hook name
# - Files checked
# - Execution time
# - Pass/fail status
```

### Profile Slow Hooks
```bash
# Identify bottlenecks
time pre-commit run --all-files

# Disable slow hooks temporarily
SKIP=mypy,interrogate pre-commit run --all-files
```

---

## 🎓 Learning Resources

### Documentation
- [Pre-commit.com](https://pre-commit.com) - Official documentation
- [Black](https://black.readthedocs.io) - Code formatter
- [Flake8](https://flake8.pycqa.org) - Linting tool
- [Bandit](https://bandit.readthedocs.io) - Security scanner
- [MyPy](https://mypy.readthedocs.io) - Type checker

### Tools
- [pre-commit.ci](https://pre-commit.ci) - Automated pre-commit checks
- [Conventional Commits](https://www.conventionalcommits.org) - Commit format

---

## 🐛 Troubleshooting

### Reset Pre-commit
```bash
# Uninstall hooks
pre-commit uninstall
pre-commit uninstall --hook-type commit-msg

# Clean cache
pre-commit clean

# Reinstall
pre-commit install
pre-commit install --hook-type commit-msg
```

### Force Hook Update
```bash
# Update all hooks to latest
pre-commit autoupdate

# Run with latest versions
pre-commit run --all-files
```

### Debug Hook Execution
```bash
# Run with debug output
pre-commit run --verbose --all-files

# Check hook configuration
pre-commit run --show-diff-on-failure
```

---

## 📝 Summary

### ✅ Installed
- ✅ 40+ pre-commit hooks
- ✅ Auto-formatting (Black, isort)
- ✅ Linting (Flake8, Pylint)
- ✅ Security scanning (Bandit, detect-secrets)
- ✅ Type checking (MyPy)
- ✅ Documentation checks (Interrogate)
- ✅ Commit message validation (Commitizen)

### 🎯 Benefits
- **Consistent code style** across team
- **Catch bugs early** before review
- **Security by default** with secret detection
- **Automated fixes** for common issues
- **Better documentation** with coverage checks
- **Professional commits** with conventional format

### 🚀 Next Steps
1. Run `pre-commit install` to enable hooks
2. Run `pre-commit run --all-files` for initial check
3. Commit changes and watch hooks in action!
4. Review any failed checks and fix them

---

**Last Updated:** 2025-11-07
**Status:** ✅ Ready for Use
