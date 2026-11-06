import { ArrowRight } from "lucide-react";
import { useState } from "react";
import { useAtlas } from "../atlas/context";
import { TEXTBOOK_STAGES } from "../atlas/stages";
import { store } from "../store/store";

const LEVELS = [
  ["A2", "基础", "先从常用基础词开始"],
  ["B1", "基础", "从高中基础词开始"],
  ["B2", "核心", "覆盖大部分高中课本词汇"],
  ["C1", "挑战", "从较难的拓展词开始"],
];

export function Onboarding() {
  const atlas = useAtlas();
  const [mode, setMode] = useState<"textbook" | "cefr">("textbook");
  const [stage, setStage] = useState(0);
  const [level, setLevel] = useState(1);
  const [goal, setGoal] = useState(10);
  const finish = () =>
    store.settings({
      onboarded: true,
      startMode: mode,
      startStage: stage,
      startLevel: atlas.cefr.indexOf(LEVELS[level][0]),
      dailyNew: goal,
    });
  return (
    <div className="onboard" role="dialog" aria-modal="true" aria-label="欢迎">
      <div className="onboard-card">
        <img className="onboard-art" src={`${import.meta.env.BASE_URL}brand/hero.webp`} alt="" />
        <div className="onboard-body">
          <p className="eyebrow">欢迎来到达哥的高中词光小宇宙</p>
          <h1 className="display">
            {atlas.count.toLocaleString()} 颗星，
            <br />
            等你一颗颗点亮。
          </h1>
          <fieldset>
            <legend>你从哪里出发？</legend>
            <div className="choice-grid choice-grid-stages">
              {TEXTBOOK_STAGES.map((item, i) => (
                <button key={item.key} className={`choice ${mode === "textbook" && stage === i ? "is-on" : ""}`} onClick={() => { setMode("textbook"); setStage(i); }} aria-pressed={mode === "textbook" && stage === i}>
                  <span className="chip chip-book">教材</span>
                  <b>{item.short}</b>
                  <small>{item.count} 个首次出现词</small>
                </button>
              ))}
              <button className={`choice ${mode === "cefr" ? "is-on" : ""}`} onClick={() => setMode("cefr")} aria-pressed={mode === "cefr"}>
                <span className="chip chip-level lv-B1">A2–C1</span>
                <b>能力分级</b>
                <small>按词汇难度选择起点</small>
              </button>
            </div>
            {mode === "cefr" && (
              <div className="choice-grid level-subgrid">
                {LEVELS.map(([code, name, desc], i) => (
                  <button key={code} className={`choice ${level === i ? "is-on" : ""}`} onClick={() => setLevel(i)} aria-pressed={level === i}>
                    <span className={`chip chip-level lv-${code}`}>{code}</span>
                    <b>{name}</b>
                    <small>{desc}</small>
                  </button>
                ))}
              </div>
            )}
          </fieldset>
          <fieldset>
            <legend>每天点亮几颗新星？</legend>
            <div className="segmented segmented-wide daily-goal-grid">
              {[5, 10, 15, 20, 30, 50, 100].map((n) => (
                <button key={n} className={goal === n ? "is-on" : ""} onClick={() => setGoal(n)} aria-pressed={goal === n}>
                  {n} 颗{n === 10 ? " · 推荐" : ""}
                </button>
              ))}
            </div>
          </fieldset>
          <button className="btn btn-primary btn-xl" onClick={finish}>
            出发 <ArrowRight size={20} />
          </button>
          <p className="muted">不用注册。进度只留在这台设备上，随时可以在「我的」里修改。</p>
        </div>
      </div>
    </div>
  );
}
