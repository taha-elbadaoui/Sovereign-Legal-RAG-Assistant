import { useState } from "react";
import { Markdown } from "../lib/markdown.jsx";

function SourceChip({ source }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="source-block">
      <button className="src-chip" onClick={() => setOpen((v) => !v)}>
        <span className="dot">📄</span> Article {source.number}
      </button>
      {open && (
        <div className="src-card">
          {source.path && <div className="path">{source.path}</div>}
          <div className="num">Article {source.number}</div>
          <div>{source.text}</div>
        </div>
      )}
    </div>
  );
}

export default function Message({ role, content, sources, disclaimer, streaming, error, cancelled }) {
  if (role === "user") {
    return (
      <div className="msg user">
        <div className="bubble">{content}</div>
      </div>
    );
  }

  return (
    <div className="msg bot">
      <div className="avatar">⚖️</div>
      <div className="bot-body">
        {error ? (
          <p className="error-text">⚠ {error}</p>
        ) : (
          <>
            <Markdown text={content} />
            {streaming && <span className="cursor">▍</span>}
            {cancelled && <p className="cancelled-note">— Génération interrompue.</p>}
          </>
        )}

        {!streaming && !error && sources && sources.length > 0 && (
          <div className="sources">
            {sources.map((s) => (
              <SourceChip key={s.number} source={s} />
            ))}
          </div>
        )}

        {!streaming && !error && disclaimer && <div className="disclaimer">{disclaimer}</div>}
      </div>
    </div>
  );
}
