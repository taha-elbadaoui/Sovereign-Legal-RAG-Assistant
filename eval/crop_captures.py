"""Recadre les captures d'interface sur leur contenu utile.

Deuxieme etape apres eval/capture_ui.js : les captures brutes montrent toute
la fenetre -- barre laterale, puis une large zone vide entre la fin de la
reponse et la zone de saisie. A la taille ou la figure les place dans le
rapport, le texte de l'interface devient illisible.

On retire la barre laterale, puis on coupe dans le plus grand intervalle de
lignes vides : celui qui separe la reponse de la zone de saisie.

Usage :  python eval/crop_captures.py
Entree :  rapport/Figures/captures/*.png       (produites par capture_ui.js)
Sortie :  rapport/Figures/captures/*-crop.png  (utilisees par le rapport)
"""
import os
from PIL import Image

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "rapport", "Figures", "captures")
# Bordure droite de la barre laterale, mesuree sur les captures (facteur 2).
SIDEBAR_PX = 560
MARGE = 36

# Cas ou la detection d'intervalle vide ne suffit pas : l'article deplie
# descend jusqu'a la zone de saisie, sans blanc exploitable. On coupe donc
# juste sous l'encadre de l'article.
BAS_MANUEL = {"02-source-depliee.png": 1500}


def lignes_vides(im):
    """Vrai/faux par ligne : cette ligne est-elle uniquement du fond ?"""
    g = im.convert("L")
    fond = g.getpixel((g.width // 2, g.height // 2))
    vides = []
    for y in range(g.height):
        ligne = list(g.crop((0, y, g.width, y + 1)).getdata())
        vides.append(all(abs(p - fond) <= 18 for p in ligne))
    return vides


for nom in sorted(os.listdir(BASE)):
    if not nom.endswith(".png") or "-crop" in nom:
        continue
    src = os.path.join(BASE, nom)
    im = Image.open(src).convert("RGB")
    chat = im.crop((SIDEBAR_PX, 0, im.width, im.height))

    vides = lignes_vides(chat)

    # Plus long intervalle de lignes vides, cherche dans la moitie basse
    debut_recherche = int(len(vides) * 0.25)
    meilleur = (0, 0, 0)  # (longueur, debut, fin)
    y = debut_recherche
    while y < len(vides):
        if vides[y]:
            d = y
            while y < len(vides) and vides[y]:
                y += 1
            if y - d > meilleur[0]:
                meilleur = (y - d, d, y)
        else:
            y += 1

    longueur, d, f = meilleur
    if nom in BAS_MANUEL:
        bas = BAS_MANUEL[nom]
    else:
        bas = min(chat.height, d + MARGE) if longueur > 80 else chat.height

    crop = chat.crop((0, 0, chat.width, bas))
    dest = os.path.join(BASE, nom.replace(".png", "-crop.png"))
    crop.save(dest)
    print(f"{nom}: {im.size} -> {crop.size}   (vide de {longueur}px a y={d})")
