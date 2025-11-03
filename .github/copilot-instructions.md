# GitHub Copilot Instructions

These rules define how GitHub Copilot should behave when assisting in this repository.

---

## General Behavior

- Never use emojis in code, comments, or output.
- Avoid verbose summaries or long explanations. Perform the requested task directly and succinctly.
- Do not auto-generate documentation or Markdown files unless explicitly instructed.
- Always favor code quality, readability, and maintainability.
- Adhere to solid software engineering practices:
  - Apply separation of concerns and single-responsibility principles.
  - Keep files and functions short and modular.
  - Use private helper functions to reduce repetition and improve clarity.
  - Avoid large monolithic files; refactor into logical components as needed.
  - Use clear, consistent naming and follow project conventions.

---

## Design Philosophy

- Follow YAGNI (You Aren’t Gonna Need It):
  - Avoid speculative features or abstractions.
  - Keep implementations minimal and practical.
- Build only what’s needed for the MVP.
- Avoid unnecessary complexity, deep inheritance, or “clever” but hard-to-maintain solutions.
- Prefer composition over inheritance.
- Write self-documenting code instead of long comments.
- Include only relevant dependencies and imports.

---

## Collaboration and Output

- Assume the user values correctness and high-quality code over lengthy explanations.
- Respect existing project patterns and architecture.
- Avoid refactoring unrelated code unless specifically requested.
- Keep answers concise and focused.
- If multiple solutions exist, choose the most straightforward and maintainable one.
