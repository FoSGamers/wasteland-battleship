# Contributing & Development Rules (Cursor)

## Universal Cursor Project Rules

### 1. Code Changes & Refactoring
- **Always provide an "Apply All" button** with the corrected code for any file changes. This ensures changes are applied exactly and reliably.
- **Never break existing functionality** when implementing new features or fixes.
- **Refactor methodically and intelligently:**
  - Do not lose any existing features or connections.
  - Ensure all parts of the codebase remain fully connected and implemented correctly.
  - If a refactor is complex, do it in clear, logical steps, verifying each before moving to the next.

### 2. GitHub Sync
- **Always commit and push to GitHub immediately after any change** (feature, fix, refactor, or test).
  - This provides a full, revertible history and enables safe, incremental development.

### 3. Testing
- **Always create or update tests immediately** for any new feature, fix, or upgrade.
  - Tests should be created as soon as a feature is implemented, not deferred.
  - If a feature is added, a corresponding test must be added in the same commit.
  - If a bug is fixed, a regression test must be added to prevent recurrence.

### 4. General Best Practices
- **Never make changes that could break the app** or leave it in an inconsistent state.
- **Communicate clearly** about what is being changed, why, and how it is being tested.
- **If a change is large or risky, break it into smaller, verifiable steps.**

---

**These rules apply to all projects developed in Cursor.** 