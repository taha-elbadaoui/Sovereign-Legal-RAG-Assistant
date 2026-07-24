// Minimal markdown renderer (bold, italic, code, lists, paragraphs) plus
// article-citation highlighting. Deliberately hand-rolled instead of a
// markdown dependency: the surface we need is tiny and this keeps the LLM's
// raw text fully escaped before any markup is applied, so nothing it
// generates can ever inject real HTML.

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function toHtml(text) {
  let s = escapeHtml(text);
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>");

  const lines = s.split("\n");
  let html = "";
  let ul = false;
  let ol = false;
  const closeLists = () => {
    if (ul) { html += "</ul>"; ul = false; }
    if (ol) { html += "</ol>"; ol = false; }
  };

  for (const line of lines) {
    const t = line.trim();
    if (!t) { closeLists(); continue; }
    const bullet = t.match(/^[-*•]\s+(.*)/);
    const numbered = t.match(/^\d+[.)]\s+(.*)/);
    if (bullet) {
      if (!ul) { closeLists(); html += "<ul>"; ul = true; }
      html += `<li>${bullet[1]}</li>`;
    } else if (numbered) {
      if (!ol) { closeLists(); html += "<ol>"; ol = true; }
      html += `<li>${numbered[1]}</li>`;
    } else {
      closeLists();
      html += `<p>${t}</p>`;
    }
  }
  closeLists();

  return html.replace(/\bArticles?\s+(\d{1,3})/g, (m) => `<span class="cite">${m}</span>`);
}

export function Markdown({ text }) {
  return <div dangerouslySetInnerHTML={{ __html: toHtml(text) }} />;
}
