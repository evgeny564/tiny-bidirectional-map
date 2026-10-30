import copy
import unittest

from tiny_bidirectional_map import BiMap, BidirectionalMap


class TestBidirectionalMap(unittest.TestCase):
    def test_roundtrip_key_to_value_to_key(self) -> None:
        b = BidirectionalMap()
        b["apple"] = 1
        b["banana"] = 2
        self.assertEqual(b["apple"], 1)
        self.assertEqual(b.inverse[1], "apple")
        self.assertEqual(b["banana"], 2)
        self.assertEqual(b.inverse[2], "banana")

    def test_key_for_returns_key(self) -> None:
        b = BidirectionalMap({"x": 10, "y": 20})
        self.assertEqual(b.key_for(10), "x")
        self.assertEqual(b.key_for(20), "y")

    def test_key_for_raises_on_missing_value(self) -> None:
        b = BidirectionalMap({"x": 10})
        with self.assertRaises(KeyError):
            b.key_for(999)

    def test_duplicate_value_raises(self) -> None:
        b = BidirectionalMap()
        b["a"] = 1
        with self.assertRaises(ValueError):
            b["b"] = 1

    def test_reassign_same_key_same_value_is_noop(self) -> None:
        b = BidirectionalMap()
        b["a"] = 1
        b["a"] = 1  # idempotent
        self.assertEqual(len(b), 1)
        self.assertEqual(b.inverse, {1: "a"})

    def test_reassign_same_key_new_value_updates_inverse(self) -> None:
        b = BidirectionalMap()
        b["a"] = 1
        b["a"] = 2
        self.assertEqual(b["a"], 2)
        self.assertEqual(b.inverse, {2: "a"})
        self.assertNotIn(1, b.inverse)

    def test_delete_removes_from_inverse(self) -> None:
        b = BidirectionalMap({"a": 1, "b": 2})
        del b["a"]
        self.assertNotIn("a", b)
        self.assertNotIn(1, b.inverse)
        self.assertEqual(b.inverse[2], "b")

    def test_pop_returns_value_and_syncs_inverse(self) -> None:
        b = BidirectionalMap({"a": 1, "b": 2})
        self.assertEqual(b.pop("a"), 1)
        self.assertNotIn(1, b.inverse)
        self.assertEqual(b.pop("missing", None), None)

    def test_pop_missing_without_default_raises(self) -> None:
        b = BidirectionalMap({"a": 1})
        with self.assertRaises(KeyError):
            b.pop("missing")

    def test_popitem_syncs_inverse(self) -> None:
        b = BidirectionalMap({"a": 1})
        key, value = b.popitem()
        self.assertEqual(key, "a")
        self.assertEqual(value, 1)
        self.assertEqual(len(b), 0)
        self.assertEqual(len(b.inverse), 0)

    def test_clear_empties_both_indexes(self) -> None:
        b = BidirectionalMap({"a": 1, "b": 2})
        b.clear()
        self.assertEqual(len(b), 0)
        self.assertEqual(len(b.inverse), 0)

    def test_setdefault_inserts_when_missing(self) -> None:
        b = BidirectionalMap()
        self.assertEqual(b.setdefault("a", 1), 1)
        self.assertEqual(b.inverse[1], "a")
        # second call returns existing, does not raise despite same value
        self.assertEqual(b.setdefault("a", 1), 1)

    def test_setdefault_with_existing_value_for_new_key_raises(self) -> None:
        b = BidirectionalMap()
        b["a"] = 1
        with self.assertRaises(ValueError):
            b.setdefault("b", 1)

    def test_update_with_dict_and_kwargs(self) -> None:
        b = BidirectionalMap()
        b.update({"a": 1}, b=2)
        self.assertEqual(b["a"], 1)
        self.assertEqual(b["b"], 2)
        self.assertEqual(b.inverse[1], "a")
        self.assertEqual(b.inverse[2], "b")

    def test_update_with_iterable_of_pairs(self) -> None:
        b = BidirectionalMap()
        b.update([("a", 1), ("b", 2)])
        self.assertEqual(b.inverse[1], "a")
        self.assertEqual(b.inverse[2], "b")

    def test_update_too_many_positional_args_raises(self) -> None:
        b = BidirectionalMap()
        with self.assertRaises(TypeError):
            b.update({"a": 1}, {"b": 2})

    def test_copy_produces_independent_instance(self) -> None:
        b = BidirectionalMap({"a": 1, "b": 2})
        c = b.copy()
        c["c"] = 3
        self.assertNotIn("c", b)
        self.assertNotIn(3, b.inverse)
        self.assertEqual(c.inverse[3], "c")

    def test_copy_module_works(self) -> None:
        b = BidirectionalMap({"a": 1})
        c = copy.copy(b)
        self.assertEqual(c, b)
        self.assertIsInstance(c, BidirectionalMap)
        c["b"] = 2
        self.assertNotIn("b", b)

    def test_construct_from_mapping(self) -> None:
        b = BidirectionalMap({"a": 1, "b": 2})
        self.assertEqual(b["a"], 1)
        self.assertEqual(b.inverse[2], "b")

    def test_construct_from_iterable(self) -> None:
        b = BidirectionalMap([("a", 1), ("b", 2)])
        self.assertEqual(b.inverse[1], "a")

    def test_bimap_alias_is_same_class(self) -> None:
        self.assertIs(BiMap, BidirectionalMap)

    def test_len_matches_dict(self) -> None:
        b = BidirectionalMap({"a": 1, "b": 2, "c": 3})
        self.assertEqual(len(b), 3)
        self.assertEqual(len(b.inverse), 3)

    def test_contains_on_values(self) -> None:
        b = BidirectionalMap({"a": 1})
        self.assertIn("a", b)
        self.assertIn(1, b.inverse)
        self.assertNotIn(2, b.inverse)

    def test_equality_with_plain_dict(self) -> None:
        b = BidirectionalMap({"a": 1, "b": 2})
        self.assertEqual(b, {"a": 1, "b": 2})

    def test_none_value_supported(self) -> None:
        b = BidirectionalMap()
        b["a"] = None
        self.assertIs(b["a"], None)
        self.assertEqual(b.inverse[None], "a")

    def test_iter(self) -> None:
        b = BidirectionalMap({"a": 1, "b": 2})
        self.assertEqual(set(iter(b)), {"a", "b"})


if __name__ == "__main__":
    unittest.main()
