---
name: python-testing
description: Applies Python testing conventions with pytest, mirrored test structure, and meaningful verification. Use when adding or updating tests for Python modules, domain logic, or use cases.
---

# Python Testing

This skill helps the agent create meaningful tests for a maintainable Python project.

## When to use this skill

Use this skill when:
- adding a new module or class
- updating logic that affects behavior
- creating tests for domain rules or use cases
- reviewing testing gaps
- defining verification steps

## Test structure

Mirror the source structure whenever practical.

Example:

```text
flowger/domain/account.py
tests/domain/test_account.py

flowger/application/sync_account_transactions.py
tests/application/test_sync_account_transactions.py

flowger/ports/banking_provider.py
tests/ports/test_banking_provider.py
```

## Testing rules

- Prioritize tests for:
  - use cases
  - domain logic
  - critical paths
- Avoid trivial tests that add no value.
- Keep tests focused and independent.

## Verification

Every step must be runnable or verifiable.

- Provide exact commands to run tests locally.
- If tests are not yet implemented, provide clear manual verification steps.
- Manual steps must be simple and reproducible.

## When to create tests

- When adding a new feature
- When modifying existing logic
- When fixing a bug
- When implementing a use case
- When creating a new module

## Test quality

Tests should:
- be easy to read
- have clear names
- test one behavior at a time
- avoid complex setup
- not contain business logic themselves

## When tests are missing

If tests are missing:
- propose a test plan
- implement tests in a separate step
- explain what is being tested
- provide manual verification until tests are ready

## Example test structure

```python
# tests/domain/test_account.py
from flowger.domain.account import Account

def test_account_creation():
    account = Account(id="1", name="Test", currency="EUR")
    assert account.id == "1"
    assert account.name == "Test"

def test_account_balance_calculation():
    account = Account(id="1", name="Test", currency="EUR")
    # ... test balance logic
```

## Verification commands

Always provide:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/domain/test_account.py

# Run all tests with verbose output
pytest -v tests/
```

## When to ask about testing

Only ask when:
- the user explicitly requests a test strategy
- the project lacks any testing foundation
- a complex testing scenario requires clarification

Otherwise, follow standard Python testing conventions.