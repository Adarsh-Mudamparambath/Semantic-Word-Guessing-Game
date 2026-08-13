const appTitle = import.meta.env.VITE_APP_TITLE ?? "Meridian";
const contactEmail = import.meta.env.VITE_CONTACT_EMAIL;

export default function PrivacyPage() {
  return (
    <main className="max-w-2xl mx-auto min-h-screen px-6 py-12 text-muted leading-7">
      <a href="/" className="text-ice hover:text-parchment">&larr; Back to {appTitle}</a>
      <h1 className="font-display text-4xl text-parchment mt-8 mb-6">Privacy Policy</h1>
      <p>Last updated: August 14, 2026</p>
      <p className="mt-5">{appTitle} stores a session cookie so your game guesses can be remembered. We do not require an account or ask for personal profile information to play.</p>
      <h2 className="font-display text-2xl text-parchment mt-8 mb-3">Advertising</h2>
      <p>We use Google AdSense to show advertising. Google and its partners may use cookies or similar technologies to personalize ads, measure ad performance, and limit repeated ads. You can learn about Google&apos;s advertising technologies and controls at <a className="text-ice underline" href="https://policies.google.com/technologies/ads">Google&apos;s advertising policy</a>.</p>
      <h2 className="font-display text-2xl text-parchment mt-8 mb-3">Your choices</h2>
      <p>Where required, we will request consent before using advertising cookies. You can also control cookies through your browser settings and manage Google ad personalization through your Google account.</p>
      <h2 className="font-display text-2xl text-parchment mt-8 mb-3">Contact</h2>
      <p>{contactEmail ? <>For privacy questions, email <a className="text-ice underline" href={`mailto:${contactEmail}`}>{contactEmail}</a>.</> : "For privacy questions, contact the site operator using the contact address published on this website."}</p>
    </main>
  );
}
