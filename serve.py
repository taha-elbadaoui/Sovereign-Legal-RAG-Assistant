"""Web server for the citizen-facing chat UI (React app in web/).

Thin layer over the existing RAG engine (src/app.py, retriever, generator):
serves the built React app (web/dist/, produced by `npm run build`) and
streams answers token by token over Server-Sent Events. The API side uses
only the Python standard library — nothing extra to install for the backend.

Setup (once):  cd web && npm install && npm run build
Run:           python serve.py   then open http://localhost:8000

For frontend development with hot-reload, run `npm run dev` in web/ instead
(it proxies /api to this server, so run both at once).
"""
import os
import sys
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Windows consoles default to cp1252 and crash on accented / symbol output.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from retriever import retrieve
from generator import generate_stream, DISCLAIMER, MODEL
from app import ABSTENTION_THRESHOLD, ABSTENTION_MESSAGE, cited_article_numbers

WEB_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "dist")
PORT = 8000


def hierarchy_path(article):
    parts = (article["livre"], article["titre"], article["chapitre"], article["section"])
    return " › ".join(p for p in parts if p)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Static files built by Vite (JS/CSS bundles, index.html, etc.).
        # Any unknown path falls back to index.html (single-page app).
        requested = self.path.split("?", 1)[0].lstrip("/") or "index.html"
        file_path = os.path.join(WEB_DIST, requested)
        if not os.path.isfile(file_path):
            file_path = os.path.join(WEB_DIST, "index.html")

        if not os.path.isfile(file_path):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<h1>Interface non compilee</h1><p>Run: cd web && npm install && npm run build</p>"
            )
            return

        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        with open(file_path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/ask":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or "{}")
        question = (payload.get("question") or "").strip()

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        # ConnectionAbortedError/BrokenPipeError happen when the browser cancels
        # (Stop button) or closes the tab mid-stream -- not a real failure.
        client_gone = False

        def sse(event, data):
            nonlocal client_gone
            if client_gone:
                return
            block = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            try:
                self.wfile.write(block.encode("utf-8"))
                self.wfile.flush()
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                client_gone = True

        if not question:
            sse("done", {"sources": [], "disclaimer": DISCLAIMER})
            return

        result = retrieve(question)
        articles = result["articles"]

        # Cheap out-of-scope gate: stream the refusal without calling the LLM.
        if result["top_similarity"] < ABSTENTION_THRESHOLD:
            for word in ABSTENTION_MESSAGE.split(" "):
                sse("delta", {"text": word + " "})
            sse("done", {"sources": [], "disclaimer": DISCLAIMER})
            return

        full = ""
        try:
            for piece in generate_stream(question, articles):
                if client_gone:
                    break  # stop pulling tokens from Ollama once nobody is listening
                full += piece
                sse("delta", {"text": piece})
        except Exception as exc:
            sse("error", {"message": f"Le modèle local ({MODEL}) est injoignable. "
                                     f"Vérifiez qu'Ollama est lancé. ({exc})"})
            return

        # Only surface sources the answer actually cited AND that were in context.
        cited = cited_article_numbers(full)
        by_number = {a["article_number"]: a for a in articles}
        sources = [
            {"number": n, "text": by_number[n]["article_text"], "path": hierarchy_path(by_number[n])}
            for n in sorted(cited, key=lambda x: int(x))
            if n in by_number
        ]
        sse("done", {"sources": sources, "disclaimer": DISCLAIMER})

    def log_message(self, *args):
        pass  # keep the console clean


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"\n  Assistant Juridique prêt  →  http://localhost:{PORT}")
    print(f"  Modèle : {MODEL}   ·   Ctrl+C pour arrêter\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur.")
