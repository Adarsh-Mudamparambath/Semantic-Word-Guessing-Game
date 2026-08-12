function buildShareText(dateStr, guesses) {
  const emojiForScore = (s) => {
    if (s >= 100) return "🎉";
    if (s >= 95) return "🚨";
    if (s >= 90) return "🔥🔥";
    if (s >= 80) return "🔥🔥";
    if (s >= 60) return "🔥";
    if (s >= 40) return "🌱";
    if (s >= 20) return "🧊";
    return "❄️";
  };
  const lines = guesses.map((g) => `${emojiForScore(g.score)} ${g.score}%`);
  return `Meridian\n${dateStr}\n\n${guesses.length} guesses\n\n${lines.join("\n")}\n\nCan you chart it?`;
}

export default function WinScreen({ secretWord, guesses, dateStr, onClose }) {
  const shareText = buildShareText(dateStr, guesses);

  async function handleShare() {
    if (navigator.share) {
      try {
        await navigator.share({ text: shareText });
        return;
      } catch {
        /* user cancelled — fall through to clipboard */
      }
    }
    await navigator.clipboard.writeText(shareText);
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="win-title"
      className="fixed inset-0 bg-void/80 backdrop-blur-sm flex items-center justify-center p-4 z-50"
    >
      <div className="bg-chart border border-chartline rounded-3xl max-w-sm w-full p-8 text-center shadow-glow shadow-ember/20">
        <p className="text-4xl mb-2" aria-hidden="true">
          🎉
        </p>
        <h2 id="win-title" className="font-display text-xl text-muted">
          You found it
        </h2>
        <p className="font-display text-4xl mt-2 mb-4 capitalize">{secretWord}</p>
        <p className="font-mono text-ember text-2xl">100%</p>
        <p className="text-muted text-sm mt-4">
          Solved in {guesses.length} guess{guesses.length === 1 ? "" : "es"}
        </p>
        <div className="flex gap-3 mt-6">
          <button
            onClick={handleShare}
            className="flex-1 py-3 rounded-xl bg-ember text-void font-semibold hover:bg-embersoft transition-colors"
          >
            Share result
          </button>
          <button
            onClick={onClose}
            className="px-4 py-3 rounded-xl border border-chartline text-muted hover:text-parchment transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
