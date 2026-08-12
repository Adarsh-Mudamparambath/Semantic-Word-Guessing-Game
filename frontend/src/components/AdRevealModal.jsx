import { useEffect, useState } from "react";

export default function AdRevealModal({ secretWord, onContinue, onClose }) {
  const [videoEnded, setVideoEnded] = useState(false);

  useEffect(() => {
    setVideoEnded(false);
  }, [secretWord]);

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 bg-void/80 backdrop-blur-sm flex items-center justify-center p-4 z-50"
    >
      <div className="bg-chart border border-chartline rounded-3xl max-w-md w-full p-6 text-center shadow-glow shadow-ember/20">
        <div className="mb-4 rounded-2xl border border-chartline bg-void/60 p-4 overflow-hidden">
          <p className="text-xs uppercase tracking-[0.2em] text-muted mb-2">Ad break</p>

          {!videoEnded ? (
            <video
              key={secretWord}
              src="/sea.mp4"
              autoPlay
              muted
              playsInline
              controls={false}
              className="aspect-video w-full rounded-xl object-cover bg-void"
              onEnded={() => setVideoEnded(true)}
            />
          ) : (
            <div className="aspect-video w-full rounded-xl bg-gradient-to-br from-ember/30 via-ice/20 to-chartline flex items-center justify-center text-parchment font-display text-lg">
              Ad complete
            </div>
          )}
        </div>

        {!videoEnded ? (
          <div className="text-center text-muted text-sm">
            Watch the demo ad to reveal the answer.
          </div>
        ) : (
          <>
            <h2 className="font-display text-xl text-muted">Answer revealed</h2>
            <p className="font-display text-4xl mt-2 mb-4 capitalize">{secretWord}</p>

            <div className="flex gap-3 mt-6">
              <button
                onClick={onContinue}
                className="flex-1 py-3 rounded-xl bg-ember text-void font-semibold hover:bg-embersoft transition-colors"
              >
                Next word
              </button>
              <button
                onClick={onClose}
                className="px-4 py-3 rounded-xl border border-chartline text-muted hover:text-parchment transition-colors"
              >
                Close
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
