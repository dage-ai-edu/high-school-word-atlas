import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import vm from "node:vm";

const scope = "https://example.test/high-school-word-atlas/";
const prefix = "word-atlas:/high-school-word-atlas/:";
const source = readFileSync(new URL("../../public/sw.js", import.meta.url), "utf8");

function worker(fetcher: (request: { url: string }) => Promise<Response>) {
  const handlers = new Map<string, (event: any) => void>();
  const data = new Map<string, Map<string, Response>>();
  const cacheFor = (name: string) => {
    let entries = data.get(name);
    if (!entries) data.set(name, (entries = new Map()));
    return {
      match: async (request: { url: string } | string) => entries!.get(typeof request === "string" ? request : request.url)?.clone(),
      put: async (request: { url: string }, response: Response) => { entries!.set(request.url, response); },
      keys: async () => [...entries!.keys()],
      delete: async (key: string) => entries!.delete(key),
    };
  };
  vm.runInNewContext(source, {
    URL, Response, location: { origin: "https://example.test" }, fetch: fetcher,
    caches: {
      keys: async () => [...data.keys()],
      open: async (name: string) => cacheFor(name),
      delete: async (name: string) => data.delete(name),
      match: async (request: { url: string }) => {
        for (const entries of data.values()) if (entries.has(request.url)) return entries.get(request.url)!.clone();
      },
    },
    self: { registration: { scope }, clients: { claim: async () => {} }, skipWaiting: () => {}, addEventListener: (name: string, handler: (event: any) => void) => handlers.set(name, handler) },
  });
  return {
    data,
    async activate() {
      let work: Promise<unknown>;
      handlers.get("activate")!({ waitUntil: (promise: Promise<unknown>) => { work = promise; } });
      await work!;
    },
    async request(path: string) {
      let result: Promise<Response>;
      handlers.get("fetch")!({
        request: { method: "GET", mode: "cors", url: scope + path, headers: new Headers() },
        respondWith: (promise: Promise<Response>) => { result = promise; },
      });
      return result!;
    },
  };
}

test("word entry chunks refresh even when an older chunk is cached", async () => {
  const sw = worker(async () => new Response('[{"id":"new-word"}]'));
  sw.data.set(prefix + "v2-shell", new Map([[scope + "atlas/entries/0.json", new Response('[{"id":"old-word"}]')]]));
  assert.equal(await (await sw.request("atlas/entries/0.json")).text(), '[{"id":"new-word"}]');
});

test("offline entry failures never fall back to HTML", async () => {
  const sw = worker(async () => { throw new Error("offline"); });
  sw.data.set(prefix + "v2-shell", new Map([[scope, new Response("<html>App shell</html>")]]));
  assert.equal((await sw.request("atlas/entries/0.json")).type, "error");
  sw.data.get(prefix + "v2-shell")!.set(scope + "atlas/entries/0.json", new Response("[]"));
  assert.equal(await (await sw.request("atlas/entries/0.json")).text(), "[]");
});

test("cache cleanup preserves the junior edition and legacy shared caches", async () => {
  const sw = worker(async () => new Response());
  for (const key of [prefix + "v1-shell", prefix + "v2-shell", "word-atlas:/junior-word-atlas/:v1-shell", "atlas-v1-shell"]) sw.data.set(key, new Map());
  await sw.activate();
  assert.equal(sw.data.has(prefix + "v1-shell"), false);
  assert.equal(sw.data.has(prefix + "v2-shell"), true);
  assert.equal(sw.data.has("word-atlas:/junior-word-atlas/:v1-shell"), true);
  assert.equal(sw.data.has("atlas-v1-shell"), true);
});

test("existing exact-URL cached entries remain available offline after upgrade", async () => {
  const sw = worker(async () => { throw new Error("offline"); });
  sw.data.set("atlas-v1-shell", new Map([[scope + "atlas/entries/0.json", new Response('[{"id":"offline-word"}]')]]));
  assert.equal(await (await sw.request("atlas/entries/0.json")).text(), '[{"id":"offline-word"}]');
});
