# tiny-bidirectional-map

A dictionary subclass that keeps a parallel reverse index, giving you O(1)
value-to-key lookups alongside normal key-to-value access.

```python
from tiny_bidirectional_map import BidirectionalMap

b = BidirectionalMap()
b["apple"] = 1
b["banana"] = 2

assert b["apple"] == 1          # forward lookup
assert b.inverse[1] == "apple"  # reverse lookup
assert b.key_for(2) == "banana" # convenience accessor
```

`BiMap` is provided as a shorter alias for the same class.

## Why

Whenever you maintain a mapping and also need to answer "which key produced
this value?", a second dict is usually the answer. Doing that by hand is
mechanical and error-prone: forget to delete from the reverse map once and
lookups silently return stale keys. This class owns both indexes and keeps
them consistent across `__setitem__`, `__delitem__`, `pop`, `popitem`,
`clear`, `setdefault`, and `update`.

The trade-off is that values must be **unique**. A reverse lookup is only
unambiguous when no two keys share a value, so inserting a duplicate value
raises `ValueError` rather than silently overwriting the inverse entry. If
your data has duplicate values, this is the wrong data structure.

## Edge cases

- Re-assigning an existing key to a *new* value cleans up the old value's slot
  in the inverse index.
- Re-assigning the same key to the same value is a no-op and does not raise.
- `inverse` returns the live internal dict. Treat it as read-only; mutating it
  directly will desynchronise the two indexes.
- `None` is a legal value, so `b.inverse[None]` works when a key maps to it.

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

