---
trigger: always_on
---

# Quality Gates

## Code quality
- Use clear naming and type hints.
- Keep functions and files small and cohesive.
- Avoid speculative abstractions and hidden side effects.
- Ensure generated code is compatible with formatting, linting, and basic type-checking expectations.

## Testing
- Add meaningful tests when behavior changes or new logic is introduced.
- Mirror source structure in tests whenever practical.
- Prefer behavior-focused tests for domain and application logic.
- If tests are not added yet, always provide reproducible manual verification steps.

## Completion standard
A step is not complete unless:
- the change is understandable,
- the verification path is clear,
- structure remains maintainable.

## Readability and comments
- Prefer self-explanatory code over comments.
- Use clear naming for functions, arguments, fields, and modules.
- Keep comments minimal and high-value.
- Add a short header comment only when behavior, constraints, or intent would otherwise be non-obvious.