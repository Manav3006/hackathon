# Copilot Instructions

This repository is currently minimal. Keep suggestions conservative and aligned with what is actually present in the workspace.

## Working Style

- Prefer small, focused changes over broad scaffolding.
- Do not assume frameworks, services, or deployment targets that are not already in the repository.
- Ask for clarification before introducing major architecture, external services, or new dependencies.
- When adding code, update documentation if the change affects setup, usage, or behavior.

## Python Defaults

- Default to Python for implementation unless the repository clearly adopts a different language.
- Use clear function and variable names; avoid one-letter names except for conventional short-lived loop variables.
- Favor the standard library unless a third-party package materially simplifies the solution.
- Write code that is easy to run locally and does not require hidden environment assumptions.

## Testing And Validation

- If you add executable code, add or suggest a minimal verification path.
- Prefer `pytest` for tests if a test suite is introduced.
- Keep tests targeted to the behavior being changed.

## Safety And Scope

- Preserve unrelated user changes.
- Avoid destructive commands and irreversible file operations unless explicitly requested.
- Call out missing requirements, ambiguities, or tradeoffs instead of guessing.