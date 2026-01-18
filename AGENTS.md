# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Creating Issues with Context

**CRITICAL:** Always include context when creating issues. This preserves information between sessions and prevents loss of important details after context compaction.

### Using the Template

```bash
# Copy and customize the template
cp docs/beads-templates/issue-template.md my-issue.md
# [Edit my-issue.md with your issue details]

# Create issue from template
bd create --title="Issue Title" --body-file=my-issue.md --type=task --priority=2
```

### Required Context Fields

Every issue MUST include:

1. **Предыстория (Background)**: Why is this issue important? What problem does it solve?
2. **Связанные файлы (Related Files)**: Which files are affected by changes?
3. **Связанные сессии (Related Sessions)**: Links to work sessions (date, description)

### Example Issue with Context

```markdown
# Fix token copying in data reorganization

## Type
bug

## Priority
P2

## Description
Reorganization script doesn't copy creature tokens from `img/bestiary/tokens/`

## Context

**Related Sessions:**
- 2026-01-18: Discovered during data reorganization testing

**Related Problems:**
- Data loss: 668MB of tokens not copied
- 472 source directories affected

**Related Files:**
- `scripts/reorganize/image_copier.py` - needs token copy function
- `img/bestiary/tokens/` - source tokens
- `data_rework/*/img/bestiary/tokens/` - target directories

**Background:**
During data reorganization testing, discovered creature tokens aren't copied. Tokens are used in the creature portrait tool and their loss is critical for users.
```

### Why Context Matters

The **Context** section helps:

1. **Recover history** after long periods
2. **Understand reasons** for issue creation (not just WHAT but WHY)
3. **Link work sessions** - avoid information loss during compaction
4. **Track dependencies** between files, problems, and solutions

This is **critical** for long-running projects (5etools-src).

See `docs/beads-templates/README.md` for detailed instructions and examples.

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
