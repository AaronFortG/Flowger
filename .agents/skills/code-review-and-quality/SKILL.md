
---

## `.agents/skills/code-review-and-quality/SKILL.md`

```md
---
name: code-review-and-quality
description: Reviews Python code for correctness, maintainability, structure, formatting, and quality gates. Use when reviewing code changes, validating generated code, or preparing a change for commit.
---

# Code Review and Quality

This skill helps the agent review and improve code quality before considering a change complete.

## When to use this skill

Use this skill when:
- reviewing a completed implementation step
- checking maintainability of new code
- ensuring structure and separation of concerns
- preparing code for commit or PR

## Review checklist

### Correctness
- Does the code do what the step intended?
- Are edge cases handled reasonably for the current scope?
- Are assumptions explicit?

### Structure
- Are responsibilities clearly separated?
- Is the code placed in the right layer?
- Are files small and navigable?
- Is each class or major component in its own file when appropriate?

### Maintainability
- Can another developer find the logic quickly?
- Is the naming clear?
- Is implementation replaceable where it should be?

### Quality gates
- Is the code formatted and lint-friendly?
- Are type hints present where appropriate?
- Are there obvious typing or lint issues?
- Are verification steps clear?

## Quality rules

- Keep code small and cohesive.
- Prefer explicit naming.
- Avoid hidden side effects.
- Avoid large functions and large files.
- Avoid mixing orchestration, persistence, and domain logic.

## Required standards

Generated or modified Python code should be consistent with:
- formatting discipline
- linting discipline
- basic type-checking discipline

Prefer alignment with:
- `ruff`
- `mypy`
- `pytest`

## Feedback style

When reviewing:
- explain why something should change
- suggest the smallest reasonable improvement
- avoid proposing broad refactors unless clearly justified

## Expected outcome

Changes should be:
- easy to read
- easy to review
- easy to verify
- easy to maintain

## Readability and comments

- Prefer self-explanatory code over explanatory comments.
- Use clear names for functions, classes, variables, fields, and arguments.
- Function signatures should make intent obvious whenever possible.
- Keep comments to a minimum.
- Do not add comments that merely restate what the code already makes clear.

### When comments are acceptable
- A short header comment is acceptable when a function has non-obvious behavior, important constraints, side effects, or business context that is not clear from the code alone.
- Comments should explain why, assumptions, invariants, or edge-case intent — not narrate line-by-line behavior.

### Comment style
- Prefer no comment over a low-value comment.
- Prefer a short, focused header comment over many inline comments.
- Avoid noisy comments, tutorial-style comments, and redundant docstrings.