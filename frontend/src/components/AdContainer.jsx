// Provider-agnostic ad slot. Swap the placeholder body for a real network's
// snippet (e.g. AdSense) later — nothing else in the app should need to
// change since every placement renders through this one component.
export default function AdContainer({ placement = "banner", className = "" }) {
  const sizing = {
    banner: "h-24",
    inline: "h-20",
    footer: "h-16",
  };

  return (
    <div
      role="complementary"
      aria-label="Advertisement"
      className={`${sizing[placement] || sizing.banner} border border-dashed border-chartline
                  rounded-xl flex items-center justify-center text-muted text-xs
                  uppercase tracking-widest ${className}`}
    >
      Advertisement
    </div>
  );
}
