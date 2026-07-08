import os
import pymupdf as fitz
import re 

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "raw", "code-du-travail.pdf"))

doc = fitz.open(PDF_PATH)
articles=[]

full_text = ""
for page in doc:
    full_text += page.get_text()
parts = re.split(r"(^Article\s(?:premier|\d+))", full_text, flags=re.MULTILINE)
temp=parts[-1].split("TABLE DES MATIÈRES")
parts[-1]=temp[0]
parts.append(temp[1])

with open("output.txt", "w", encoding="utf-8") as f:
    for p in parts:
        f.write(p)

for i in range(1,len(parts)-1,2):
    if "premier" in parts[i]:
        articles.append({"article_number": "1", "article_text": parts[i+1]})
    else:
        articles.append({"article_number": parts[i].replace("Article ", ""), "article_text": parts[i+1]})




print(type(parts))      # <class 'list'>  ← confirms it's a list
print(len(parts))       # how many elements
print(parts[1])         # just the 2nd element → 'Article premier'
print(parts[-1])        # → 'Article 2'

print(type(articles))   # <class 'list'>  ← confirms it's a list
print(len(articles))    # how many elements
print(articles[0])      # just the 1st element → {'article_number': '1', 'article_text': '...'}
print(articles[-1])     # → {'article_number': '2', 'article_text': '...'}