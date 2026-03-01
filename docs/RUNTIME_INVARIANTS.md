# Runtime Invariants (v0.1)

These invariants are executable law and must be enforced by tests, guards, and runtime checks.

1. No manifest may activate unless it passes schema validation.
2. No agent may execute beyond its declared capability set.
3. No child context may exceed its parent-granted capabilities.
4. No spawn may exceed the effective maximum depth cap.
5. No plugin may mutate core modules, schemas, or kernel configuration.
6. No undeclared capability may be invoked at runtime.
7. No fallback chain may recurse indefinitely; all chains must be finite and cycle-safe.
8. No promotion may occur without an operator-approved, human-readable diff.
9. No release may proceed without a rollback artifact for the previous stable state.
10. No core change may merge without an Architecture Decision Record (ADR) reference.
11. No observability event may log raw secrets or unredacted sensitive data.
12. No autonomous evolution may bypass the evolution pipeline (proposal -> validation -> replay -> approval -> promotion).
