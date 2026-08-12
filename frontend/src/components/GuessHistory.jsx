function heatColor(score) {
  const ice = [90, 169, 230];
  const ember = [255, 107, 53];
  const t = Math.min(1, Math.max(0, score / 100));
  const rgb = ice.map((c, i) => Math.round(c + (ember[i] - c) * t));
  return `rgb(${rgb.join(",")})`;
}

export default function GuessHistory({ guesses, bestScore }) {
  if (guesses.length === 0) {
    return (
      <div className="text-muted text-sm py-8 text-center border border-dashed border-chartline rounded-2xl">
        Your guesses will chart here as you explore.
      </div>
    );
  }

  const strongestFirst = [...guesses].sort((a, b) => b.score - a.score);

  return (
    <div>
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="font-display text-lg">Your guesses</h2>
        <span className="text-sm text-muted font-mono">
          best <span className="text-parchment">{bestScore}%</span>
        </span>
      </div>
      <ol className="space-y-1.5" aria-label="Guess history by score">
        {strongestFirst.map((g, i) => {
          const color = heatColor(g.score);
          return (
            <li
              key={`${g.guess}-${i}`}
              className={`flex items-center gap-3 rounded-lg px-4 py-2.5 border transition-colors ${
                g.is_correct
                  ? "border-ember bg-ember/10"
                  : i === 0
                  ? "border-ice bg-ice/10"
                  : "border-chartline bg-chart"
              }`}
            >
              <span className="text-xs font-mono text-muted w-8">#{i + 1}</span>
              <span className="flex-1 font-medium capitalize">{g.guess}</span>
              {g.is_correct && <span aria-hidden="true">🎉</span>}
              <span className="font-mono tabular-nums" style={{ color }}>
                {g.score}%
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
