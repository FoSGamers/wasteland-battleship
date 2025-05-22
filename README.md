# Battleship (Cursor Edition)

## Overview
A modern, streamer-friendly Battleship game with a robust PyQt5 UI, GM control panel, and full test automation. Built for live streaming, fair play, and professional usability.

## Features
- Fully resizable, modern UI with draggable splitters
- GM vs Players mode with team selection
- Robust controls for shots, ship placement, randomization, stats, and logs
- All grids and controls are always visible and usable
- Comprehensive logic and UI test suite
- Universal development rules for all Cursor projects

## Install & Run
1. **Clone the repo:**
   ```
   git clone <your-repo-url>
   cd Battleship
   ```
2. **Install dependencies:**
   ```
   pip install -r Battleship/requirements.txt
   ```
3. **Run the app:**
   ```
   python Battleship/wasteland_battleship_secretset.py
   ```

## Testing
- **Run all tests:**
  ```
  pytest
  ```
- **Test Philosophy:**
  - Every feature, fix, or upgrade must have a test.
  - UI tests simulate real user actions and check visible results.
  - Regression tests for every bug fixed.
  - Never break existing tests.

## Contribution & Development Rules
- Always provide an Apply All button for code changes.
- Never break existing functionality.
- Refactor methodically and in steps if needed.
- Always commit and push to GitHub after every change.
- Always create or update tests immediately for every feature/fix.
- Never leave the app in an inconsistent state.
- Communicate clearly about changes and testing.
- See CONTRIBUTING.md for full rules (universal for all projects).

## How to Add Tests
- Add new test files as `test_*.py` in `Battleship/tests/`.
- Use `pytest` and `pytest-qt` for logic and UI tests.
- Simulate real user actions in UI tests (clicks, typing, toggling, etc.).
- Commit new/updated tests with the feature/fix.

## Changelog
- Modernized UI and controls
- GM vs Players mode with team selection
- Robust, resizable layout
- Full test automation (logic + UI)
- Universal rules and documentation

---

**This README is a template for all Cursor projects. Copy and adapt for your next app!** 