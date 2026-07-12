"""Shared deprecation warnings for public SDK surfaces.

Call :func:`warn_deprecated` at the start of any public method that still
invokes an OpenAPI operation marked ``deprecated: true``. Release N keeps the
method working and warns; release N+1 removes the operation and the method.
"""

from __future__ import annotations

import warnings


def warn_deprecated(*, old: str, new: str, stacklevel: int = 2) -> None:
    """Emit a :class:`DeprecationWarning` naming the replacement surface.

    Parameters
    ----------
    old:
        The deprecated public name (method, attribute, or path segment).
    new:
        The replacement callers should use.
    stacklevel:
        Passed to :func:`warnings.warn` (default 2 points at the caller).
    """
    warnings.warn(
        f"{old} is deprecated and will be removed in the next release; use {new} instead.",
        DeprecationWarning,
        stacklevel=stacklevel,
    )
