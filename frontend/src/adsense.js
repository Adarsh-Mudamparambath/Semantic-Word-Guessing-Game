const publisherId = import.meta.env.VITE_ADSENSE_CLIENT?.trim();

export const adSlots = {
  banner: import.meta.env.VITE_ADSENSE_SLOT_BANNER?.trim(),
  inline: import.meta.env.VITE_ADSENSE_SLOT_INLINE?.trim(),
  footer: import.meta.env.VITE_ADSENSE_SLOT_FOOTER?.trim(),
};

export function isAdSenseConfigured(slot) {
  return Boolean(publisherId && slot);
}

export function getPublisherId() {
  return publisherId;
}

export function loadAdSense() {
  if (!publisherId || document.querySelector("script[data-adsense-loader]")) return;

  const script = document.createElement("script");
  script.async = true;
  script.crossOrigin = "anonymous";
  script.dataset.adsenseLoader = "true";
  script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${encodeURIComponent(publisherId)}`;
  document.head.appendChild(script);
}
