import { useEffect, useState } from "react";

// Interpolates the ice -> ember palette by score, used for the needle,
// glow and arc so color is always paired with the numeric/text feedback
// (never color alone) per accessibility requirements.
function heatColor(score) {
  const ice = [90, 169, 230];
  const ember = [255, 107, 53];
  const t = Math.min(1, Math.max(0, score / 100));
  const rgb = ice.map((c, i) => Math.round(c + (ember[i] - c) * t));
  return `rgb(${rgb.join(",")})`;
}

export default function ScoreGauge({ score, feedback, loading }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    // animate toward the new score rather than jumping
    let raf;
    const start = display;
    const startTime = performance.now();
    const duration = 500;
    function tick(now) {
      const t = Math.min(1, (now - startTime) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(Math.round(start + (score - start) * eased));
      if (t < 1) raf = requestAnimationFrame(tick);
    }
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [score]);

  const color = heatColor(display);
  const angle = -120 + (display / 100) * 240; // needle sweep, -120deg..120deg
  const circumference = 2 * Math.PI * 80;
  const arcOffset = circumference * (1 - display / 100);

  return (
    <div className="relative flex flex-col items-center contour-field rounded-3xl py-6 px-4">
      <div className="relative w-40 h-40 sm:w-56 sm:h-56">
        <svg viewBox="0 0 200 200" className="w-full h-full -rotate-90">
          <circle cx="100" cy="100" r="80" fill="none" stroke="#2a3244" strokeWidth="10" />
          <circle
            cx="100"
            cy="100"
            r="80"
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={arcOffset}
            style={{ transition: "stroke-dashoffset 80ms linear, stroke 80ms linear" }}
          />
          <span
            className="font-mono text-4xl sm:text-5xl font-bold tabular-nums"
            style={{ color }}
            aria-live="polite"
          >
            {loading ? "···" : `${display}%`}
          </span>
            transition: "transform 80ms linear, background 80ms linear",
        <p className="mt-4 text-base sm:text-lg" aria-live="polite">
          {loading ? "Checking your guess…" : feedback}
        </p>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="font-mono text-5xl font-bold tabular-nums"
            style={{ color }}
            aria-live="polite"
          >
            {loading ? "···" : `${display}%`}
          </span>
        </div>
      </div>
      <p className="mt-4 text-lg" aria-live="polite">
        {loading ? "Checking your guess…" : feedback}
      </p>
    </div>
  );
}
