# Code Generation Standards

## Code Formatting

- Always include mypy type hints for basic Python primitives (str, int, bool, list, dict, etc.)
- Include type hints for standard library and third-party library types where possible
- Exception: Skip type hints for 3ds Max Python classes and other external classes where types are unknown
- Use proper type annotations for function parameters, return values, and class attributes

## Unit Testing

- Only generate tests when explicitly requested
- Follow existing test patterns in the codebase
- Use descriptive test names that explain what is being tested
- Keep test setup minimal and focused
- Mock external dependencies appropriately
- Prefer pytest parameterized tests when applicable and not overly complicated with if-else logic
- Always include an `id` parameter in test parameterization for clear test identification
- Run `hatch run test` for basic unit tests
- Only run `hatch run all:test` for comprehensive testing after basic tests pass

## Code Quality (After Tests Pass)

- Run `hatch run fmt` to format code automatically
- Run `hatch run lint` to check and cleanup code quality issues
- Ensure all formatting and linting passes before considering work complete

## Code Review Checklist

Before completing code generation, verify:
- No syntax errors or type issues
- Follows existing code style and patterns
- Includes necessary imports
- Handles edge cases appropriately
- Does not introduce security vulnerabilities
