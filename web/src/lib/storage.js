// Conversation history, persisted in the browser's localStorage.
//
// This is a local, single-user tool with no accounts/auth (per the project's
// sovereignty design: nothing leaves the machine, so there is no server-side
// user database to store history in either). localStorage is the honest fit:
// history really persists across reloads, scoped to this browser, with zero
// added server infrastructure.

const KEY = "assistant-juridique.conversations.v1";

function readAll() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function writeAll(conversations) {
  localStorage.setItem(KEY, JSON.stringify(conversations));
}

export function listConversations() {
  return readAll().sort((a, b) => b.updatedAt - a.updatedAt);
}

export function createConversation() {
  const conv = { id: crypto.randomUUID(), title: null, messages: [], updatedAt: Date.now() };
  writeAll([conv, ...readAll()]);
  return conv;
}

export function saveConversation(conv) {
  const all = readAll();
  const idx = all.findIndex((c) => c.id === conv.id);
  const updated = { ...conv, updatedAt: Date.now() };
  if (idx === -1) all.unshift(updated);
  else all[idx] = updated;
  writeAll(all);
}

export function deleteConversation(id) {
  writeAll(readAll().filter((c) => c.id !== id));
}

export function titleFrom(firstUserMessage) {
  const t = firstUserMessage.trim();
  return t.length > 48 ? t.slice(0, 48) + "…" : t;
}

// Sidebar layout prefs (width, collapsed) -- separate key from conversations
// so clearing one doesn't touch the other.
const UI_KEY = "assistant-juridique.ui.v1";

export function loadUiPrefs() {
  try {
    const raw = localStorage.getItem(UI_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

export function saveUiPrefs(prefs) {
  localStorage.setItem(UI_KEY, JSON.stringify(prefs));
}
