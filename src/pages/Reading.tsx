import { BookOpen, ExternalLink, Languages, Volume2 } from "lucide-react";

const ORIGINAL_SHORTS = "https://0xlei.tech/words/#/read";
const ORIGINAL_BOOK = "https://0xlei.tech/words/#/books/the-little-prince";

export function Reading() {
  return (
    <section className="reading-page page">
      <header className="reading-hero">
        <div>
          <p className="eyebrow">书房 · READ & GROW</p>
          <h1>把词汇放进故事里，<br />才会真正活起来。</h1>
          <p>这里保留阅读入口。完整分级短文和《小王子》27 章内容，都在词光原站继续阅读。</p>
        </div>
        <BookOpen aria-hidden="true" />
      </header>

      <section className="reading-original-library">
        <div>
          <p className="eyebrow">原站完整短文库</p>
          <h2>从 A1、A2 到 B1，<br />去词光原站继续读。</h2>
          <p>原站包含完整短文列表、词汇标记和练习进度。我们不再只展示三篇示例，也不把原作者的文章复制到这里。</p>
          <div className="reading-levels-static" aria-label="保留的阅读级别">
            <span>A1 · 入门</span><span>A2 · 基础</span><span>B1 · 进阶</span>
          </div>
        </div>
        <a className="reading-open-button" href={ORIGINAL_SHORTS} target="_blank" rel="noreferrer">
          <span>打开完整短文库</span><ExternalLink />
        </a>
      </section>

      <section className="reading-bookcase">
        <figure className="little-prince-cover">
          <img src={`${import.meta.env.BASE_URL}brand/little-prince-cover-v2.jpg`} alt="少年坐在深蓝小星球上，身旁有一朵玫瑰" />
          <figcaption>
            <small>ANTOINE DE SAINT-EXUPÉRY</small>
            <b>The Little Prince</b>
            <span>小 王 子</span>
          </figcaption>
        </figure>
        <div className="reading-book-copy">
          <p className="eyebrow">原版书 · 1943</p>
          <h2>小王子</h2>
          <h3>The Little Prince</h3>
          <p>安托万·德·圣埃克苏佩里 · 27 章 · B1</p>
          <div className="reading-features"><span><Languages /> 双语阅读</span><span><Volume2 /> 双语音频</span></div>
          <p className="reading-rights">原站的新译、插图与音频未包含在开源仓库许可中，因此从这里进入原作者的完整版本。</p>
          <a className="btn btn-primary btn-xl" href={ORIGINAL_BOOK} target="_blank" rel="noreferrer">开始阅读 <ExternalLink size={18} /></a>
        </div>
      </section>
    </section>
  );
}
