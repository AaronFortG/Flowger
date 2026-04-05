---
trigger: always_on
---

# Python Structure

Follow a simple layered architecture:

- domain
- application
- ports
- infrastructure
- entrypoints

## Structural rules
- Keep domain independent from infrastructure.
- Keep CLI as an entrypoint only; do not put business logic in the CLI.
- Separate interfaces from implementations.
- Each class should live in its own file when it has meaningful responsibility or non-trivial behavior.
- Each major component should have a clearly scoped file.
- Prefer smaller files with clear names over large mixed modules.

## Dependency rules
- Application should not depend directly on concrete infrastructure implementations.
- Infrastructure should implement contracts defined in higher layers where replacement is likely.