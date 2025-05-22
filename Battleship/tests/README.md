# Battleship Project Testing

## How to Run Tests

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Run all tests:
   ```
   pytest
   ```

## How to Add New Tests
- Add new test files as `test_*.py` in this directory.
- Use `pytest` style: functions named `test_*`.
- Import the relevant modules/classes from your project.
- Add tests for every new feature, bugfix, or refactor.

## Testing Philosophy
- **Every feature, fix, or upgrade must have a test.**
- **Regression tests** must be added for every bug fixed.
- **Tests should be committed in the same commit as the feature/fix.**
- **Never break existing tests.**

---

For more, see the main CONTRIBUTING.md. 