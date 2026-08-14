import { useState } from "react";

export default function Header({ onToggleHelp }) {
  const title = import.meta.env.VITE_APP_TITLE ?? "Meridian";
  return (
    <header className="flex flex-col sm:flex-row items-center justify-between py-5 gap-3">
      <div className="flex items-baseline gap-2">
        <span className="font-display text-2xl sm:text-3xl tracking-tight">{title}</span>
        <span className="hidden sm:inline text-xs text-muted font-mono uppercase tracking-widest">
          daily word chart
        </span>
      </div>
      <nav className="mt-1 sm:mt-0 flex items-center gap-4 text-sm text-muted">
        <button onClick={onToggleHelp} className="hover:text-parchment transition-colors">
          How to play
        </button>
      </nav>
    </header>
  );
}
