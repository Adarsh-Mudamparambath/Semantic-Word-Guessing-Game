import { useEffect, useState, useCallback } from "react";
import Header from "./components/Header.jsx";
import ScoreGauge from "./components/ScoreGauge.jsx";
import GuessInput from "./components/GuessInput.jsx";
import GuessHistory from "./components/GuessHistory.jsx";
import WinScreen from "./components/WinScreen.jsx";
import AdContainer from "./components/AdContainer.jsx";
import HelpModal from "./components/HelpModal.jsx";
import AdRevealModal from "./components/AdRevealModal.jsx";
import PrivacyPage from "./components/PrivacyPage.jsx";
import { getToday, submitGuess, getHistory, revealSecretWord, startNextRound } from "./api.js";

export default function App() {
  if (window.location.pathname === "/privacy") return <PrivacyPage />;

  const [game, setGame] = useState(null); // { game_id, date }
  const [guesses, setGuesses] = useState([]); // newest first
  const [current, setCurrent] = useState({ score: 0, feedback: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showHelp, setShowHelp] = useState(false);
  const [showWin, setShowWin] = useState(false);
  const [showAdReveal, setShowAdReveal] = useState(false);
  const [revealedWord, setRevealedWord] = useState("");
  const [initLoading, setInitLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const today = await getToday();
        setGame(today);
        const history = await getHistory(today.game_id);
        const ordered = [...history.guesses]
          .sort((a, b) => b.score - a.score)
          .map((g) => ({ ...g }));
        setGuesses(ordered);
        if (ordered.length > 0) {
          setCurrent({ score: ordered[0].score, feedback: "" });
        }
        if (history.solved) setShowWin(true);
      } catch (e) {
        setError("Couldn't load today's challenge. Please refresh.");
      } finally {
        setInitLoading(false);
      }
    })();
  }, []);

  const handleGuess = useCallback(
    async (word) => {
      if (!game) return;
      // recognize duplicate on the frontend too — no need to hit the network
      // spinner state for a guess we already have
      const existing = guesses.find(
        (g) => g.guess.trim().toLowerCase() === word.trim().toLowerCase()
      );
      setError("");
      setLoading(true);
      try {
        const result = existing || (await submitGuess(game.game_id, word));
        setCurrent({ score: result.score, feedback: result.feedback || "" });
        if (!existing) {
          setGuesses((prev) => [
            { guess: result.guess, score: result.score, is_correct: result.is_correct },
            ...prev,
          ].sort((a, b) => b.score - a.score));
        }
        if (result.is_correct) setShowWin(true);
      } catch (e) {
        setError(e.message || "Something went wrong. Try again.");
      } finally {
        setLoading(false);
      }
    },
    [game, guesses]
  );

  const bestScore = guesses.reduce((max, g) => Math.max(max, g.score), 0);
  const solvedGuess = guesses.find((g) => g.is_correct);

  const resetRound = useCallback(async () => {
    setLoading(true);
    try {
      const nextGame = await startNextRound();
      const history = await getHistory(nextGame.game_id);
      setGame(nextGame);
      setGuesses([]);
      setCurrent({ score: 0, feedback: "" });
      setShowWin(false);
      setShowAdReveal(false);
      setRevealedWord("");
      setError("");
      if (history.solved) {
        setShowWin(true);
      }
    } catch (e) {
      setError("Couldn't start the next word. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleRevealAd = useCallback(async () => {
    if (!game) return;
    setError("");
    setLoading(true);
    try {
      const result = await revealSecretWord(game.game_id);
      setRevealedWord(result.secret_word);
      setShowAdReveal(true);
    } catch (e) {
      setError("Ad reveal failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [game]);

  return (
    <div className="min-h-screen flex flex-col">
      <div className="max-w-2xl mx-auto w-full px-4 flex-1 flex flex-col">
        <Header onToggleHelp={() => setShowHelp(true)} />

        <AdContainer placement="banner" className="mb-6" />

        <main className="flex-1 flex flex-col gap-6 pb-10">
          <section className="text-center">
            <h1 className="font-display text-3xl mb-1">Today's word</h1>
            <p className="text-muted text-sm">
              One word, hidden. Guess by meaning — spelling won't help you.
            </p>
          </section>

          {initLoading ? (
            <p className="text-center text-muted py-16">Loading today's challenge…</p>
          ) : (
            <>
              <ScoreGauge score={current.score} feedback={current.feedback} loading={loading} />

              <div className="flex gap-3">
                <GuessInput onSubmit={handleGuess} disabled={loading || !game} error={error} />
                <button
                  type="button"
                  onClick={handleRevealAd}
                  disabled={loading || !game}
                  className="px-4 py-3 rounded-xl border border-ember text-ember hover:bg-ember/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Reveal answer
                </button>
              </div>

              <AdContainer placement="inline" />

              <GuessHistory guesses={guesses} bestScore={bestScore} />
            </>
          )}
        </main>

        <AdContainer placement="footer" className="mb-4" />

        <footer className="text-center text-xs text-muted py-4 border-t border-chartline">
          {import.meta.env.VITE_APP_TITLE ?? "Meridian"} — a new word to chart every day.
          <a className="underline hover:text-parchment" href="/privacy">Privacy</a>
        </footer>
      </div>

      {showHelp && <HelpModal onClose={() => setShowHelp(false)} />}
      {showAdReveal && revealedWord && (
        <AdRevealModal
          secretWord={revealedWord}
          onContinue={resetRound}
          onClose={() => {
            setShowAdReveal(false);
            setRevealedWord("");
          }}
        />
      )}
      {showWin && solvedGuess && game && (
        <WinScreen
          secretWord={solvedGuess.guess}
          guesses={[...guesses].reverse()}
          dateStr={game.date}
          onClose={() => setShowWin(false)}
          onNextRound={resetRound}
        />
      )}
    </div>
  );
}
