import { useEffect, useRef, useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import Message from "./components/Message.jsx";
import Composer from "./components/Composer.jsx";
import { streamAnswer } from "./lib/api.js";
import * as store from "./lib/storage.js";

const SUGGESTIONS = [
  "Quelle est la durée du congé de maternité ?",
  "Comment est calculée l'indemnité de licenciement ?",
  "Un employeur peut-il licencier une salariée enceinte ?",
  "À quel âge minimum peut-on travailler ?",
];

// How close to the bottom (px) counts as "still following" the conversation.
const STICK_THRESHOLD = 100;
const SIDEBAR_MIN = 220;
const SIDEBAR_MAX = 440;

export default function App() {
  const [conversations, setConversations] = useState(() => store.listConversations());
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarSearch, setSidebarSearch] = useState("");

  const uiPrefs = store.loadUiPrefs();
  const [sidebarWidth, setSidebarWidth] = useState(uiPrefs.sidebarWidth || 280);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(uiPrefs.sidebarCollapsed || false);

  const scrollRef = useRef(null);
  const stickToBottom = useRef(true); // false once the user scrolls away manually
  const cancelRef = useRef(null);
  const resizing = useRef(false);

  useEffect(() => {
    store.saveUiPrefs({ sidebarWidth, sidebarCollapsed });
  }, [sidebarWidth, sidebarCollapsed]);

  // Drag-to-resize the sidebar, like VS Code's panel border.
  useEffect(() => {
    function onMove(e) {
      if (!resizing.current) return;
      setSidebarWidth(Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, e.clientX)));
    }
    function onUp() {
      if (!resizing.current) return;
      resizing.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    }
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, []);

  function startResize() {
    resizing.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }

  // Auto-follow new content ONLY while the user hasn't scrolled up to read
  // something earlier -- previously this ran unconditionally on every token,
  // which yanked the view back down and made scrolling up impossible mid-answer.
  useEffect(() => {
    if (stickToBottom.current && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  function handleScroll() {
    const el = scrollRef.current;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    stickToBottom.current = distanceFromBottom < STICK_THRESHOLD;
  }

  function refreshConversations() {
    setConversations(store.listConversations());
  }

  function startNewChat() {
    setActiveId(null);
    setMessages([]);
    setSidebarOpen(false);
  }

  function selectConversation(id) {
    const conv = store.listConversations().find((c) => c.id === id);
    if (!conv) return;
    setActiveId(id);
    setMessages(conv.messages);
    setSidebarOpen(false);
    stickToBottom.current = true;
  }

  function removeConversation(id) {
    store.deleteConversation(id);
    if (id === activeId) startNewChat();
    refreshConversations();
  }

  async function ask(question) {
    if (!question.trim() || streaming) return;
    setInput("");
    setStreaming(true);
    stickToBottom.current = true; // sending always jumps to the new exchange

    let convId = activeId;
    if (!convId) {
      const conv = store.createConversation();
      convId = conv.id;
      setActiveId(convId);
    }

    const withUser = [...messages, { role: "user", content: question }];
    const withBot = [...withUser, { role: "bot", content: "", streaming: true, sources: [] }];
    setMessages(withBot);

    let finalContent = "";

    const { promise, cancel } = streamAnswer(question, {
      onDelta: (text) => {
        finalContent += text;
        setMessages((prev) => {
          const next = [...prev];
          next[next.length - 1] = { ...next[next.length - 1], content: finalContent };
          return next;
        });
      },
      onDone: (data) => {
        setMessages((prev) => {
          const next = [...prev];
          next[next.length - 1] = {
            ...next[next.length - 1],
            streaming: false,
            sources: data.sources || [],
            disclaimer: data.disclaimer,
          };
          persist(convId, withUser, next);
          return next;
        });
        setStreaming(false);
        cancelRef.current = null;
      },
      onError: (message) => {
        setMessages((prev) => {
          const next = [...prev];
          next[next.length - 1] = { ...next[next.length - 1], streaming: false, error: message };
          persist(convId, withUser, next);
          return next;
        });
        setStreaming(false);
        cancelRef.current = null;
      },
    });

    cancelRef.current = cancel;
    await promise;
  }

  function stopGeneration() {
    cancelRef.current?.();
    cancelRef.current = null;
    setStreaming(false);
    setMessages((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      if (last && last.role === "bot" && last.streaming) {
        next[next.length - 1] = { ...last, streaming: false, cancelled: true };
      }
      return next;
    });
  }

  function persist(convId, withUser, finalMessages) {
    const title = withUser.length ? store.titleFrom(withUser[0].content) : null;
    store.saveConversation({ id: convId, title, messages: finalMessages });
    refreshConversations();
  }

  const showEmptyState = messages.length === 0;

  return (
    <div className="app">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={selectConversation}
        onNew={startNewChat}
        onDelete={removeConversation}
        open={sidebarOpen}
        width={sidebarWidth}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed((v) => !v)}
        onStartResize={startResize}
        searchQuery={sidebarSearch}
        onSearchChange={setSidebarSearch}
      />
      {sidebarOpen && <div className="scrim" onClick={() => setSidebarOpen(false)} />}

      <div className="main-col">
        <header>
          <button className="menu-btn" onClick={() => setSidebarOpen((v) => !v)} aria-label="Menu">
            ☰
          </button>
          <div className="brand">
            <span className="logo">⚖️</span>
            <div>
              Assistant Juridique
              <small>Code du travail marocain · 100 % local</small>
            </div>
          </div>
          <div style={{ width: 34 }} />
        </header>

        <main ref={scrollRef} onScroll={handleScroll}>
          {showEmptyState ? (
            <div className="empty">
              <h1 className="hero">Bonjour</h1>
              <p className="hero-sub">Posez votre question sur le Code du travail.</p>
              <div className="chips">
                {SUGGESTIONS.map((q) => (
                  <button key={q} className="chip-suggest" onClick={() => ask(q)}>
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="messages">
              {messages.map((m, i) => (
                <Message key={i} role={m.role} {...m} />
              ))}
            </div>
          )}
        </main>

        <footer>
          <Composer
            value={input}
            onChange={setInput}
            onSubmit={() => ask(input)}
            onStop={stopGeneration}
            streaming={streaming}
          />
          <p className="foot-note">
            Réponses informatives fondées sur les textes cités. Ne remplacent pas l'avis d'un professionnel du droit.
          </p>
        </footer>
      </div>
    </div>
  );
}
