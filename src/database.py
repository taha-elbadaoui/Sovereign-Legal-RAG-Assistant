import os
import json
import chromadb
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORPUS_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "processed", "corpus_chunks.jsonl"))
CHROMA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "chroma"))

articles = []
with open(CORPUS_PATH, encoding="utf-8") as f:
    for line in f:
        articles.append(json.loads(line))

# Multilingual embedding model, runs fully local (sovereignty requirement).
# First run downloads and caches the weights (~2.2GB); later runs are instant.
model = SentenceTransformer("BAAI/bge-m3")

# Embed only the legal text itself. Hierarchy (livre/titre/chapitre/section) is kept
# as metadata rather than embedded, so it can be displayed and filtered on without
# diluting the semantic signal a retrieval query is actually matching against.
texts = [a["article_text"] for a in articles]
embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

# Chroma metadata values must be str/int/float/bool, not None — hierarchy fields
# are None for articles at the top of a book/title with no deeper level yet.
def metadata_for(a):
    return {
        "livre": a["livre"] or "",
        "titre": a["titre"] or "",
        "chapitre": a["chapitre"] or "",
        "section": a["section"] or "",
        "amende_2021": a["amende_2021"],
    }

client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection("code_du_travail")

collection.upsert(
    ids=[a["article_number"] for a in articles],
    embeddings=embeddings.tolist(),
    documents=texts,
    metadatas=[metadata_for(a) for a in articles],
)

print(f"{collection.count()} articles indexed -> {CHROMA_DIR}")
