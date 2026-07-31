/**
 * Capture des captures d'ecran de l'interface web, pour le rapport.
 *
 * Pilote Chrome en mode headless via le Chrome DevTools Protocol. Aucune
 * dependance npm : Node 22+ expose WebSocket globalement.
 *
 * Prerequis : le serveur doit tourner (python serve.py) et Ollama doit servir
 * le modele, puisque les captures montrent de vraies reponses generees.
 *
 * Usage :  node eval/capture_ui.js
 * Sortie :  rapport/Figures/captures/*.png
 */
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const APP = "http://localhost:8000";
const PORT = 9333;
const OUT = path.join(__dirname, "..", "rapport", "Figures", "captures");
const PROFILE = path.join(require("node:os").tmpdir(), "ajs-capture-profile");

// Les trois situations que le rapport doit montrer : une reponse sourcee, le
// detail d'un article source, et une abstention.
const SCENES = [
  {
    nom: "01-reponse-citee",
    question: "Quelle est la durée du congé de maternité ?",
    apres: null,
  },
  {
    nom: "02-source-depliee",
    question: "Comment est calculée l'indemnité de licenciement ?",
    // Deplier la premiere puce d'article pour montrer le texte legal et le
    // chemin hierarchique complet.
    apres: `const c = [...document.querySelectorAll('button')]
              .find(b => /Article\\s+\\d+/.test(b.textContent));
            if (c) c.click();`,
  },
  {
    nom: "03-abstention",
    question: "Quelle est la recette du couscous royal ?",
    apres: null,
  },
];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function cdpTargets() {
  const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
  return res.json();
}

class Session {
  constructor(ws) {
    this.ws = ws;
    this.id = 0;
    this.pending = new Map();
    ws.addEventListener("message", (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
      }
    });
  }
  send(method, params = {}) {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
  }
  async evaluate(expression) {
    const r = await this.send("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
    });
    if (r.exceptionDetails) {
      const d = r.exceptionDetails;
      throw new Error(
        (d.exception && (d.exception.description || d.exception.value)) || d.text);
    }
    return r.result.value;
  }
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  fs.rmSync(PROFILE, { recursive: true, force: true });

  const chrome = spawn(CHROME, [
    "--headless=new",
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${PROFILE}`,
    "--hide-scrollbars",
    "--force-device-scale-factor=2",
    "--window-size=1280,880",
    "--no-first-run",
    "--no-default-browser-check",
    APP,
  ], { stdio: "ignore" });

  // Attendre que le port de debogage reponde
  let targets = null;
  for (let i = 0; i < 60 && !targets; i++) {
    try { targets = await cdpTargets(); } catch { await sleep(500); }
  }
  if (!targets) throw new Error("Chrome n'a pas ouvert le port de debogage");

  const page = targets.find((t) => t.type === "page" && t.url.includes("localhost:8000"))
            || targets.find((t) => t.type === "page");
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener("open", r, { once: true }));
  const s = new Session(ws);

  await s.send("Page.enable");
  await s.send("Runtime.enable");
  await s.send("Emulation.setDeviceMetricsOverride", {
    width: 1280, height: 880, deviceScaleFactor: 2, mobile: false,
  });

  // L'application React met un instant a se monter : attendre que la zone de
  // saisie existe avant toute interaction.
  const attendreInterface = async () => {
    for (let i = 0; i < 60; i++) {
      const pret = await s.evaluate(`!!document.querySelector('textarea')`);
      if (pret) return;
      await sleep(500);
    }
    throw new Error("l'interface ne s'est pas montee (aucune zone de saisie)");
  };
  await attendreInterface();

  for (const scene of SCENES) {
    console.log(`  ${scene.nom} : "${scene.question}"`);

    // Repartir d'une conversation vierge
    await s.evaluate(`
      (() => {
        const b = [...document.querySelectorAll('button')]
          .find(x => x.textContent.includes('Nouvelle conversation'));
        if (b) b.click();
      })()`);
    await sleep(600);
    await attendreInterface();

    // Poser la question dans la zone de saisie, puis soumettre
    await s.evaluate(`
      (() => {
        const ta = document.querySelector('textarea');
        const setter = Object.getOwnPropertyDescriptor(
          window.HTMLTextAreaElement.prototype, 'value').set;
        setter.call(ta, ${JSON.stringify(scene.question)});
        ta.dispatchEvent(new Event('input', { bubbles: true }));
      })()`);
    await sleep(300);
    await s.evaluate(`
      (() => {
        const ta = document.querySelector('textarea');
        const form = ta.closest('form');
        if (form) form.requestSubmit();
        else ta.dispatchEvent(new KeyboardEvent('keydown',
          { key: 'Enter', bubbles: true }));
      })()`);

    // Attendre la fin du streaming (le curseur ▍ disparait)
    let stable = 0, last = -1;
    for (let i = 0; i < 150; i++) {
      await sleep(1000);
      const state = await s.evaluate(`
        (() => {
          const t = document.querySelector('main').innerText;
          return JSON.stringify({ n: t.length, streaming: t.includes('▍') });
        })()`);
      const { n, streaming } = JSON.parse(state);
      if (!streaming && n === last) { if (++stable >= 2) break; } else { stable = 0; }
      last = n;
    }

    if (scene.apres) {
      await s.evaluate(`(() => { ${scene.apres} })()`);
      await sleep(900);
    }

    const shot = await s.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
    const file = path.join(OUT, `${scene.nom}.png`);
    fs.writeFileSync(file, Buffer.from(shot.data, "base64"));
    console.log(`     -> ${file} (${(fs.statSync(file).size / 1024).toFixed(0)} Ko)`);
  }

  ws.close();
  chrome.kill();
  console.log("captures terminees");
}

main().catch((e) => { console.error("ECHEC:", e.message); process.exit(1); });
