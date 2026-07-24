# Jeu de test manuel — Code du travail (Loi 65-99)

Batch de questions pour tester `generator.py` avant la démo. Pour chaque question,
la réponse attendue et l'article source sont indiqués — sert à vérifier que la
réponse générée cite bien le(s) bon(s) article(s) et ne contredit pas le texte.
Ceci est un échantillon manuel rapide, pas encore le jeu de référence formel de
30-50 questions prévu pour S5/S6 (`eval/reference_qa.jsonl`).

---

**1. Quelle est la durée de la période d'essai pour un cadre en CDI ?**
Réponse attendue : trois mois, renouvelable une seule fois.
Article source : **Article 14**

<sub>Commande :</sub>
```
python src/generator.py "Quelle est la durée de la période d'essai pour un cadre en CDI ?"
```

---

**2. Quel est l'âge minimum légal pour travailler au Maroc ?**
Réponse attendue : quinze ans révolus.
Article source : **Article 143**

<sub>Commande :</sub>
```
python src/generator.py "Quel est l'âge minimum légal pour travailler au Maroc ?"
```

---

**3. Combien de jours de congé annuel payé un salarié acquiert-il par mois de service ?**
Réponse attendue : un jour et demi de travail effectif par mois de service (deux jours pour les salariés de moins de 18 ans).
Article source : **Article 231**

<sub>Commande :</sub>
```
python src/generator.py "Combien de jours de congé annuel payé un salarié acquiert-il par mois de service ?"
```

---

**4. Quelle est la durée du congé de maternité ?**
Réponse attendue : quatorze semaines.
Article source : **Article 152**

<sub>Commande :</sub>
```
python src/generator.py "Quelle est la durée du congé de maternité ?"
```

---

**5. Quelle est la durée légale du travail dans les activités non agricoles ?**
Réponse attendue : 2288 heures par an, ou 44 heures par semaine.
Article source : **Article 184**

<sub>Commande :</sub>
```
python src/generator.py "Quelle est la durée légale du travail dans les activités non agricoles ?"
```

---

**6. Dans quel délai un salarié doit-il saisir le tribunal en cas de licenciement contesté ?**
Réponse attendue : 90 jours à compter de la réception de la décision de licenciement, sous peine de déchéance.
Article source : **Article 65**

<sub>Commande :</sub>
```
python src/generator.py "Dans quel délai un salarié doit-il saisir le tribunal en cas de licenciement contesté ?"
```

---

**7. À partir de combien de salariés une entreprise doit-elle créer un comité d'entreprise ?**
Réponse attendue : cinquante salariés employés habituellement.
Article source : **Article 464**

<sub>Commande :</sub>
```
python src/generator.py "À partir de combien de salariés une entreprise doit-elle créer un comité d'entreprise ?"
```

---

**8. À quel âge un salarié doit-il être mis à la retraite ?**
Réponse attendue : soixante ans en général ; cinquante-cinq ans pour les salariés du secteur minier ayant travaillé au fond pendant au moins cinq ans.
Article source : **Article 526**

<sub>Commande :</sub>
```
python src/generator.py "À quel âge un salarié doit-il être mis à la retraite ?"
```

---

**9. Le harcèlement sexuel commis par l'employeur est-il une faute grave ?**
Réponse attendue : oui — c'est explicitement listé comme faute grave de l'employeur ; un salarié qui quitte son poste pour ce motif est assimilé à un licenciement abusif.
Article source : **Article 40**

<sub>Commande :</sub>
```
python src/generator.py "Le harcèlement sexuel commis par l'employeur est-il une faute grave ?"
```

---

**10. Un employeur peut-il employer un mineur de moins de 18 ans dans les mines ?**
Réponse attendue : non, c'est interdit (carrières et travaux souterrains au fond des mines).
Article source : **Article 179**

<sub>Commande :</sub>
```
python src/generator.py "Un employeur peut-il employer un mineur de moins de 18 ans dans les mines ?"
```

---

**11. Combien de temps par mois un délégué des salariés dispose-t-il pour exercer ses fonctions ?**
Réponse attendue : quinze heures par mois et par délégué, sauf circonstances exceptionnelles, payées comme temps de travail effectif.
Article source : **Article 456**

<sub>Commande :</sub>
```
python src/generator.py "Combien de temps par mois un délégué des salariés dispose-t-il pour exercer ses fonctions ?"
```

---

**12. Quelles catégories de salariés sont régies par des statuts spéciaux plutôt que par le Code du travail ?**
Réponse attendue : salariés des entreprises/établissements publics, marins, salariés des entreprises minières, journalistes professionnels, salariés de l'industrie cinématographique, concierges d'immeubles d'habitation — mais soumis au Code du travail pour tout ce que leurs statuts ne couvrent pas.
Article source : **Article 3**

<sub>Commande :</sub>
```
python src/generator.py "Quelles catégories de salariés sont régies par des statuts spéciaux plutôt que par le Code du travail ?"
```

---

**13. Pour combien de temps peut-on conclure un CDD lors de l'ouverture d'une nouvelle entreprise (hors secteur agricole) ?**
Réponse attendue : un an maximum, renouvelable une seule fois ; devient CDI au-delà.
Article source : **Article 17**

<sub>Commande :</sub>
```
python src/generator.py "Pour combien de temps peut-on conclure un CDD lors de l'ouverture d'une nouvelle entreprise ?"
```

---

**14. Quelle amende est prévue en cas de paiement d'un salaire inférieur au salaire minimum légal ?**
Réponse attendue : 300 à 500 dirhams par salarié concerné, sans dépasser 20.000 dirhams au total.
Article source : **Article 361**

<sub>Commande :</sub>
```
python src/generator.py "Quelle amende est prévue en cas de paiement d'un salaire inférieur au salaire minimum légal ?"
```

---

**15. Quelle est la procédure pour divorcer au Maroc ? *(test d'abstention — hors périmètre)***
Réponse attendue : le système doit **refuser de répondre** — cette question relève du Code de la famille, pas du Code du travail. Aucun article du corpus ne la couvre.
Article source : *aucun — doit déclencher l'abstention*

<sub>Commande :</sub>
```
python src/generator.py "Quelle est la procédure pour divorcer au Maroc ?"
```

---

## Comment tester

Chaque question a sa commande prête à copier-coller ci-dessus. Comparer la
réponse générée (numéros d'articles cités + contenu) à la réponse attendue.
Noter tout écart — citation manquante, article incorrect, ou (question 15)
absence d'abstention alors qu'elle est requise.
