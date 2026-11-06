import { ArrowUpRight, Database, Github, Heart } from "lucide-react";
import { useAtlas } from "../atlas/context";
import { REPO_URL } from "../config";

const BASE = import.meta.env.BASE_URL;
const UPSTREAM_URL = "https://github.com/designfuchen/word-atlas";

export function About() {
  const atlas = useAtlas();
  return (
    <div className="page about">
      <header className="about-hero">
        <img src={`${BASE}brand/og.webp`} alt="" />
        <div>
          <p className="eyebrow">关于高中专属词光</p>
          <h1 className="display">一词一画，点亮高中词汇。</h1>
          <p className="lede">
            这套累计词库保留初中专属词光的基础词，并合并人教版高中英语必修第一至第三册、选择性必修第一至第四册，共 {atlas.count.toLocaleString()} 个学习词。3159 个词复用词光官方完整词条，88 个复用初中版补充词条，另有 451 个教材补充词。
          </p>
          <p className="lede">无需注册，学习记录只保存在当前浏览器中。学习范围可按初中基础、高一上、高一下、高二和高三切换。</p>
          <div className="about-actions">
            <a className="btn btn-primary" href={UPSTREAM_URL} target="_blank" rel="noreferrer">
              <Github size={18} /> 查看词光原版项目
            </a>
            <a className="btn btn-ghost" href={`${UPSTREAM_URL}/tree/main/data`} target="_blank" rel="noreferrer">
              <Database size={18} /> 查看原版数据规范
            </a>
          </div>
        </div>
      </header>

      <div className="about-grid">
        <section className="panel">
          <h3 className="eyebrow">为什么记得住</h3>
          <ul className="feature-list">
            <li>
              <b>先看见。</b>词光官方词条保留原版插画；教材补充词使用同版式视觉词卡。
            </li>
            <li>
              <b>再想起。</b>选义、看图补句、听音辨词、拼写，从认得走到会写。
            </li>
            <li>
              <b>刚好在快忘时重逢。</b>FSRS 是新版 Anki 用的开源记忆算法，只在你快要遗忘时安排复习。
            </li>
            <li>
              <b>分数诚实。</b>只算第一次作答。答错的词会换个题型再见一面，但不会抬高正确率。
            </li>
            <li>
              <b>进度只属于你。</b>没有账号，没有服务器，数据存在你的浏览器里，随时能导出。
            </li>
          </ul>
        </section>

        <section className="panel">
          <h3 className="eyebrow">快捷键</h3>
          <dl className="keys">
            <div>
              <dt>
                <kbd>⌘</kbd>
                <kbd>K</kbd> 或 <kbd>/</kbd>
              </dt>
              <dd>搜索任何词</dd>
            </div>
            <div>
              <dt>
                <kbd>1</kbd>–<kbd>4</kbd>
              </dt>
              <dd>选择答案</dd>
            </div>
            <div>
              <dt>
                <kbd>Enter</kbd>
              </dt>
              <dd>确认 / 继续</dd>
            </div>
            <div>
              <dt>
                <kbd>←</kbd> <kbd>→</kbd>
              </dt>
              <dd>词卡里切换上一个、下一个</dd>
            </div>
            <div>
              <dt>
                <kbd>Esc</kbd>
              </dt>
              <dd>关闭弹窗</dd>
            </div>
          </dl>
        </section>

        <section className="panel">
          <h3 className="eyebrow">内容从哪里来</h3>
          <p className="muted">
            3159 个重合词的释义、例句、搭配、提示、插画和音频来自 Word Atlas（词光）开源版。教材补充词的中文释义来自本地教材词汇表及用户提供的 50 页词表 PDF，视觉词卡由本项目生成，缺少独立录音时使用设备语音。
          </p>
          <p className="muted">用户提供的 PDF 共解析出 2596 条教材项目，包括 2147 条独立词记录和 449 条短语或多词项目。与原高中词库及初中基础词合并后，最终形成 3698 个不重复的累计学习词；短语单独保存，没有拿来凑单词数量。</p>
          <p className="muted">原项目：Word Atlas contributors（词光）。代码与原版内容分别遵循其仓库标注的许可证；教材补充释义仅用于个人学习，公开发布前需再次核对教材内容授权边界。</p>
        </section>

        <section className="panel">
          <h3 className="eyebrow">给开发者</h3>
          <p className="muted">
            <code>data/word-atlas.json</code> 和 <code>.csv</code> 是高中筛选词库；<code>public/atlas</code> 里是网页使用的分块数据和媒体。教材来源、年级映射、重合词及补充词清单保存在 <code>data/high-school-source</code>，便于复核。
          </p>
          <a className="link" href={`${REPO_URL}#readme`} target="_blank" rel="noreferrer">
            阅读文档 <ArrowUpRight size={14} />
          </a>
        </section>
      </div>
      <p className="colophon">
        <Heart size={14} /> 做给每一个在背单词的人。
      </p>
    </div>
  );
}
