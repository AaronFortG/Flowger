# Flowger Specification

## Goal
Build an open source application that syncs bank transactions from a provider such as Enable Banking, persists them locally, and exports them as CSV files that can be imported into Actual Budget.

## Product expectations
The application should:
- support multiple bank accounts within one application
- allow per-account export configuration
- ideally export one CSV per account
- run easily with Docker and docker compose
- remain maintainable and easy to understand
- serve as a learning project for architecture, CI/CD, security, deployment, testing, and operations

## Priorities
1. architectural clarity
2. pragmatic simplicity
3. safe iteration
4. ease of operation
5. real-world best practices
6. learning while building
7. avoiding overengineering

## Constraints and philosophy
Avoid:
- overly formal DDD
- unnecessary abstractions
- unnecessary complexity
- large unverified changes

Prefer:
- layered architecture
- ports and adapters only where useful
- small explicit domain
- SQLite first
- Python first
- CLI first
- short verifiable steps

## Target architecture
- domain
- application
- ports
- infrastructure
- entrypoints

## Initial functional requirements
- configure access to a banking provider
- discover available accounts
- store multiple accounts locally
- configure export per account
- sync transactions per account
- persist transactions in SQLite
- export transactions to CSV per account
- avoid duplicates reasonably
- prepare for Docker, CI/CD, and open source release

## Initial non-functional requirements
- clean repo structure
- reasonable typing
- tests
- environment-based configuration
- understandable logging
- reasonable idempotency
- GitHub Actions
- linting
- basic security checks
- Dockerfile
- docker compose
- useful documentation

## Preferred stack
- Python
- Typer
- Pydantic Settings
- SQLite
- SQLAlchemy or SQLModel
- httpx
- pytest
- ruff
- mypy

## Delivery style
The project should be built iteratively in small, verifiable steps, with practical explanations and minimal unnecessary complexity.

## Initial implementation mode
Start by:
1. proposing a minimal project structure
2. defining a realistic MVP
3. listing the first 5 implementation steps
4. recommending what to implement first
5. then implementing step 1 only

## Out of scope for now
- web UI
- multi-user support
- direct Actual API integration
- production cloud deployment