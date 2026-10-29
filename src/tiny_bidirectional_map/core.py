"""Core implementation of the bidirectional map.

Design decisions
-----------------
1. **Unique values only.** A reverse index can map a value back to at most one
   key, so attempting to insert a duplicate value raises ``ValueError``.
   Allowing one-to-many would silently break the O(1) inverse contract, so we
   reject it eagerly rather than returning stale data later.
2. **Mutable, dict-like surface.** The class subclasses ``dict`` so it is
   interchangeable with a plain mapping for read operations while maintaining
   the parallel ``_inverse`` index.
3. **Equality ignores the inverse.** Two ``BidirectionalMap`` instances are
   equal when their forward contents match, mirroring how ``dict`` equality
   works. Comparing the inverse too would surprise callers who build maps in
   different insertion orders.
"""

from __future__ import annotations

from typing import Any, Iterator


class BidirectionalMap(dict):
    """A dictionary with an O(1) reverse lookup.

    ``b[key]`` returns the value, as with any dict.
    ``b.inverse[value]`` returns the unique key that maps to that value.

    Raises
    ------
    ValueError
        On any assignment that would make two keys share the same value.
    """

    __slots__ = ("_inverse",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # We cannot use ``super().__init__(...)`` directly because the default
        # dict initializer calls ``__setitem__`` *before* ``_inverse`` exists.
        # Initialise both stores empty, then bulk-populate through our own
        # ``__setitem__`` so the reverse index is built consistently.
        super().__init__()
        object.__setattr__(self, "_inverse", {})
        if args or kwargs:
            self.update(*args, **kwargs)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _check_unique(self, key: Any, value: Any) -> None:
        existing_key = self._inverse.get(value)
        if existing_key is not None and existing_key != key:
            raise ValueError(
                f"value {value!r} is already mapped to key {existing_key!r}"
            )

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------
    def __setitem__(self, key: Any, value: Any) -> None:
        self._check_unique(key, value)
        # If we are re-assigning an existing key to a *new* value, the stale
        # entry in the inverse must be removed first so that value slots are
        # not leaked.
        if dict.__contains__(self, key):
            old_value = dict.__getitem__(self, key)
            if old_value != value:
                self._inverse.pop(old_value, None)
        super().__setitem__(key, value)
        self._inverse[value] = key

    def __delitem__(self, key: Any) -> None:
        value = dict.__getitem__(self, key)
        super().__delitem__(key)
        self._inverse.pop(value, None)

    def clear(self) -> None:
        super().clear()
        self._inverse.clear()

    def pop(self, key: Any, *default: Any) -> Any:
        # ``dict.pop`` accepts at most one default. We route through
        # ``__delitem__`` only when the key exists so the inverse stays in sync.
        if dict.__contains__(self, key):
            value = dict.__getitem__(self, key)
            super().__delitem__(key)
            self._inverse.pop(value, None)
            return value
        if default:
            return default[0]
        raise KeyError(key)

    def popitem(self) -> Any:
        key, value = super().popitem()
        self._inverse.pop(value, None)
        return key, value

    def setdefault(self, key: Any, default: Any = None) -> Any:
        if dict.__contains__(self, key):
            return dict.__getitem__(self, key)
        self[key] = default
        return default

    def update(self, *args: Any, **kwargs: Any) -> None:
        # Route everything through ``__setitem__`` so the uniqueness guard and
        # inverse bookkeeping apply uniformly.
        if len(args) > 1:
            raise TypeError(
                f"update expected at most 1 positional argument, got {len(args)}"
            )
        if args:
            other = args[0]
            if hasattr(other, "items"):
                for k, v in other.items():
                    self[k] = v
            else:
                for k, v in other:
                    self[k] = v
        for k, v in kwargs.items():
            self[k] = v

    # ------------------------------------------------------------------
    # Inverse access
    # ------------------------------------------------------------------
    @property
    def inverse(self) -> dict:
        """Return the live reverse mapping (value -> key).

        The returned object is the internal inverse dict, shared with this
        ``BidirectionalMap``. Mutating it directly is not supported and will
        desynchronise the two indexes; treat it as read-only.
        """
        return self._inverse

    def key_for(self, value: Any) -> Any:
        """Return the key that maps to ``value``.

        Raises ``KeyError`` if no key maps to ``value``.
        """
        if value not in self._inverse:
            raise KeyError(value)
        return self._inverse[value]

    # ------------------------------------------------------------------
    # Copying
    # ------------------------------------------------------------------
    def copy(self) -> "BidirectionalMap":
        new = BidirectionalMap()
        for k, v in self.items():
            super(BidirectionalMap, new).__setitem__(k, v)
            new._inverse[v] = k
        return new

    def __copy__(self) -> "BidirectionalMap":
        return self.copy()


# Short alias for ergonomic call sites.
BiMap = BidirectionalMap
