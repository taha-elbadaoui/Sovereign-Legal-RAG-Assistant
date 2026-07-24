import os
import re
import json
import pymupdf as fitz

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "raw", "code-du-travail.pdf"))
OUTPUT_JSONL = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "processed", "corpus_chunks.jsonl"))

# Page-break noise PyMuPDF leaves behind: " -\n<page number>\n - "
PAGINATION_RE = re.compile(r"\n\s*-\s*\n\s*\d+\s*\n\s*-\s*\n")

# Hierarchy header lines: "Livre ...", "Titre ...", "Chapitre ...", "Section ..."
# Some titles are too long to fit on one visual line in the PDF and wrap onto a
# second or third line (e.g. "Chapitre VII : Le Conseil supérieur de la promotion de\n
# l'emploi et les conseils régionaux et provinciaux de la\npromotion de l'emploi.").
# The trailing "(?:\n(?!...)[^\n]*)*" keeps consuming further lines as long as they
# don't themselves start a new Livre/Titre/Chapitre/Section/Article boundary — found
# by scanning for header lines immediately followed by a short non-boundary line,
# which surfaced 32 wrapped titles (5 of them wrapping a 3rd line) that were silently
# truncating hierarchy metadata and leaking their tail into the next article's body.
HEADER_RE = re.compile(
    r"^(Livre|Titre|Chapitre|Section)\s[^\n]*"
    r"(?:\n(?!\s*(?:Livre|Titre|Chapitre|Section|Article)\b)[^\n]*)*",
    re.MULTILINE,
)
LEVEL_KEY = {"Livre": "livre", "Titre": "titre", "Chapitre": "chapitre", "Section": "section"}
# When a header at one level appears, everything below it resets (a new Titre means
# the old Chapitre/Section no longer apply until a new one is announced).
RESET_BELOW = {
    "livre": ["titre", "chapitre", "section"],
    "titre": ["chapitre", "section"],
    "chapitre": ["section"],
    "section": [],
}

doc = fitz.open(PDF_PATH)
full_text = ""
for page in doc:
    full_text += page.get_text()

# 1. Strip pagination markers before splitting (they never carry legal content,
#    and stripping them here can't disturb the Article boundaries below).
full_text = PAGINATION_RE.sub("\n", full_text)

# 2. Split into article label/body pairs.

parts = re.split(r"(^[ \t]*Article\s(?:premier|\d{1,3}))", full_text, flags=re.MULTILINE)
temp = parts[-1].split("TABLE DES MATIÈRES")
parts[-1] = temp[0]
parts.append(temp[1])

articles = []
for i in range(1, len(parts) - 1, 2):
    number = "1" if "premier" in parts[i] else parts[i].replace("Article ", "").strip()
    articles.append({"article_number": number, "article_text": parts[i + 1], "amende_2021": False})

# 3. Hierarchy: Livre/Titre/Chapitre/Section headers sit at the END of the article
# body that precedes them in the raw text (they announce what comes NEXT), so we
# walk articles in order, apply whatever hierarchy was announced so far, THEN look
# for new headers inside this article's own text to carry forward to the next one.

hierarchy = {"livre": None, "titre": None, "chapitre": None, "section": None}


def apply_headers_and_advance(text):
    for match in HEADER_RE.finditer(text):
        key = LEVEL_KEY[match.group(1)]
        # wrapped titles span multiple physical lines; collapse them to one clean string
        hierarchy[key] = re.sub(r"\s+", " ", match.group(0)).strip()
        for lower_key in RESET_BELOW[key]:
            hierarchy[lower_key] = None


apply_headers_and_advance(parts[0])  # seed from the front matter

for article in articles:
    article["livre"] = hierarchy["livre"]
    article["titre"] = hierarchy["titre"]
    article["chapitre"] = hierarchy["chapitre"]
    article["section"] = hierarchy["section"]

    apply_headers_and_advance(article["article_text"])

    # header lines are structural, not legal text: strip them out of the body
    article["article_text"] = HEADER_RE.sub("", article["article_text"])

    # 4. collapse pymupdf's per-visual-line newlines into single spaces
    article["article_text"] = re.sub(r"\s+", " ", article["article_text"]).strip()

# 4b. Patch articles 32 and 256: both are abrogated/near-empty in this 2011 FR
# PDF (service-militaire alinéas removed by loi 48-06 in 2007), but restored by
# loi 02.21 in 2021. Replaced with the French gloss of the 2021 Arabic text
# already verified against the source in docs/comparaison-code-du-travail-FR-AR.md
# Flagged with "amende_2021" so this deviation from the
# raw 2011 PDF stays visible in the data itself, per Annexe A of the design doc.
PATCHES = {
    "32": ("Le contrat est provisoirement suspendu : 1. pendant la période "
           "d'accomplissement du service militaire ; 2. pendant l'absence du "
           "salarié pour maladie ou accident dûment constaté par un médecin ; "
           "3. pendant la période qui précède et suit l'accouchement dans les "
           "conditions prévues par les articles 154 et 156 ci-dessous ; "
           "4. pendant la période d'incapacité temporaire du salarié résultant "
           "d'un accident du travail ou d'une maladie professionnelle ; "
           "5. pendant les périodes d'absence du salarié prévues par les "
           "articles 274, 275 et 277 ci-dessous ; 6. pendant la durée de la "
           "grève ; 7. pendant la fermeture provisoire de l'entreprise "
           "intervenue légalement. Toutefois, nonobstant les dispositions "
           "prévues ci-dessus, le contrat de travail à durée déterminée prend "
           "fin à sa date d'échéance."),
    "256": ("L'employeur verse au salarié appelé au service militaire, avant "
            "qu'il n'ait bénéficié de son congé annuel payé, une indemnité "
            "pour le congé non pris, lors de son départ de l'entreprise."),
}
for article in articles:
    if article["article_number"] in PATCHES:
        article["article_text"] = PATCHES[article["article_number"]]
        article["amende_2021"] = True

# 5. Serialize to JSONL, one article per line.
os.makedirs(os.path.dirname(OUTPUT_JSONL), exist_ok=True)
with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
    for article in articles:
        f.write(json.dumps(article, ensure_ascii=False) + "\n")

print(f"{len(articles)} articles -> {OUTPUT_JSONL}")
