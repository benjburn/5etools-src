# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## 🚨 CRITICAL: Session Completion Protocol

**Work is NOT complete until git push succeeds.**

1. **File issues** for remaining work
2. **Run quality gates** (tests, linters, builds)
3. **Update issue status** (close finished work)
4. **PUSH TO REMOTE** - MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune branches
6. **Verify** - All changes committed AND pushed

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git (auto-synced by daemon)
```

## Creating Issues

**ALWAYS use templates** for new issues to preserve context between sessions:

```bash
# Copy template
cp docs/beads-templates/issue-template.md my-issue.md

# Edit and create
bd create --title="Issue Title" --body-file=my-issue.md --type=task --priority=2
```

**Required context fields:**
- **Предыстория**: Why is this issue important?
- **Связанные файлы**: Which files are affected?
- **Связанные сессии**: Links to work sessions (date, description)

See `docs/beads-templates/README.md` for detailed instructions and examples.

## Data Reorganization Workflow

**CRITICAL**: After changing scripts in `scripts/reorganize/`:

```bash
# Delete and reorganize
rm -rf data_rework/
python scripts/reorganize/reorganize_data.py

# Or use --clean flag (recommended)
python scripts/reorganize/reorganize_data.py --clean

# Validate results
python scripts/validation/run-all.py
```

**Why?** Scripts work incrementally and skip existing files. Changes won't apply to existing files.

See `CLAUDE.md` (lines 111-144) and `scripts/reorganize/README.md` for details.
