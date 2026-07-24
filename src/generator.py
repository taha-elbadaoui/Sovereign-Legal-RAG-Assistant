import ollama
from retriever import hybrid_search

MODEL = "mistral:7b"

# Grounding + citation + abstention rules live entirely in this prompt for now.
# A pre-LLM relevance-threshold gate (skip calling the model at all when
# retrieval confidence is too low) is planned per the design doc (F5) but not
# implemented yet -- it needs calibration against real queries first, and an
# uncalibrated threshold risks wrongly refusing a valid question live.
SYSTEM_PROMPT = """Tu es un assistant juridique qui répond à des questions sur le Code du travail marocain (Loi 65-99).

Règles strictes :
1. Réponds UNIQUEMENT à partir des articles fournis ci-dessous. N'utilise aucune autre connaissance ni aucune supposition.
2. Cite systématiquement le ou les numéros d'article sur lesquels tu t'appuies, sous la forme (Article N).
3. Si les articles fournis ne permettent pas de répondre à la question, dis-le clairement au lieu d'inventer une réponse, avec exactement cette phrase : "Je ne dispose pas d'information suffisante dans le corpus fourni pour répondre à cette question."
4. Ne donne jamais de conseil juridique personnalisé ; rappelle que la réponse est informative et ne remplace pas l'avis d'un professionnel du droit.
"""


def format_context(articles):
    blocks = [f"Article {a['article_number']} :\n{a['article_text']}" for a in articles]
    return "\n\n".join(blocks)


def answer(question, k=5):
    articles = hybrid_search(question, k=k)
    context = format_context(articles)

    user_prompt = f"Articles du Code du travail :\n\n{context}\n\nQuestion : {question}"

    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response["message"]["content"], articles


if __name__ == "__main__":
    import sys

    question = " ".join(sys.argv[1:]) or "Quelle est la durée du congé annuel payé ?"
    reply, sources = answer(question)

    print(f"Question : {question}\n")
    print(reply)
    print("\n--- Articles récupérés (retrieval, pas forcément tous cités) ---")
    for a in sources:
        print(f"Article {a['article_number']}")
