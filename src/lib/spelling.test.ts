import assert from "node:assert/strict";
import { test } from "node:test";
import { spellingSlots } from "./spelling";

const errors = (value: string, target = "government") =>
  spellingSlots(value, target).flatMap((slot, index) => slot.kind === "match" ? [] : [{ index, ...slot }]);

test("keeps every entered letter for matching and extra input", () => {
  assert.deepEqual(errors("government"), []);
  assert.deepEqual(errors("governmentt"), [{ index: 10, kind: "extra", typed: "t" }]);
  assert.deepEqual(errors("governxment"), [{ index: 6, kind: "extra", typed: "x" }]);
});

test("marks a missing middle or final letter without marking the remaining letters", () => {
  assert.deepEqual(errors("govenment"), [{ index: 4, kind: "missing", expected: "r" }]);
  assert.deepEqual(errors("governmen"), [{ index: 9, kind: "missing", expected: "t" }]);
  assert.deepEqual(errors("governmant"), [{ index: 7, kind: "wrong", typed: "a", expected: "e" }]);
});

test("accepts the same typography as the spelling grader and preserves what was typed", () => {
  assert.deepEqual(errors(" DON’T ", "don't"), []);
  assert.equal(spellingSlots("Government", "government").map((slot) => "typed" in slot ? slot.typed : "").join(""), "Government");
  assert.deepEqual(errors("highschool", "high school"), [{ index: 4, kind: "missing", expected: " " }]);
});
