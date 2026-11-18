import assert from "node:assert/strict";
import { test } from "node:test";
import type { Atlas, WordRef } from "../atlas/types";
import { nextNew, resumableSession } from "./session";
import { defaultSettings, emptyProgress, type ActiveSession } from "./store";

const ref = (id: string, order: number, cefr: number): WordRef => ({ id, word: id, zh: id, ipa: "", cefr, topic: 0, media: 0, order });
const words = [ref("junior", 0, 1), ref("g10a", 1996, 2), ref("g10b", 2169, 2), ref("g11", 2661, 3), ref("g12", 3201, 3)];
const atlas = { words, byId: new Map(words.map((word) => [word.id, word])) } as Atlas;

test("starts new words from the selected textbook stage", () => {
  const settings = { ...defaultSettings, startMode: "textbook" as const, startStage: 3 };
  assert.deepEqual(nextNew(atlas, emptyProgress("x"), settings, 2), ["g11"]);
});

test("starts senior year from the selected textbook stage", () => {
  const settings = { ...defaultSettings, startMode: "textbook" as const, startStage: 4 };
  assert.deepEqual(nextNew(atlas, emptyProgress("x"), settings, 2), ["g12"]);
});

test("keeps CEFR starts available as the graded alternative", () => {
  const settings = { ...defaultSettings, startMode: "cefr" as const, startLevel: 3 };
  assert.deepEqual(nextNew(atlas, emptyProgress("x"), settings, 2), ["g11", "g12"]);
});

const session = (patch: Partial<ActiveSession> = {}): ActiveSession => ({
  id: "saved", started: 1000, steps: [{ id: "g10a", kind: "intro" }], index: 0,
  graded: {}, newIds: ["g10a"], reviewIds: [], ...patch,
});

test("empty and exhausted sessions do not block a new daily plan", () => {
  assert.equal(resumableSession(atlas, session({ steps: [] })), null);
  assert.equal(resumableSession(atlas, session({ index: 1 })), null);
  assert.equal(resumableSession(atlas, session({ finished: 2000 })), null);
});

test("keeps a valid partial session and its pending answer unchanged", () => {
  const saved = session({ pending: { correct: true, value: "g10a" } });
  assert.equal(resumableSession(atlas, saved), saved);
});

test("skips removed words and discards the removed step's pending feedback", () => {
  const saved = session({
    steps: [{ id: "removed", kind: "intro" }, { id: "g10a", kind: "intro" }],
    newIds: ["removed", "g10a"],
    pending: { correct: false, value: "removed" },
  });
  const repaired = resumableSession(atlas, saved)!;
  assert.deepEqual(repaired.steps, [{ id: "g10a", kind: "intro" }]);
  assert.equal(repaired.index, 0);
  assert.equal(repaired.pending, undefined);
  assert.deepEqual(repaired.newIds, ["g10a"]);
  assert.equal(saved.steps.length, 2);
});

test("reindexes removed completed steps without replaying learned steps", () => {
  const repaired = resumableSession(atlas, session({
    steps: [{ id: "removed", kind: "intro" }, { id: "g10a", kind: "intro" }, { id: "g10b", kind: "intro" }],
    index: 2,
  }))!;
  assert.equal(repaired.index, 1);
  assert.equal(repaired.steps[repaired.index].id, "g10b");
});

test("rebuilds invalid multiple-choice options from current entries", () => {
  const dense = words.map((word, order) => ({ ...word, order }));
  const optionAtlas = { ...atlas, words: dense, byId: new Map(dense.map((word) => [word.id, word])) };
  const repaired = resumableSession(optionAtlas, session({
    steps: [{ id: "g10a", kind: "meaning", options: ["removed"] }],
  }))!;
  const options = (repaired.steps[0] as { options: string[] }).options;
  assert.ok(options.includes("g10a"));
  assert.ok(options.every((id) => atlas.byId.has(id)));
  assert.ok(options.length >= 2);
});

