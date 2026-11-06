import assert from "node:assert/strict";
import { test } from "node:test";
import type { Atlas, WordRef } from "../atlas/types";
import { buildAtlasPrintHtml } from "./printAtlas";

const word = (id: string, value: string): WordRef => ({ id, word: value, zh: "n. 测试", ipa: "/test/", cefr: 0, topic: 0, media: 0, order: 0 });
const atlas = { topics: [["education", "教育"]], cefr: ["A1"] } as Atlas;

test("builds a printable sheet from the current filters", () => {
  const html = buildAtlasPrintHtml(atlas, [word("one", "unit"), word("two", "spell")], {
    query: "",
    level: "A1",
    topic: "education",
    status: "learning",
    statusLabel: "学习中",
  });
  assert.match(html, /状态：学习中/);
  assert.match(html, /主题：教育/);
  assert.match(html, /共 2 词/);
  assert.equal((html.match(/<tr>/g) ?? []).length, 3);
});

test("escapes words and searches before writing a new document", () => {
  const html = buildAtlasPrintHtml(atlas, [word("unsafe", "<script>alert(1)</script>")], {
    query: "<教材>",
    status: "all",
    statusLabel: "全部",
  });
  assert.doesNotMatch(html, /<script>alert\(1\)<\/script>/);
  assert.match(html, /&lt;script&gt;alert\(1\)&lt;\/script&gt;/);
  assert.match(html, /搜索：&lt;教材&gt;/);
});
