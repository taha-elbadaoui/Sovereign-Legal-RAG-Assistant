import ollama

MODEL = "mistral:7b"

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
4. Ne donne jamais de conseil juridique personnalisé.
5. Réponds de façon claire et concise, dans la même langue que la question.
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
            options={"temperature": 0.1},  # low = stable, near-deterministic answers
        )
    except Exception as exc:
        return None, (
            f"Impossible de contacter le modèle local ({MODEL}) via Ollama : {exc}. "
            "Vérifiez qu'Ollama est lancé (`ollama serve`) et que le modèle est installé "
            "(`ollama pull mistral:7b`)."
        )

    return response["message"]["content"].strip(), None


if __name__ == "__main__":
    import sys
    from retriever import hybrid_search

    question = " ".join(sys.argv[1:]) or "Quelle est la durée du congé annuel payé ?"
    sources = hybrid_search(question)
    reply, error = generate(question, sources)

    print(f"Question : {question}\n")
    print(error if error else reply)
