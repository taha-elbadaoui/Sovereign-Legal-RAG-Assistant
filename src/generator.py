import ollama

MODEL = "mistral:7b"

# temperature: low = stable, near-deterministic answers (right fit for legal Q&A).
# repeat_penalty: raised above Ollama's default (1.1) because low-temperature
# generation on this model can degenerate into repeating the same word/phrase
# hundreds of times once it runs out of confident tokens (observed live: a
# question about "toutes les fêtes payées" looping on one holiday name
# indefinitely). num_predict caps the worst case so a runaway generation still
# stops on its own instead of running unbounded.
GENERATION_OPTIONS = {"temperature": 0.1, "repeat_penalty": 1.3, "num_predict": 700}

DISCLAIMER = (
    "Réponse fournie à titre informatif, fondée sur les textes cités ; "
    "elle ne constitue pas un conseil juridique. Pour une situation particulière, "
    "consultez un professionnel du droit."
)

SYSTEM_PROMPT = """Tu es un assistant juridique qui répond à des questions sur le Code du travail marocain (Loi 65-99).

Règles strictes :
1. Réponds UNIQUEMENT à partir des articles fournis ci-dessous. N'utilise aucune autre connaissance ni aucune supposition.
2. Cite systématiquement le ou les numéros d'article sur lesquels tu t'appuies, sous la forme (Article N).
3. Si les articles fournis ne permettent pas de répondre à la question, dis-le clairement au lieu d'inventer une réponse, avec exactement cette phrase : "Je ne dispose pas d'information suffisante dans le corpus fourni pour répondre à cette question."
4. Cette règle s'applique même si un numéro d'article précis est demandé et n'apparaît pas dans le contexte fourni : n'écris JAMAIS de phrase du type "cependant, je peux vous dire que cet article traite de..." ou toute autre supposition sur son contenu. Constater l'absence de l'article, puis t'arrêter à la phrase d'abstention de la règle 3 — ne complète jamais par une supposition, même présentée comme approximative ou incertaine.
5. Par défaut, RÉPONDS. Si les articles fournis contiennent de quoi répondre, même partiellement, réponds en citant ces articles — l'abstention est réservée aux cas où les articles fournis ne traitent réellement pas du sujet. Ne refuse pas une question simplement parce qu'elle te paraît sensible, incomplète ou proche d'un autre domaine.
6. En revanche, si la question relève réellement d'un autre texte de loi que le Code du travail, il t'est absolument interdit d'en décrire le contenu : ne cite jamais un numéro de loi, un numéro d'article, une procédure ou une règle provenant d'un autre code — tu n'as reçu aucun de ces textes, donc toute affirmation à leur sujet serait inventée. Tu peux seulement nommer le domaine concerné. N'écris jamais que tu as "consulté" un texte : les seuls textes dont tu disposes sont les articles fournis ci-dessous.
7. Ne donne jamais de conseil juridique personnalisé.
8. Réponds de façon claire et concise, dans la même langue que la question.
"""


def format_context(articles):
    blocks = [f"Article {a['article_number']} :\n{a['article_text']}" for a in articles]
    return "\n\n".join(blocks)


def generate(question, articles):
    """Call the local LLM. Returns (answer_text, error).

    error is None on success, or a human-readable string if the model could not
    be reached (e.g. the Ollama service is not running) — so the caller can fail
    gracefully instead of crashing.
    """
    context = format_context(articles)
    user_prompt = f"Articles du Code du travail :\n\n{context}\n\nQuestion : {question}"

    try:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            options=GENERATION_OPTIONS,
        )
    except Exception as exc:
        return None, (
            f"Impossible de contacter le modèle local ({MODEL}) via Ollama : {exc}. "
            "Vérifiez qu'Ollama est lancé (`ollama serve`) et que le modèle est installé "
            "(`ollama pull mistral:7b`)."
        )

    return response["message"]["content"].strip(), None


def generate_stream(question, articles):
    """Yield the answer piece by piece as the model produces it (for the web UI's
    typing effect). Raises on connection failure — the caller handles it."""
    context = format_context(articles)
    user_prompt = f"Articles du Code du travail :\n\n{context}\n\nQuestion : {question}"

    stream = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        options=GENERATION_OPTIONS,
        stream=True,
    )
    for chunk in stream:
        piece = chunk.get("message", {}).get("content", "")
        if piece:
            yield piece


if __name__ == "__main__":
    import sys
    from retriever import hybrid_search

    question = " ".join(sys.argv[1:]) or "Quelle est la durée du congé annuel payé ?"
    sources = hybrid_search(question)
    reply, error = generate(question, sources)

    print(f"Question : {question}\n")
    print(error if error else reply)
