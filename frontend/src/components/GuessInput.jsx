import { useState } from "react";

export default function GuessInput({ onSubmit, disabled, error }) {
  const [value, setValue] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setValue("");
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <label htmlFor="guess-input" className="sr-only">
        Enter a word
      </label>
      <div className="flex gap-3">
        <input
          id="guess-input"
          type="text"
          autoComplete="off"
          autoCorrect="off"
          spellCheck="false"
          placeholder="Enter a word…"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={disabled}
          className="flex-1 bg-chart border border-chartline rounded-xl px-5 py-4 text-lg
                     placeholder:text-muted focus-visible:border-ice outline-none
                     disabled:opacity-50 transition-colors"
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="px-6 py-4 rounded-xl bg-ember text-void font-semibold
                     hover:bg-embersoft transition-colors disabled:opacity-40
                     disabled:cursor-not-allowed"
        >
          {disabled ? "Checking…" : "Guess"}
        </button>
      </div>
      {error && (
        <p role="alert" className="mt-2 text-sm text-embersoft">
          {error}
        </p>
      )}
    </form>
  );
}
