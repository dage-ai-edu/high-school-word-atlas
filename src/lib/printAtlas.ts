import type { Atlas, WordRef } from "../atlas/types";

export interface AtlasPrintFilters {
  query: string;
  level?: string;
  topic?: string;
  status: string;
  statusLabel: string;
}

const escapeHtml = (value: string) =>
  value.replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]!);

function filterLabels(atlas: Atlas, filters: AtlasPrintFilters) {
  const topic = filters.topic ? atlas.topics.find(([key]) => key === filters.topic)?.[1] : undefined;
  return [
    filters.level ? `难度：${filters.level}` : "难度：全部",
    `主题：${topic ?? "全部"}`,
    `状态：${filters.statusLabel}`,
    filters.query.trim() ? `搜索：${filters.query.trim()}` : "",
  ].filter(Boolean);
}

export function buildAtlasPrintHtml(atlas: Atlas, words: WordRef[], filters: AtlasPrintFilters) {
  const labels = filterLabels(atlas, filters);
  const filename = `高中专属词光-${filters.statusLabel}-${words.length}词`;
  const date = new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
  const rows = words
    .map(
      (word, index) => `
        <tr>
          <td class="number">${index + 1}</td>
          <td class="check"><span></span></td>
          <td class="word" lang="en">${escapeHtml(word.word)}</td>
          <td class="ipa">${escapeHtml(word.ipa || "-")}</td>
          <td class="meaning">${escapeHtml(word.zh)}</td>
          <td class="practice"><i></i><i></i><i></i></td>
        </tr>`,
    )
    .join("");

  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>${escapeHtml(filename)}</title>
  <style>
    :root { color-scheme: light; }
    * { box-sizing: border-box; }
    body { margin: 0; color: #172033; background: #eef1f5; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif; }
    .screen-actions { position: sticky; top: 0; z-index: 2; display: flex; justify-content: center; gap: 12px; padding: 14px; background: rgba(23,32,51,.92); }
    .screen-actions button { border: 0; border-radius: 999px; padding: 10px 20px; color: #172033; background: #f5eee0; font: 600 14px/1 inherit; cursor: pointer; }
    .screen-actions .secondary { color: #fff; background: rgba(255,255,255,.16); }
    main { width: 210mm; min-height: 297mm; margin: 18px auto; padding: 12mm 12mm 16mm; background: #fff; box-shadow: 0 20px 60px rgba(26,35,55,.14); }
    header { padding-bottom: 7mm; border-bottom: 2px solid #172033; }
    .brand { margin: 0 0 3mm; color: #687184; font-size: 10px; font-weight: 700; letter-spacing: .16em; }
    h1 { margin: 0; font-family: Georgia, "Songti SC", serif; font-size: 24px; line-height: 1.2; }
    .meta { display: flex; flex-wrap: wrap; gap: 5px; margin: 4mm 0 0; }
    .meta span { padding: 3px 8px; border: 1px solid #cfd4dc; border-radius: 999px; color: #4e596d; font-size: 9px; }
    .summary { display: flex; justify-content: space-between; gap: 12px; margin: 4mm 0 3mm; color: #657084; font-size: 9px; }
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    thead { display: table-header-group; }
    th { padding: 2.4mm 1.8mm; color: #fff; background: #29344b; font-size: 8px; font-weight: 600; text-align: left; }
    td { padding: 2.4mm 1.8mm; border-bottom: .35mm solid #dfe3e9; vertical-align: middle; }
    tr { break-inside: avoid; page-break-inside: avoid; }
    tbody tr:nth-child(even) { background: #f7f8fa; }
    .number { width: 8mm; color: #7a8392; font-size: 8px; text-align: center; }
    .check { width: 8mm; text-align: center; }
    .check span { display: inline-block; width: 3.5mm; height: 3.5mm; border: .35mm solid #596376; border-radius: .7mm; }
    .word { width: 34mm; font: 700 12px/1.2 Georgia, serif; }
    .ipa { width: 33mm; color: #697386; font: 9px/1.2 "SFMono-Regular", Consolas, monospace; }
    .meaning { font-size: 9.5px; line-height: 1.35; }
    .practice { width: 28mm; white-space: nowrap; }
    .practice i { display: inline-block; width: 6mm; margin-right: 1.8mm; border-bottom: .3mm solid #8f97a5; }
    footer { position: fixed; right: 12mm; bottom: 5mm; left: 12mm; display: flex; justify-content: space-between; color: #858d99; font-size: 7px; }
    @page { size: A4 portrait; margin: 10mm 0 12mm; }
    @media print {
      body { background: #fff; print-color-adjust: exact; -webkit-print-color-adjust: exact; }
      .screen-actions { display: none !important; }
      main { width: auto; min-height: 0; margin: 0; padding: 0 12mm 12mm; box-shadow: none; }
    }
  </style>
</head>
<body>
  <div class="screen-actions">
    <button onclick="window.print()">打印 / 保存为 PDF</button>
    <button class="secondary" onclick="window.close()">关闭</button>
  </div>
  <main>
    <header>
      <p class="brand">HIGH SCHOOL WORD ATLAS · 高中专属词光</p>
      <h1>词汇学习打印表</h1>
      <div class="meta">${labels.map((label) => `<span>${escapeHtml(label)}</span>`).join("")}<span>共 ${words.length.toLocaleString("zh-CN")} 词</span></div>
    </header>
    <div class="summary"><span>姓名：________________　班级：____________</span><span>导出日期：${date}</span></div>
    <table>
      <thead><tr><th class="number">序号</th><th class="check">完成</th><th class="word">单词</th><th class="ipa">音标</th><th class="meaning">中文释义</th><th class="practice">听写练习</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  </main>
  <footer><span>一词一画，点亮高中词汇。</span><span>high-school-word-atlas</span></footer>
</body>
</html>`;
}

export function printAtlasPdf(atlas: Atlas, words: WordRef[], filters: AtlasPrintFilters) {
  if (!words.length) return false;
  const printWindow = window.open("", "_blank", "popup,width=980,height=900");
  if (!printWindow) return false;
  printWindow.opener = null;
  printWindow.document.open();
  printWindow.document.write(buildAtlasPrintHtml(atlas, words, filters));
  printWindow.document.close();
  const launch = () => window.setTimeout(() => printWindow.print(), 250);
  if (printWindow.document.fonts?.ready) void printWindow.document.fonts.ready.then(launch);
  else launch();
  return true;
}
