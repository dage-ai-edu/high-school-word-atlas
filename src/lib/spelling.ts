import { normalize } from "./text";

type SpellingSlot =
  | { kind: "match"; typed: string }
  | { kind: "extra"; typed: string }
  | { kind: "missing"; expected: string }
  | { kind: "wrong"; typed: string; expected: string };

export function spellingSlots(value: string, target: string): SpellingSlot[] {
  const typed = Array.from(value);
  if (normalize(value) === normalize(target)) return typed.map((ch) => ({ kind: "match", typed: ch }));

  const expected = Array.from(target);
  const comparable = (ch: string) => (/\s/u.test(ch) ? " " : normalize(ch));
  const input = typed.map(comparable);
  const answer = expected.map(comparable);
  // Align the strings with the fewest edits so one missing letter does not mark the suffix wrong.
  const distance = Array.from({ length: typed.length + 1 }, () => Array<number>(expected.length + 1).fill(0));
  for (let i = typed.length; i >= 0; i--) {
    for (let j = expected.length; j >= 0; j--) {
      if (i === typed.length) distance[i][j] = expected.length - j;
      else if (j === expected.length) distance[i][j] = typed.length - i;
      else if (input[i] === answer[j]) distance[i][j] = distance[i + 1][j + 1];
      else distance[i][j] = 1 + Math.min(distance[i + 1][j], distance[i][j + 1], distance[i + 1][j + 1]);
    }
  }

  const slots: SpellingSlot[] = [];
  let i = 0;
  let j = 0;
  while (i < typed.length || j < expected.length) {
    if (i < typed.length && j < expected.length && input[i] === answer[j]) {
      slots.push({ kind: "match", typed: typed[i++] });
      j++;
    } else if (j < expected.length && distance[i][j] === 1 + distance[i][j + 1]) {
      slots.push({ kind: "missing", expected: expected[j++] });
    } else if (i < typed.length && distance[i][j] === 1 + distance[i + 1][j]) {
      slots.push({ kind: "extra", typed: typed[i++] });
    } else {
      slots.push({ kind: "wrong", typed: typed[i++], expected: expected[j++] });
    }
  }
  return slots;
}
