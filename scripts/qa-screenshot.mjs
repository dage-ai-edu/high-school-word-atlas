#!/usr/bin/env node
import { chromium } from "playwright";

const app = process.argv[2] || "http://127.0.0.1:5188/";
const executablePath = process.env.CHROME_PATH;
const browser = await chromium.launch(executablePath ? { executablePath } : {});
const context = await browser.newContext({ viewport: { width: 1440, height: 1200 }, colorScheme: "light" });
await context.addInitScript(() => {
  localStorage.setItem(
    "word-atlas:settings",
    JSON.stringify({ onboarded: true, startLevel: 0, dailyNew: 10, autoplay: false, splash: false, theme: "light" }),
  );
});
const page = await context.newPage();
const errors = [];
page.on("console", (message) => {
  if (message.type() === "error") errors.push(message.text());
});
page.on("pageerror", (error) => errors.push(error.message));
await page.goto(new URL("#/w/unit", app).href, { waitUntil: "networkidle" });
await page.locator(".sheet-root .entry").waitFor();
await page.screenshot({ path: "/private/tmp/junior-word-atlas-word-ready.png" });
const image = await page.locator(".sheet-root .entry-art img").first().getAttribute("src");
const audioButtons = await page.locator(".sheet-root button[aria-label*='发音'], .sheet-root button[aria-label*='朗读']").count();
const result = {
  title: await page.title(),
  heading: await page.locator(".sheet-root .headword").textContent(),
  image,
  audioButtons,
  errors,
};
console.log(JSON.stringify(result, null, 2));
await browser.close();
