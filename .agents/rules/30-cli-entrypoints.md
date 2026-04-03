---
trigger: glob
globs: src/**/cli.py src/**/entrypoints/**
---

# CLI Entrypoints

CLI modules are entrypoints.

## Rules
- CLI code must only parse input, call use cases, and present output.
- CLI code must not contain business logic.
- CLI code must not directly implement persistence rules, domain rules, or provider logic.
- Keep CLI functions thin and explicit.

## Goal
The same use case should be reusable from a CLI, a future API, or a background job without rewriting business logic.