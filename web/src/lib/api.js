// Streams an answer from the Python backend (serve.py -> src/app.py -> Ollama).
// Real Server-Sent Events over the actual local LLM -- callbacks fire as
// tokens genuinely arrive from the model, not simulated client-side.
//
// Returns { promise, cancel } instead of a bare promise so the caller can
// abort mid-stream (Stop button). Aborting closes the fetch, which the
// backend detects on its next write and stops calling the model further.
export function streamAnswer(question, { onDelta, onDone, onError }) {
  const controller = new AbortController();

  const promise = (async () => {
    let res;
    try {
      res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
        signal: controller.signal,
      });
    } catch (err) {
      if (err.name === "AbortError") return;
      onError("Impossible de contacter le serveur local.");
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const blocks = buffer.split("\n\n");
        buffer = blocks.pop();

        for (const block of blocks) {
          const eventMatch = block.match(/event: (.*)/);
          const dataMatch = block.match(/data: (.*)/s);
          if (!dataMatch) continue;
          const event = eventMatch ? eventMatch[1] : "message";
          const data = JSON.parse(dataMatch[1]);

          if (event === "delta") onDelta(data.text);
          else if (event === "done") onDone(data);
          else if (event === "error") onError(data.message);
        }
      }
    } catch (err) {
      if (err.name !== "AbortError") onError("Connexion interrompue.");
    }
  })();

  return { promise, cancel: () => controller.abort() };
}
