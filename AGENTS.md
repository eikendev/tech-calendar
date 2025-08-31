## Coding Standards

### Code Clarity & Style

- Use **meaningful names** for variables, functions, and classes
- Keep functions and methods short and focused (one purpose / responsibility)
- Follow **PEP 8** guidelines for style
- Use **type hints** for better clarity and static analysis
- Add **docstrings** to modules, classes, functions, and methods to explain their purpose, arguments, and return values
- DO NOT ADD **inline code comments** when not explicitly asked for them

### Input Validation & Sanitization

- Validate and sanitize **all external inputs**, such as command-line arguments or data from external APIs

### Security Practices

- Never log passwords, API keys, or other sensitive data
- Use environment variables or a secure configuration management system for secrets; never commit them directly to the repository

### Tests & Coverage

- Write tests using **pytest**
- Test edge cases and error conditions, not just the "happy path"
- Keep tests deterministic, independent, and reasonably fast
- Aim for clear and expressive assertions

### Simplicity First

- Prioritize **simple, clear, and maintainable** code over overly complex or "clever" solutions
- Follow the Zen of Python (`import this`)

### Error Handling Strategy

- Raise specific custom exceptions
- Critical errors must halt the application
- Implement retries for transient item failures

## Behavior Guidelines

### General Guidance

- Prefer asking for clarification if context appears missing or ambiguous
- Identify any **assumptions** you're making before proceeding with changes or recommendations
- Never make adjustments to dependencies directly; leverage the package manager!

### Task Execution

- Before writing code:
  1. Analyze **all relevant** code files
  2. Extract existing patterns and conventions
  3. Suggest an implementation plan in Markdown
  4. Only then, proceed to write actual code

- Do not propose refactors unless:
  - There's clear duplication
  - Complexity thresholds are exceeded (e.g., long methods, nested logic)
  - The suggestion improves maintainability without breaking conventions

### Style & Completeness

- Always return **complete** function/class/module implementations unless otherwise requested
- Avoid truncation and include **all** required dependencies or imports in generated code

### Testing Suggestions

- When modifying business logic, suggest matching unit tests
- For endpoint changes, recommend or generate integration test updates
- Mention potential test fallout when editing shared or central components
