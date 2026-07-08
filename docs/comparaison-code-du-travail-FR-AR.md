# Comparaison — Code du travail marocain (Loi n° 65‑99)
### Version française vs version arabe — différences pointées exactement

> **Fichiers comparés**
> - **FR** : `code-du-travail.pdf` — *« Version consolidée en date du 26 octobre 2011 »* — 206 pages, 589 articles.
> - **AR** : `القانون_رقم_65_99_المتعلق_بمدونة_الشغل.pdf` — version consolidée intégrant les modifications **jusqu'au 9 février 2021** — 144 pages, 589 articles. (Source : Conseil Supérieur du Pouvoir Judiciaire / المجلس الأعلى للسلطة القضائية, avril 2025.)

---

## 0. Verdict en une phrase

Ton intuition est correcte — **la version arabe est plus récente** — **mais l'écart réel est minuscule** : les deux textes sont le **même Code (Loi 65‑99, 589 articles, structure identique)**. La version arabe ne diffère que par **UNE loi de plus intégrée (02.21 de 2021)**, qui **modifie exactement 2 articles : l'article 32 et l'article 256**. Tout le reste est identique. **Tu n'as donc PAS à tout refaire — juste à patcher 2 articles + une mise en garde importante (§6).**

---

## 1. Identité des deux documents

| Attribut | FR (`code-du-travail.pdf`) | AR (`القانون رقم 65.99…`) |
|---|---|---|
| Loi de base | Dahir n° 1‑03‑194 du 11 sept. 2003, Loi 65‑99 | Idem |
| Date de consolidation | **26 octobre 2011** (p. 1) | **≈ 9 février 2021** (implicite via loi 02.21) |
| Nombre d'articles | 589 | 589 |
| Structure (Livres / Titres) | Livre préliminaire → Livre VII | Identique |
| Langue | Traduction française (édition de traduction du B.O.) | **Texte arabe = version juridiquement faisant foi** |
| B.O. de publication d'origine | n° 5210 du 6 mai 2004, p. 600 *(édition de traduction FR)* | n° 5167 du 8 déc. 2003, p. 3969 *(édition arabe originale)* |

> ⚠️ **Point de méthode à retenir** : tes deux fichiers diffèrent sur **DEUX axes à la fois** — (a) la **langue** (traduction FR vs original AR) et (b) la **date de consolidation** (2011 vs 2021). Un « diff » caractère par caractère entre les deux n'a aucun sens (langues différentes). La seule différence *de fond* est l'axe (b), résumé ci‑dessous.

---

## 2. Différence de fond n° 1 — l'historique des amendements (page 2 des deux docs)

Liste des lois modificatrices déclarées en tête de chaque document :

| Loi modificatrice | Objet | Présente en **FR (2011)** ? | Présente en **AR (2021)** ? |
|---|---|:--:|:--:|
| **Loi 02.21** (Dahir 1.21.01 du 5 févr. 2021 ; B.O. 6959 bis du 9 févr. 2021, p. 1139) | Modifie **art. 32 et 256** (rétablissement du service militaire) | ❌ **NON** | ✅ **OUI** |
| **Loi 19.12** (Dahir 1.16.21 du 10 août 2016 ; B.O. 6493 du 22 août 2016, p. 6175) | Conditions de travail des **travailleuses/travailleurs domestiques** | ❌ **NON** | ✅ **OUI** |
| Loi 58.11 (Dahir 1.11.170 du 25 oct. 2011) | Cour de cassation (remplace « Cour suprême ») | ✅ OUI | ✅ OUI |
| Loi 48.06 (Dahir 1.06.233 du 17 avr. 2007) | **Suppression** du service militaire | ✅ OUI | ✅ OUI |

**Le delta d'amendements AR − FR = { Loi 02.21 (2021), Loi 19.12 (2016) }.**

- **Loi 02.21** → change *réellement le texte* de 2 articles du Code (voir §3). **C'est la seule vraie divergence de contenu article.**
- **Loi 19.12** → régime **autonome** pour les employés de maison ; ce n'est **pas** une modification des 589 articles numérotés — c'est une loi séparée simplement citée dans l'en‑tête arabe. (À traiter comme un corpus *complémentaire*, pas comme un « article manquant ».)

---

## 3. Différences article par article (le cœur du diff)

### 🔴 Article 32 — Suspension provisoire du contrat de travail

| | Version FR (2011) | Version AR (2021) |
|---|---|---|
| **Page (PDF)** | **p. 24** (numéro imprimé « ‑ 24 ‑ ») | **p. 18** (numéro imprimé 18) |
| **Alinéa 1** | **VIDE / ABROGÉ** — le texte affiche « 1. …………………… » avec la note de bas de page 11 : *« Abrogé par l'article unique de la loi n° 48‑06 relative à la suppression du service militaire »* | **RÉTABLI** — « **1. فترة أداء الخدمة العسكرية** » (= *pendant la période d'accomplissement du service militaire*) |
| Alinéas 2 à 7 | Identiques (maladie/accident, maternité, incapacité temporaire, absences art. 274/275/277, grève, fermeture provisoire) | Identiques |
| Note de bas de page | fn 11 → abrogation par **loi 48‑06 (2007)** | fn 10 → *« تم تغيير وتتميم المادة 32 … بمقتضى المادة الأولى من القانون رقم 02.21 »* (modifié par l'art. 1 de la **loi 02.21**) |

**Nature du changement** : l'alinéa « service militaire » existait en 2003 → **abrogé en 2007** (loi 48‑06) → **réintroduit en 2021** (loi 02.21), après le rétablissement du service militaire obligatoire au Maroc en 2019 (loi 44‑18). La version FR (figée en 2011) montre donc l'état *abrogé/vide* ; la version AR montre l'état *réintroduit*.

---

### 🔴 Article 256 — Indemnité de congé en cas d'appel au service militaire

| | Version FR (2011) | Version AR (2021) |
|---|---|---|
| **Page (PDF)** | **p. 94** (numéro imprimé « ‑ 94 ‑ ») | **p. 68** (numéro imprimé 68) |
| **Texte** | **VIDE / ABROGÉ** — « Article 256 » suivi de la note 35 : *« Abrogé par l'article unique de la loi 48‑06 portant suppression du service militaire »* | **RÉTABLI** — « يؤدي المشغل للأجير الذي طُلب للخدمة العسكرية، قبل أن يستفيد من العطلة السنوية المؤدى عنها، تعويضاً عن عدم التمتع بهذه العطلة، وذلك عند مغادرته المقاولة. » (= *l'employeur verse au salarié appelé au service militaire, avant qu'il n'ait bénéficié de son congé annuel payé, une indemnité pour le congé non pris, lors de son départ de l'entreprise*) |
| Note de bas de page | fn 35 → abrogation par **loi 48‑06 (2007)** | fn 30 → modifié par l'art. 1 de la **loi 02.21** |

**Nature du changement** : identique au mécanisme de l'art. 32 — abrogé en 2007, réintroduit en 2021.

> ✅ **Vérification structurelle** : hors art. 32 et 256, l'ensemble des articles 1 → 589 est **présent et à la même position** dans les deux documents (contrôle automatique sur les 589 en‑têtes d'articles des deux PDF : aucun autre écart). **Aucun autre article n'a été ajouté, supprimé ou renuméroté.**

---

## 4. Divergences de citations / références (à ne pas confondre avec des différences de fond)

| Élément | FR (2011) | AR (2021) | Correct ? |
|---|---|---|---|
| B.O. de la loi 48‑06 | n° **5522** du 3 avr. 2007, **p. 581** | n° **5519** du 23 avr. 2007, **p. 1283** | La version **AR est exacte** (confirmé : B.O. n° 5519, 23 avr. 2007). La référence FR est **erronée**. |
| B.O. de publication du Code | n° 5210, 6 mai 2004 (traduction FR) | n° 5167, 8 déc. 2003 (original AR) | Les deux sont corrects — éditions linguistiques différentes du B.O. |

Ce ne sont pas des différences de *droit*, mais des divergences de **métadonnées de citation** — utiles à normaliser dans un RAG juridique (sinon le modèle risque de citer une référence B.O. fausse pour la loi 48‑06).

---

## 5. Ce qui est strictement IDENTIQUE entre les deux versions

- Les 589 articles, leur numérotation et leur ordre.
- L'architecture en Livres / Titres / Chapitres / Sections / Fer­ (الفرع).
- Le dahir de promulgation (1‑03‑194, 11 sept. 2003).
- L'intégration de la loi 58.11 (Cour de cassation) et de la loi 48.06 (les *autres* effets de l'abrogation de 2007 hors art. 32/256).

---

## 6. ⚠️ Angle mort critique pour ton projet : la version arabe 2021 n'est PAS « la plus récente »

Ton objectif est *« le code le plus à jour »* comme fondation du RAG. Or **même ta version arabe (arrêtée à févr. 2021) est déjà dépassée en 2026** :

- Un **projet de loi n° 032.26 modifiant la Loi 65‑99** a été adopté en Conseil de gouvernement (2026). Il **modifie l'article 193** pour ramener la durée de travail journalière de **12 h à 8 h** pour les **agents de gardiennage** (entreprises soumises à la loi 27‑06), **entrée en vigueur prévue en 2027**.
- À la date de ce rapport, cet amendement **n'était pas encore publié au Bulletin officiel** (stade « adopté en conseil de gouvernement » / processus législatif en cours). **À vérifier** avant intégration.
- D'autres textes sont en discussion (proposition sur l'art. 11 — principe de faveur ; proposition sur l'art. 516 ; loi organique sur la grève — texte *séparé* du Code).

**Conséquence pour ton RAG** : « à jour » n'est pas un état figé, c'est un *processus*. Prévois dès maintenant un champ de métadonnée `date_consolidation` par document et un mécanisme de veille B.O. (SGG / adala.justice.gov.ma), sinon ton assistant donnera des réponses périmées avec assurance — le pire défaut pour un assistant juridique « souverain ».

---

## 7. Recommandation concrète pour la fondation du RAG

1. **Source de vérité = l'arabe.** En droit marocain, **le texte arabe fait juridiquement foi** ; le français est une traduction. Pour un « Sovereign Legal RAG », l'arabe doit être le corpus primaire, avec `date_consolidation = 2021‑02‑09`.
2. **Garde le français comme traduction alignée**, pas comme version concurrente. Beaucoup de citoyens interrogent en français/darija ; mais aligne‑le et **corrige/annexe les 2 articles divergents** (32, 256) pour qu'il reflète l'état 2021, sinon ton FR répondra « article abrogé » à tort.
3. **Applique le patch minimal** : remplace le texte des art. 32 et 256 côté FR par la traduction de la version 2021 (rétablissement service militaire), et corrige la référence B.O. de la loi 48‑06 (→ n° 5519).
4. **Traite la loi 19.12 (domestiques) comme un corpus séparé** relié, pas comme un article du Code.
5. **Ajoute une note de fraîcheur** : signale l'amendement art. 193 (gardiennage, en cours 2026) comme *pending* dans tes métadonnées.

---

## Annexe — Table de diff exploitable (pour ton pipeline)

```json
{
  "loi": "65-99",
  "fr": { "fichier": "code-du-travail.pdf", "consolidation": "2011-10-26", "pages": 206, "articles": 589 },
  "ar": { "fichier": "القانون_رقم_65_99_المتعلق_بمدونة_الشغل.pdf", "consolidation": "2021-02-09", "pages": 144, "articles": 589 },
  "amendements_delta_ar_moins_fr": ["loi 02.21 (2021)", "loi 19.12 (2016)"],
  "articles_modifies": [
    {
      "article": 32,
      "sujet": "suspension du contrat - service militaire (alinéa 1)",
      "fr": { "page_pdf": 24, "etat": "alinéa 1 ABROGÉ (loi 48-06, 2007)" },
      "ar": { "page_pdf": 18, "etat": "alinéa 1 RÉTABLI (loi 02.21, 2021)" }
    },
    {
      "article": 256,
      "sujet": "indemnité de congé pour salarié appelé au service militaire",
      "fr": { "page_pdf": 94, "etat": "ABROGÉ (loi 48-06, 2007)" },
      "ar": { "page_pdf": 68, "etat": "RÉTABLI (loi 02.21, 2021)" }
    }
  ],
  "divergence_citation": {
    "loi_48-06_BO": { "fr": "n°5522, 03-04-2007, p.581 (ERRONÉ)", "ar": "n°5519, 23-04-2007, p.1283 (CORRECT)" }
  },
  "gap_connu_2026": {
    "loi_032.26": "modifie art. 193 (gardiennage 12h->8h, en vigueur 2027) - non publié au BO à ce jour, à vérifier"
  },
  "recommandation_source_verite": "arabe (texte faisant foi)"
}
```
