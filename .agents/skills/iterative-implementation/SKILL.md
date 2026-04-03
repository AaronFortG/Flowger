
---

## `.agents/skills/iterative-implementation/SKILL.md`

```md
---
name: iterative-implementation
description: Guides incremental implementation in small, verifiable steps. Use when planning or implementing features to keep the project maintainable and avoid overengineering.
---

# Iterative Implementation

This skill helps the agent implement work in small, safe, verifiable iterations.

## When to use this skill

Use this skill when:
- starting a new feature
- planning the next change
- implementing a new module
- deciding whether a task is too large
- reducing complexity during execution

## Working model

Never implement too much at once.

Every change should:
- have one clear primary goal
- modify the minimum number of files
- leave the project runnable or verifiable
- avoid mixing unrelated concerns

## Required response structure

For each iteration, provide:

1. Objective of this step
2. Technical decision
3. Files to modify
4. Proposed implementation
5. How to verify
6. Risks or accepted trade-offs
7. Next recommended step

## Decision rules

If a request is too large:
- reduce it to the smallest useful executable step
- state what is postponed
- explain why the reduced step is sufficient now

If a question is not truly blocking:
- choose the simplest reasonable option
- state the choice briefly
- continue

Only ask a question when it blocks implementation.

## Complexity control

If a design introduces too much complexity for the current stage:
- stop
- explain the risk
- propose a simpler alternative
- recommend postponing the complex path

## Implementation boundaries

Do not:
- add speculative abstractions
- implement future features “while here”
- restructure broad parts of the codebase without clear need
- mix feature work and broad refactors in one step

## Expected outcome

The project should evolve through:
- small diffs
- clear intent
- low risk
- strong learning value