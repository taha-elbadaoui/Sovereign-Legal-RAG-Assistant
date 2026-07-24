import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

st.set_page_config(page_title="Assistant Juridique — Code du travail", page_icon="⚖️", layout="centered")


@st.cache_resource(show_spinner="Chargement des modèles (au premier lancement : téléchargement)…")
def load_engine():
    from app import answer_question, ABSTENTION_THRESHOLD
    from generator import DISCLAIMER, MODEL
    return answer_question, DISCLAIMER, MODEL, ABSTENTION_THRESHOLD


answer_question, DISCLAIMER, MODEL, ABSTENTION_THRESHOLD = load_engine()

EXAMPLES = [
    "Quelle est la durée du congé de maternité ?",
    "À quel âge minimum un mineur peut-il travailler ?",
    "Comment est calculée l'indemnité de licenciement ?",
    "Un employeur peut-il licencier une salariée enceinte ?",
]

# --- Sidebar ---
with st.sidebar:
    st.header("⚖️ Assistant Juridique")
    st.caption("Code du travail marocain — Loi 65-99")
    st.markdown(
        "Recherche augmentée (**RAG**) **100 % locale** : le corpus, la recherche "
        "et le modèle tournent sur la machine. Aucune question ne quitte le territoire."
    )
    st.divider()
    st.subheader("Paramètres")
    k = st.slider("Articles récupérés", min_value=3, max_value=10, value=5)
    rerank = st.toggle("Reranking (cross-encodeur)", value=False,
                       help="Plus précis, mais télécharge un modèle (~2.3 Go) au premier usage.")
    st.divider()
    st.caption(f"Modèle : `{MODEL}` · Embeddings : `BGE-M3` · Base : `Chroma`")
    if st.button("🗑️ Effacer la conversation"):
        st.session_state.messages = []
        st.rerun()

st.title("Assistant Juridique Marocain")
st.caption("Posez une question sur le Code du travail. Chaque réponse cite ses articles sources.")


def render_extras(result):
    """Render sources, citation check and disclaimer under an assistant message."""
    if result.get("error"):
        return
    if result["unverified"]:
        st.warning(
            "⚠️ Citations non vérifiées (absentes du contexte fourni) : "
            + ", ".join(f"Article {n}" for n in sorted(result["unverified"]))
        )
    if not result["abstained"] and result["sources"]:
        with st.expander(f"📚 Articles retrouvés ({len(result['sources'])})"):
            for a in result["sources"]:
                path = " › ".join(p for p in (a["livre"], a["titre"], a["chapitre"], a["section"]) if p)
                cited = a["article_number"] in result["cited"]
                st.markdown(f"**Article {a['article_number']}**{' ✅ cité' if cited else ''}")
                if path:
                    st.caption(path)
                st.write(a["article_text"])
                st.divider()
    st.caption(DISCLAIMER)


if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant" and m.get("result"):
            render_extras(m["result"])

# Example prompts (only before the first exchange, to keep it clean)
pending = None
if not st.session_state.messages:
    st.write("**Exemples :**")
    cols = st.columns(2)
    for i, example in enumerate(EXAMPLES):
        if cols[i % 2].button(example, use_container_width=True):
            pending = example

prompt = st.chat_input("Votre question…") or pending

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Recherche dans le corpus et génération…"):
            result = answer_question(prompt, k=k, rerank=rerank)
        content = result["error"] or result["answer"]
        st.markdown(content)
        render_extras(result)

    st.session_state.messages.append({"role": "assistant", "content": content, "result": result})
