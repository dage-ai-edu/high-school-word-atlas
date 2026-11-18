import assert from "node:assert/strict";
import { test } from "node:test";
import type { Atlas, WordRef } from "../atlas/types";
import { additionalStudyPlan, buildSession, nextNew, resumableSession } from "./session";
import { dayKey, defaultSettings, emptyProgress, type ActiveSession } from "./store";

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


const batchWords = Array.from({ length: 12 }, (_, i) => ref(`word-${i}`, 1996 + i, 2));
const batchAtlas = { words: batchWords, byId: new Map(batchWords.map((word) => [word.id, word])) } as Atlas;
const batchSettings = { ...defaultSettings, dailyNew: 5, startMode: "textbook" as const, startStage: 1 };
const learnedCard = { due: Date.now() + 86400000, s: 3, d: 5, el: 0, sd: 1, ls: 0, reps: 1, lapses: 0, st: 2 as const, seen: 1000 };

test("extra study starts five unseen words after finishing today's quota without changing the quota or records", () => {
  const p = emptyProgress("x");
  p.days[dayKey()] = { n: 5, r: 5, c: 5, t: 30 };
  p.cards = Object.fromEntries(batchWords.slice(0, 5).map((word) => [word.id, learnedCard]));
  p.session = session({ finished: Date.now() });
  const before = structuredClone(p);
  const addition = additionalStudyPlan(batchAtlas, p, batchSettings);
  assert.deepEqual(addition.ids, batchWords.slice(5, 10).map((word) => word.id));
  assert.equal(addition.startStage, 1);
  const next = buildSession(batchAtlas, p, batchSettings, { ids: addition.ids });
  assert.equal(next.steps.length, 10);
  assert.equal(next.index, 0);
  assert.equal(next.finished, undefined);
  assert.deepEqual(next.newIds, addition.ids);
  assert.deepEqual(p, before);
  assert.equal(batchSettings.dailyNew, 5);
});

test("extra study offers the next nonempty textbook stage when the selected stage is finished", () => {
  const p = emptyProgress("x");
  p.cards.g10a = learnedCard;
  p.cards.g10b = learnedCard;
  assert.deepEqual(additionalStudyPlan(atlas, p, batchSettings), { ids: ["g11"], startStage: 3 });
});

test("extra study keeps the remaining words in the current stage before moving on", () => {
  const p = emptyProgress("x");
  p.cards = Object.fromEntries(batchWords.slice(0, 10).map((word) => [word.id, learnedCard]));
  assert.deepEqual(additionalStudyPlan(batchAtlas, p, batchSettings), { ids: ["word-10", "word-11"], startStage: 1 });
});

test("extra study reports exhaustion without looping back into earlier textbook stages", () => {
  const p = emptyProgress("x");
  p.cards.g12 = learnedCard;
  assert.deepEqual(additionalStudyPlan(atlas, p, { ...batchSettings, startStage: 4 }), { ids: [], startStage: 4 });
});

test("extra study preserves the CEFR path", () => {
  const p = emptyProgress("x");
  assert.deepEqual(additionalStudyPlan(atlas, p, { ...batchSettings, startMode: "cefr", startLevel: 3 }, 2), { ids: ["g11", "g12"], startStage: 1 });
});
