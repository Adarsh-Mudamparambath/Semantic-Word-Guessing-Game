import { useState } from "react";

export default function Header({ onToggleHelp }) {
  return (
    <header className="flex items-center justify-between py-5">
      <div className="flex items-baseline gap-2">
        <span className="font-display text-2xl tracking-tight">Meridian</span>
        <span className="hidden sm:inline text-xs text-muted font-mono uppercase tracking-widest">
          daily word chart
        </span>
      </div>
      <nav className="flex items-center gap-4 text-sm text-muted">
        <button
          onClick={onToggleHelp}
          className="hover:text-parchment transition-colors"
        >
          How to play
        </button>
      </nav>
    </header>
  );
}
