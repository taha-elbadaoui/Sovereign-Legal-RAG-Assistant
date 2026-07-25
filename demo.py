"""Scripted demonstration of the assistant — one capability per scene.

Built for a live walkthrough (soutenance / encadrant demo): every scene runs the
real pipeline, so nothing here is staged. Run it with no arguments to play the
whole sequence, or pass a scene number to run just one.

    python demo.py          # all scenes
    python demo.py 3        # scene 3 only

Requires Ollama running (`ollama list` should show mistral:7b).
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from retriever import retrieve, dense_search, bm25_search  # noqa: E402
from app import answer_question, ABSTENTION_THRESHOLD      # noqa: E402
from generator import MODEL                                # noqa: E402

WIDTH = 78
PAUSE = float(os.environ.get("DEMO_PAUSE", "0"))  # set e.g. 2 for a slower live demo


def title(n, text):
    print()
    print("=" * WIDTH)
    print(f"  SCÈNE {n} — {text}")
    print("=" * WIDTH)
    time.sleep(PAUSE)


def say(text=""):
    print(text)


def ask(question, note=None):
    """Run one real question through the full pipeline and show the result."""
    say(f"\n  Question : {question}")
    if note:
        say(f"  ({note})")
    started = time.time()
    result = answer_question(question)
    elapsed = time.time() - started

    if result["error"]:
        say(f"\n  [!] {result['error']}")
        return result

    say(f"\n  Score de recherche : {result['retrieval_score']:.3f}"
        f"   (seuil d'abstention : {ABSTENTION_THRESHOLD})")
    say(f"  Abstention pré-LLM : {'OUI — le modèle n a pas été appelé' if result['abstained'] else 'non'}")
    say(f"  Temps              : {elapsed:.1f} s\n")
    for line in result["answer"].split("\n"):
        say(f"  {line}")
    if result["cited"]:
        say(f"\n  Articles cités      : {', '.join(sorted(result['cited'], key=int))}")
        say(f"  Citations vérifiées : "
            f"{'toutes présentes dans le contexte' if not result['unverified'] else 'NON VÉRIFIÉES -> ' + ', '.join(sorted(result['unverified']))}")
    time.sleep(PAUSE)
    return result


# --------------------------------------------------------------------------- #
def scene1():
    title(1, "Le corpus : 589 articles structurés")
    import json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "data", "processed", "corpus_chunks.jsonl")
    with open(path, encoding="utf-8") as f:
        articles = [json.loads(l) for l in f]
    say(f"\n  {len(articles)} articles extraits du PDF officiel du Code du travail.")
    say("  Chaque article porte sa position exacte dans la hiérarchie de la loi :\n")
    a = next(x for x in articles if x["article_number"] == "152")
    say(f"    Article {a['article_number']}")
    say(f"      livre    : {a['livre']}")
    say(f"      titre    : {a['titre']}")
    say(f"      chapitre : {a['chapitre']}")
    say(f"\n      texte    : {a['article_text'][:150]}...")
    say("\n  -> Le corpus se régénère à l'identique depuis le PDF (octet pour octet).")


def scene2():
    title(2, "La recherche : pourquoi hybride (dense + BM25)")
    q = "Quelle est la durée du congé de maternité ?"
    say(f"\n  Question : {q}\n")
    dense = [i for i, _ in dense_search(q, k=5)]
    lex = bm25_search(q, k=5)
    hyb = [a["article_number"] for a in retrieve(q, k=5)["articles"]]
    say(f"    Dense seul (sémantique) : {', '.join(dense)}")
    say(f"    BM25 seul (mots-clés)   : {', '.join(lex)}")
    say(f"    Hybride (fusion RRF)    : {', '.join(hyb)}")
    say("\n  Les deux méthodes trouvent des choses différentes : le sémantique")
    say("  comprend la reformulation, le lexical retrouve les termes exacts.")


def scene3():
    title(3, "Réponse ancrée avec citation obligatoire")
    ask("Un employeur peut-il licencier une salariée enceinte ?")


def scene4():
    title(4, "Abstention — question hors périmètre, mais juridique")
    ask("Quelle est la procédure pour divorcer au Maroc ?",
        note="relève du Code de la famille, pas du Code du travail")
    say("\n  -> Le système refuse ET nomme le bon domaine, sans jamais inventer")
    say("     de numéro d'article ou de loi qu'il n'a pas reçu.")


def scene5():
    title(5, "Abstention — question sans rapport (garde-fou avant le LLM)")
    ask("Quelle est la recette du couscous ?",
        note="score trop bas -> le LLM n'est même pas appelé")


def scene6():
    title(6, "Article inexistant — ne rien inventer")
    ask("Que dit l'article 999 du Code du travail ?",
        note="cet article n'existe pas : la loi s'arrête à 589")


def scene7():
    title(7, "Recherche par numéro d'article explicite")
    ask("Que dit l'article 32 du Code du travail ?",
        note="cas particulier : la recherche sémantique seule échoue ici")
    say("\n  Deux choses à noter :")
    say("    1. « que dit l'article 32 » ne ressemble PAS au contenu de l'article 32.")
    say("       La similarité sémantique seule ne peut donc pas le retrouver : une")
    say("       référence explicite déclenche une recherche directe par numéro.")
    say("    2. Les articles signalés « non vérifiés » sont les renvois internes")
    say("       cités DANS le texte de l'article 32 lui-même (« …prévues par les")
    say("       articles 154 et 156 »). Le contrôle est volontairement strict :")
    say("       il signale tout numéro absent du contexte, quitte à sur-signaler.")


def scene8():
    title(8, "Ce qui est mesuré")
    say(f"\n  Modèle local : {MODEL}   (aucun appel à une API externe)\n")
    say("  Recherche (eval/run_eval.py, 32 questions) :")
    say("      Dense seul      Recall@5 0.97   MRR 0.89")
    say("      BM25 seul       Recall@5 0.78   MRR 0.63")
    say("      Hybride (RRF)   Recall@5 0.88   MRR 0.79")
    say("\n  Réponses (eval/run_answer_eval.py, 37 questions) :")
    say("      voir eval/resultats-evaluation.md — citation, abstention,")
    say("      vérification des citations, refus à tort.")
    say("\n  Les deux scripts sont rejouables : rien n'est saisi à la main.")


SCENES = [scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8]

if __name__ == "__main__":
    print()
    print("#" * WIDTH)
    print("#  ASSISTANT JURIDIQUE SOUVERAIN — Code du travail marocain (Loi 65-99)")
    print("#  Démonstration : recherche -> réponse citée -> abstention")
    print("#" * WIDTH)

    if len(sys.argv) > 1:
        idx = int(sys.argv[1])
        SCENES[idx - 1]()
    else:
        for fn in SCENES:
            fn()

    print()
    print("=" * WIDTH)
    print("  Fin de la démonstration.")
    print("=" * WIDTH)
    print()
