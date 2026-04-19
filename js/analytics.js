// Lightweight analytics + owner-notification wrapper.
//
// Two channels:
//   1. PostHog — captures every event to the dashboard (history, funnels, charts).
//   2. Owner webhook — optional real-time ping (ntfy.sh, Discord, Slack) on select events.
//
// PostHog is loaded from the snippet injected in <head>, so `window.posthog` exists by the
// time this module runs in an event handler. If it doesn't (blocker, offline), calls no-op.

// ---- CONFIG --------------------------------------------------------------
// Webhook destination for real-time phone pings. Options:
//   - ntfy.sh: "https://ntfy.sh/<your-secret-topic>"  (POST with plain-text body)
//   - Discord: "https://discord.com/api/webhooks/<id>/<token>"  (POST JSON { content })
// Leave empty to disable the webhook channel (PostHog still runs).
const OWNER_WEBHOOK_URL = "https://discord.com/api/webhooks/1495175220636680373/5MaSvE6VsXFtbrRItJWuEDWYT6iLsV8cZvXg6nqpXbGaxb7P6_lluVUbDNEdIiOPSBvH";

// Which events trigger the owner webhook. PostHog receives everything regardless.
const WEBHOOK_EVENTS = new Set(["user_signed_in", "note_created", "like_added", "image_shared", "lens_search"]);
// -------------------------------------------------------------------------

export function identifyUser(user) {
  if (!user || !window.posthog) return;
  window.posthog.identify(user.uid, {
    name: user.displayName || "Anonymous",
    email: user.email || null,
  });
}

export function resetUser() {
  if (window.posthog) window.posthog.reset();
}

export function track(event, props = {}) {
  if (window.posthog) {
    try { window.posthog.capture(event, props); } catch {}
  }
  if (OWNER_WEBHOOK_URL && WEBHOOK_EVENTS.has(event)) {
    sendOwnerPing(event, props);
  }
}

function sendOwnerPing(event, props) {
  const line = formatPing(event, props);
  const isDiscord = OWNER_WEBHOOK_URL.includes("discord.com/api/webhooks");
  const body = isDiscord ? JSON.stringify({ content: line }) : line;
  const headers = isDiscord ? { "Content-Type": "application/json" } : { "Content-Type": "text/plain" };
  // keepalive so the request survives the page unload that often follows a share/sign-in.
  fetch(OWNER_WEBHOOK_URL, { method: "POST", headers, body, keepalive: true }).catch(() => {});
}

function formatPing(event, props) {
  const who = props.displayName || props.userId || "someone";
  const img = props.imageFile ? ` · ${props.imageFile}` : "";
  const extra = props.text ? ` · "${truncate(props.text, 140)}"` : "";
  const labels = {
    user_signed_in: "signed in",
    note_created: "left a note",
    like_added: "liked",
    like_removed: "unliked",
    image_shared: "shared",
    lens_search: "Google-Lens'd",
  };
  return `${who} ${labels[event] || event}${img}${extra}`;
}

function truncate(s, n) {
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}
