export default function HelpModal({ onClose }) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="help-title"
      className="fixed inset-0 bg-void/80 backdrop-blur-sm flex items-center justify-center p-4 z-50"
      onClick={onClose}
    >
      <div
        className="bg-chart border border-chartline rounded-3xl max-w-md w-full p-8"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="help-title" className="font-display text-2xl mb-4">
          How to play
        </h2>
        <ul className="space-y-3 text-sm text-muted">
          <li>There's one secret word, shared by everyone today.</li>
          <li>Guess any word. You'll see how close it is in spelling, not meaning.</li>
          <li>0% is unrelated, 100% is the exact word — everything between is a clue.</li>
          <li>Use the score to explore toward the answer. No guess limit.</li>
        </ul>
        <button
          onClick={onClose}
          className="mt-6 w-full py-3 rounded-xl bg-chartline hover:bg-chartline/70 transition-colors"
        >
          Got it
        </button>
      </div>
    </div>
  );
}
