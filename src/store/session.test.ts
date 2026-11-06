import assert from "node:assert/strict";
import { test } from "node:test";
import type { Atlas, WordRef } from "../atlas/types";
import { nextNew } from "./session";
import { defaultSettings, emptyProgress } from "./store";

const ref = (id: string, order: number, cefr: number): WordRef => ({ id, word: id, zh: id, ipa: "", cefr, topic: 0, media: 0, order });
const words = [ref("junior", 0, 1), ref("g10a", 1996, 2), ref("g10b", 2169, 2), ref("g11", 2661, 3), ref("g12", 3201, 3)];
const atlas = { words } as Atlas;

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

