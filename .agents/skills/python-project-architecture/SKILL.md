---
name: python-project-architecture
description: Defines maintainable Python project architecture for layered applications with domain, application, ports, infrastructure, and entrypoints. Use when creating or restructuring project code, modules, or file organization.
---

# Python Project Architecture

This skill helps the agent design and maintain a clean, sustainable Python codebase for a layered application.

## When to use this skill

Use this skill when:
- creating the initial project structure
- adding new modules or classes
- deciding where code should live
- reviewing whether responsibilities are properly separated
- restructuring code for maintainability

## Architecture to use

Use a simple layered architecture:

- `domain`: business entities, value-like models, business rules
- `application`: use cases and orchestration of domain behavior
- `ports`: interfaces/protocols/abstract contracts only where real substitution is likely
- `infrastructure`: concrete implementations such as database access, HTTP clients, CSV export, config, logging
- `entrypoints`: CLI or other external interfaces that invoke use cases

## Core rules

- Keep `domain` independent from infrastructure concerns.
- Keep `application` independent from concrete infrastructure implementations.
- `infrastructure` implements contracts defined higher up.
- `entrypoints` should orchestrate only; they must not contain business logic.

## File organization

Prefer many small, well-named files over fewer large files.

### File structure guidance
- Each class should live in its own file when it has meaningful responsibility or non-trivial behavior.
- Each major module should have a clearly scoped file.
- Avoid “misc”, “utils”, or dumping unrelated code together.
- Separate interfaces from implementations.

### Example layout

```text
src/flowger/
  domain/
    account.py
    transaction.py
    sync_state.py

  application/
    sync_account_transactions.py
    export_account_transactions.py

  ports/
    banking_provider.py
    transaction_repository.py
    transaction_exporter.py

  infrastructure/
    banking/
      enable_banking_provider.py
      stub_banking_provider.py
    persistence/
      sqlite_transaction_repository.py
    export/
      csv_transaction_exporter.py
    config/
      settings.py
    logging/
      logger.py

  entrypoints/
    cli.py

