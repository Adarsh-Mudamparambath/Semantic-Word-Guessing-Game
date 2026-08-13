import { useEffect, useRef } from "react";
import { adSlots, getPublisherId, isAdSenseConfigured, loadAdSense } from "../adsense.js";

export default function AdContainer({ placement = "banner", className = "" }) {
  const adRef = useRef(null);
  const slot = adSlots[placement];
  const configured = isAdSenseConfigured(slot);
  const sizing = { banner: "h-24", inline: "h-20", footer: "h-16" };

  useEffect(() => {
    if (!configured || !adRef.current || adRef.current.dataset.loaded) return;

    loadAdSense();
    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
      adRef.current.dataset.loaded = "true";
    } catch {
      // Privacy tools may block the script; the game remains fully usable.
    }
  }, [configured, slot]);

  if (!configured) {
    return (
      <div
        role="complementary"
        aria-label="Advertisement"
        className={`${sizing[placement] || sizing.banner} border border-dashed border-chartline rounded-xl flex items-center justify-center text-muted text-xs uppercase tracking-widest ${className}`}
      >
        Advertisement
      </div>
    );
  }

  return (
    <div
      role="complementary"
      aria-label="Advertisement"
      className={`${sizing[placement] || sizing.banner} overflow-hidden ${className}`}
    >
      <ins
        ref={adRef}
        className="adsbygoogle block h-full w-full"
        style={{ display: "block" }}
        data-ad-client={getPublisherId()}
        data-ad-slot={slot}
        data-ad-format="auto"
        data-full-width-responsive="true"
      />
    </div>
  );
}
