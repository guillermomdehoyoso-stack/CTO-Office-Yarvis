"""F-012 technical observability primitives with no business authority.

Submodules are imported explicitly.  The HTTP error boundary depends on
redaction and must not initialize persistence or tracing as an import side
effect.
"""
