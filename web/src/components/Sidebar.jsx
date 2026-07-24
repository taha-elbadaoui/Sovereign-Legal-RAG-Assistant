// Strips accents so "indemnite" matches "indemnité" -- French search queries
// are often typed without diacritics, especially in a hurry.
function foldAccents(text) {
  return text.normalize("NFD").replace(/[̀-ͯ]/g, "");
}

export default function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
  open,
  width,
  collapsed,
  onToggleCollapse,
  onStartResize,
  searchQuery,
  onSearchChange,
}) {
  const q = foldAccents(searchQuery.trim().toLowerCase());
  const filtered = q
    ? conversations.filter((c) => foldAccents((c.title || "").toLowerCase()).includes(q))
    : conversations;

  return (
    <>
      <aside
        className={`sidebar ${open ? "open" : ""} ${collapsed ? "collapsed" : ""}`}
        style={{ width: collapsed ? 0 : width }}
      >
        <div className="sidebar-top">
          <button className="collapse-btn" onClick={onToggleCollapse} title="Réduire la barre latérale">
            ⟨
          </button>
          <button className="new-chat" onClick={onNew}>
            <span className="plus">＋</span> Nouvelle conversation
          </button>
        </div>

        <div className="search-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Rechercher une conversation…"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            onKeyDown={(e) => e.key === "Escape" && onSearchChange("")}
          />
          {searchQuery && (
            <button
              type="button"
              className="search-clear"
              onClick={() => onSearchChange("")}
              title="Effacer la recherche"
            >
              ✕
            </button>
          )}
        </div>

        <div className="conv-list">
          {filtered.length === 0 && (
            <p className="conv-empty">
              {q ? "Aucune conversation trouvée." : "Vos conversations apparaîtront ici."}
            </p>
          )}
          {filtered.map((c) => (
            <div key={c.id} className={`conv-item ${c.id === activeId ? "active" : ""}`}>
              <button className="conv-title" onClick={() => onSelect(c.id)}>
                {c.title || "Nouvelle conversation"}
              </button>
              <button
                className="conv-delete"
                title="Supprimer"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(c.id);
                }}
              >
                ✕
              </button>
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          <span className="dot" /> 100 % local · Code du travail (Loi 65‑99)
        </div>

        <div className="resize-handle" onMouseDown={onStartResize} />
      </aside>

      {collapsed && (
        <button className="expand-btn" onClick={onToggleCollapse} title="Afficher la barre latérale">
          ⟩
        </button>
      )}
    </>
  );
}
