import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { chromium } from "playwright";

// Run against a preview server or the deployed edition using ATLAS_TEST_URL.
const base = process.env.ATLAS_TEST_URL || "http://127.0.0.1:5194/high-school-word-atlas/";
const atlas = JSON.parse(readFileSync(new URL("../public/atlas/index.json", import.meta.url), "utf8"));
const key = `word-atlas:v2:${atlas.id}`;
const browser = await chromium.launch({
  ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}),
  headless: true,
});
try {
  for (const scenario of ["normal", "stage-finished", "all-finished"]) {
    const context = await browser.newContext({ serviceWorkers: "block" });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.route(/\.(mp3|webp|svg|jpe?g|png)(\?|$)/, (route) => route.abort());
    const seeded = scenario === "normal" ? [] : atlas.words.slice(1996, scenario === "all-finished" ? atlas.words.length : 2164).map((w) => w[0]);
    await page.addInitScript(({ seeded, key, datasetId }) => {
      if (sessionStorage.getItem("test-seeded")) return;
      sessionStorage.setItem("test-seeded", "yes");
      const now = Date.now();
      const card = { due: now + 86400000, s: 3, d: 5, el: 0, sd: 1, ls: 0, reps: 2, lapses: 0, st: 2, seen: now - 86400000 };
      localStorage.setItem("word-atlas:settings", JSON.stringify({ onboarded: true, splash: false, autoplay: false, sfx: false, ambience: "off", startMode: "textbook", startStage: 1, dailyNew: 5 }));
      localStorage.setItem(key, JSON.stringify({ version: 2, datasetId, cards: Object.fromEntries(seeded.map((id) => [id, card])), bookmarks: seeded.slice(0, 1), days: {}, typing: [], mistakes: [], session: null }));
    }, { seeded, key, datasetId: atlas.id });
    const progress = () => page.evaluate((key) => JSON.parse(localStorage.getItem(key)), key);
    async function finishRound() {
      for (let i = 0; i < 25; i++) {
        await page.waitForTimeout(400);
        if (await page.locator(".summary").count()) break;
        if (await page.locator(".intro button.btn-primary").count()) await page.locator(".intro button.btn-primary").click();
        else if (await page.locator(".feedback button").count()) await page.locator(".feedback button").click();
        else {
          const session = (await progress()).session;
          await page.locator(`[data-option="${session.steps[session.index].id}"]`).click();
        }
      }
      await page.locator(".summary").waitFor();
      await page.getByRole("button", { name: "完成", exact: true }).click();
      await page.locator(".journey-actions").waitFor();
    }
    await page.goto(base, { waitUntil: "domcontentloaded" });
    if (scenario === "all-finished") {
      assert.match(await page.locator(".journey-lede").innerText(), /已学完/);
      await page.getByRole("button", { name: /调整学习范围/ }).click();
      await page.locator(".page.me").waitFor();
    } else {
      await page.locator(".journey-actions button").first().click();
      await page.locator(".intro .headword").waitFor();
      await finishRound();
      const before = await progress();
      assert.equal(Object.values(before.days)[0].n, 5);
      const button = page.locator(".journey-actions button").first();
      assert.match(await button.innerText(), scenario === "normal" ? /再认识 5/ : /继续高一下.*5/);
      await button.click();
      await page.locator(".intro .headword").waitFor();
      await page.waitForTimeout(350);
      const after = await progress();
      assert.equal(after.session.newIds.length, 5);
      assert.equal(after.session.index, 0);
      assert.ok(after.session.newIds.every((id) => !before.cards[id]));
      assert.deepEqual(after.cards, before.cards);
      assert.deepEqual(after.days, before.days);
      assert.deepEqual(after.bookmarks, before.bookmarks);
      const settings = await page.evaluate(() => JSON.parse(localStorage.getItem("word-atlas:settings")));
      assert.equal(settings.dailyNew, 5);
      assert.equal(settings.startStage, scenario === "normal" ? 1 : 2);
      await page.reload();
      await page.locator(".intro .headword").waitFor();
      assert.deepEqual((await progress()).session.newIds, after.session.newIds);
      if (scenario === "normal") {
        await finishRound();
        await page.locator(".journey-actions button").first().click();
        await page.locator(".intro .headword").waitFor();
        await page.waitForTimeout(350);
        const third = await progress();
        assert.equal(third.session.newIds.length, 5);
        assert.ok(third.session.newIds.every((id) => !third.cards[id]));
        assert.equal(Object.values(third.days)[0].n, 10);
      }
    }
    assert.deepEqual(errors, []);
    await context.close();
    console.log(`PASS extra study: ${scenario}`);
  }
} finally {
  await browser.close();
}
