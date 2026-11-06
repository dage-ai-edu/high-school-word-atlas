import { useEffect, useRef } from "react";

const PALETTE: [string, number][] = [
  ["243,236,223", 0.58],
  ["230,180,87", 0.16],
  ["229,124,90", 0.12],
  ["151,184,142", 0.08],
  ["143,178,204", 0.06],
];

interface Particle {
  x: number;
  y: number;
  sx: number;
  sy: number;
  tx: number;
  ty: number;
  color: string;
  radius: number;
  delay: number;
  alpha: number;
  twinkle: number;
}

const ease = (value: number) => 1 - Math.pow(1 - Math.min(1, Math.max(0, value)), 3);

function sampleTargets(width: number, height: number, count: number) {
  const source = document.createElement("canvas");
  source.width = width;
  source.height = height;
  const context = source.getContext("2d")!;
  const size = Math.min(width, height);
  const centerX = width / 2;
  const logoRadius = size * 0.1;
  const centerY = height * 0.15;

  context.fillStyle = context.strokeStyle = "#fff";
  context.lineWidth = Math.max(2, size * 0.006);
  context.beginPath();
  context.arc(centerX, centerY, logoRadius, 0, Math.PI * 2);
  context.stroke();
  context.beginPath();
  context.moveTo(centerX, centerY - logoRadius * 0.9);
  context.lineTo(centerX + logoRadius * 0.3, centerY);
  context.lineTo(centerX, centerY + logoRadius * 0.9);
  context.lineTo(centerX - logoRadius * 0.3, centerY);
  context.closePath();
  context.fill();
  context.beginPath();
  context.moveTo(centerX - logoRadius * 0.62, centerY);
  context.lineTo(centerX, centerY - logoRadius * 0.1);
  context.lineTo(centerX + logoRadius * 0.62, centerY);
  context.lineTo(centerX, centerY + logoRadius * 0.1);
  context.closePath();
  context.fill();

  const chineseSize = Math.min(width * 0.42, height * 0.46);
  context.font = `700 ${chineseSize}px "Songti SC", "STSong", "Noto Serif SC", serif`;
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillText("达哥", centerX, height * 0.53);
  const englishSize = Math.max(18, chineseSize * 0.18);
  context.font = `700 ${englishSize}px "Fraunces Variable", Georgia, serif`;
  context.letterSpacing = `${englishSize * 0.34}px`;
  context.fillText("DAGE", centerX, height * 0.83);

  const pixels = context.getImageData(0, 0, width, height).data;
  const lit: [number, number][] = [];
  for (let y = 0; y < height; y += 2) {
    for (let x = 0; x < width; x += 2) {
      if (pixels[(y * width + x) * 4 + 3] > 120) lit.push([x, y]);
    }
  }
  return Array.from({ length: count }, () => lit[Math.floor(Math.random() * lit.length)] ?? [centerX, centerY]);
}

export function DageParticleHero() {
  const canvas = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const element = canvas.current;
    if (!element) return;
    let animationFrame = 0;

    const render = () => {
      cancelAnimationFrame(animationFrame);
      const rect = element.getBoundingClientRect();
      const width = Math.max(1, Math.round(rect.width));
      const height = Math.max(1, Math.round(rect.height));
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      element.width = width * dpr;
      element.height = height * dpr;
      const context = element.getContext("2d")!;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = width < 700 ? 4200 : 7600;
      const targets = sampleTargets(width, height, count);
      const pickColor = () => {
        let random = Math.random();
        for (const [color, probability] of PALETTE) if ((random -= probability) <= 0) return color;
        return PALETTE[0][0];
      };
      const wordTop = height * 0.7;
      const particles: Particle[] = targets.map(([targetX, targetY]) => {
        const startX = -0.1 * width + Math.random() * 1.2 * width;
        const startY = -0.1 * height + Math.random() * 1.2 * height;
        return {
          x: startX,
          y: startY,
          sx: startX,
          sy: startY,
          tx: targetX + (Math.random() - 0.5) * 1.2,
          ty: targetY + (Math.random() - 0.5) * 1.2,
          color: pickColor(),
          radius: targetY < wordTop && Math.random() < 0.025 ? 1.8 + Math.random() : 0.7 + Math.random() * 1.1,
          delay: Math.random() * 0.55,
          alpha: 0.55 + Math.random() * 0.45,
          twinkle: Math.random() * Math.PI * 2,
        };
      });
      const stars = Array.from({ length: Math.round((width * height) / 9000) }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        radius: Math.random() * 0.9 + 0.2,
        twinkle: Math.random() * 6,
      }));
      const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
      const startedAt = performance.now();

      const frame = (now: number) => {
        const elapsed = reduced ? 3 : (now - startedAt) / 1000;
        context.clearRect(0, 0, width, height);
        context.globalCompositeOperation = "lighter";
        for (const star of stars) {
          context.fillStyle = `rgba(243,236,223,${0.15 + 0.25 * (0.5 + 0.5 * Math.sin(elapsed * 1.3 + star.twinkle))})`;
          context.fillRect(star.x, star.y, star.radius, star.radius);
        }
        for (const particle of particles) {
          const progress = ease((elapsed - 0.15 - particle.delay) / 1.7);
          const swirl = (1 - progress) * (90 + particle.twinkle * 12);
          const angle = (1 - progress) * 3.2 + particle.twinkle;
          particle.x = particle.sx + (particle.tx - particle.sx) * progress + Math.cos(angle) * swirl;
          particle.y = particle.sy + (particle.ty - particle.sy) * progress + Math.sin(angle) * swirl;
          if (progress >= 1) {
            particle.x += Math.sin(elapsed * 2 + particle.twinkle) * 0.35;
            particle.y += Math.cos(elapsed * 1.7 + particle.twinkle) * 0.35;
          }
          const alpha = particle.alpha * (0.75 + 0.25 * Math.sin(elapsed * 3 + particle.twinkle * 3));
          if (particle.radius > 2) {
            context.fillStyle = `rgba(${particle.color},${alpha * 0.12})`;
            context.beginPath();
            context.arc(particle.x, particle.y, particle.radius * 2.6, 0, Math.PI * 2);
            context.fill();
          }
          context.fillStyle = `rgba(${particle.color},${alpha})`;
          context.fillRect(particle.x - particle.radius / 2, particle.y - particle.radius / 2, particle.radius, particle.radius);
        }
        context.globalCompositeOperation = "source-over";
        if (!reduced) animationFrame = requestAnimationFrame(frame);
      };
      animationFrame = requestAnimationFrame(frame);
    };

    const observer = new ResizeObserver(render);
    observer.observe(element);
    render();
    return () => {
      observer.disconnect();
      cancelAnimationFrame(animationFrame);
    };
  }, []);

  return <canvas ref={canvas} className="dage-particle-stage" role="img" aria-label="暖色发光粒子聚合成达哥二字" />;
}
