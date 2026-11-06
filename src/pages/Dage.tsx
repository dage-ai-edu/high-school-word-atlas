import { ArrowDown, ArrowRight, Brain, Compass, Database, MessageCircle, Sparkles } from "lucide-react";
import { DageParticleHero } from "../ui/DageParticleHero";

const BRAND = `${import.meta.env.BASE_URL}brand`;

const scenes = [
  ["预习", "先自己读和标记，再带着具体卡点问 AI，最后关掉 AI 讲一遍。"],
  ["概念与公式", "不止背定义和公式，要能辨边界、说条件、推得出、换情境还会用。"],
  ["卡住了", "先说清目标、已知、尝试和卡点；AI 从追问开始，确实需要才多帮一点。"],
  ["错题", "不写“粗心”。找到第一个断点，只修这一处，再用陌生题验证。"],
  ["复盘", "每天留下证据，每周找重复，让下一步计划从真实记录里长出来。"],
  ["阶段画像", "看卡点是否更准、AI 帮助是否减少、隔周是否记得、换题是否还会。"],
];

export function Dage() {
  return (
    <article className="dage-page">
      <section className="dage-hero" aria-labelledby="dage-title">
        <div className="dage-stars" aria-hidden="true" />
        <p className="dage-code">DAGE · AI SELF-LEARNING COACH</p>
        <h1 id="dage-title" className="sr-only">
          达哥
        </h1>
        <DageParticleHero />
        <div className="dage-intro">
          <strong>我是达哥。</strong>
          <span>带孩子用 AI 自学</span>
        </div>
        <a className="dage-scroll" href="#dage-method">
          往下看 <ArrowDown size={18} />
        </a>
      </section>

      <div className="dage-content" id="dage-method">
        <header className="dage-lead">
          <p className="eyebrow">达哥 AI 自学者计划</p>
          <h2>不是让 AI 替孩子学，<br />而是让孩子慢慢学会自己学。</h2>
          <p>我把学习拆成能看见、能练习、能验证的一组场景。方向盘始终在孩子手里，AI 是陪练、追问者和记录员，不是答案机器。</p>
        </header>

        <section className="dage-shift" aria-label="学习方式的转变">
          <div>
            <small>从前</small>
            <h3>凭感觉</h3>
            <p>听懂了就当会了，做完就算，错了常常只写一句“粗心”。</p>
          </div>
          <ArrowRight className="dage-shift-arrow" aria-hidden="true" />
          <div className="is-new">
            <small>现在</small>
            <h3>有标准 · 有方法 · 有验证</h3>
            <p>合上书能讲，关掉 AI 能做，换一道新题还能迁移。</p>
          </div>
        </section>

        <section className="dage-principles">
          <header>
            <p className="eyebrow">孩子与 AI 怎么合作</p>
            <h2>开头和结尾，都在孩子手里。</h2>
          </header>
          <ol>
            <li><span>01</span><b>我先想</b><small>先留下自己的尝试</small></li>
            <li><span>02</span><b>我说清楚</b><small>目标、已知、尝试、卡点</small></li>
            <li className="is-ai"><span>03</span><b>AI 再帮</b><small>从追问和最小提示开始</small></li>
            <li><span>04</span><b>AI 退出</b><small>把任务交还给孩子</small></li>
            <li><span>05</span><b>我自己完成</b><small>用新情境再次验证</small></li>
          </ol>
        </section>

        <section className="dage-scenes">
          <header>
            <p className="eyebrow">学习场景</p>
            <h2>孩子真正遇到问题时，知道怎么开始。</h2>
          </header>
          <div className="dage-scene-grid">
            {scenes.map(([title, copy], index) => (
              <article key={title}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <h3>{title}</h3>
                <p>{copy}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="dage-system">
          <div className="dage-system-copy">
            <p className="eyebrow">一套会成长的学习系统</p>
            <h2>学习产生证据，证据帮助孩子做下一次决定。</h2>
            <p>预习记录、概念卡、错题卡和每日复盘，都会留下来。AI 可以帮助扫库和归并，但最终由孩子说出：我变在哪、还卡在哪、下一步先改什么。</p>
          </div>
          <div className="dage-system-cards">
            <div><Compass /><b>孩子掌舵</b><span>自主选择下一步重点</span></div>
            <div><Brain /><b>AI 陪练</b><span>追问、提示、记录与验证</span></div>
            <div><Database /><b>证据留下</b><span>自己的学习资产持续累积</span></div>
            <div><Sparkles /><b>逐步退出</b><span>示范 → 提示 → 验收 → 不在场</span></div>
          </div>
        </section>

        <section className="dage-contact" id="dage-wechat">
          <div>
            <p className="eyebrow">联系达哥</p>
            <h2>一起带孩子，<br />把 AI 真正用来学习。</h2>
            <p>如果你也在陪孩子探索 AI 自学，可以扫码添加达哥微信。备注“词光”，方便我知道你从这里来。</p>
            <span><MessageCircle /> 微信扫码添加达哥</span>
          </div>
          <figure>
            <img src={`${BRAND}/dage-wechat.jpg`} alt="达哥微信二维码" loading="lazy" />
          </figure>
        </section>

        <blockquote className="dage-finale">
          <p>遇到不会的，我知道怎么开始；<br />做错了，我知道怎么修；<br />学了一段时间，我知道下一步往哪里用力。</p>
          <footer>没有失败，只有迭代。</footer>
        </blockquote>
      </div>
    </article>
  );
}
