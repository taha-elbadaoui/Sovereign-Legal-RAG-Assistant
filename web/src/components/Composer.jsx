import { useEffect, useRef } from "react";

// Above this many "?" in the box, warn -- the retriever fetches one shared
// context for the whole message, so several unrelated questions in one send
// dilutes it across all of them instead of answering any single one well.
const MANY_QUESTIONS_THRESHOLD = 1;

export default function Composer({ value, onChange, onSubmit, onStop, streaming }) {
  const textareaRef = useRef(null);

  function autoResize() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }

  // Re-measure on every value change, not just typing. This is what makes it
  // shrink back down after sending: App.jsx clears `value` programmatically
  // (setInput("")), which doesn't touch the textarea's inline height style on
  // its own -- previously a large pasted question left the box stuck tall.
  useEffect(autoResize, [value]);

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!streaming) onSubmit();
    }
  }

  const questionMarks = (value.match(/\?/g) || []).length;
  const manyQuestions = questionMarks > MANY_QUESTIONS_THRESHOLD;

  return (
    <div className="composer-wrap">
      {manyQuestions && (
        <div className="multi-warning">
          <span>⚠</span> {questionMarks} questions détectées — pour de meilleurs résultats, posez-les une par une.
        </div>
      )}
      <form
        className="composer"
        onSubmit={(e) => {
          e.preventDefault();
          if (!streaming) onSubmit();
        }}
      >
        <textarea
          ref={textareaRef}
          rows={1}
          placeholder="Écrivez votre question (une à la fois)…"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          autoFocus
        />
        {streaming ? (
          <button type="button" className="stop-btn" onClick={onStop} title="Arrêter la génération">
            ■
          </button>
        ) : (
          <button type="submit" disabled={!value.trim()} title="Envoyer">
            ➤
          </button>
        )}
      </form>
    </div>
  );
}
