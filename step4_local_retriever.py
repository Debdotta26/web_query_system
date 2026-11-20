"""
STEP 4: Intent-Aware & Entity-Guarded Vector Retrieval Engine
Prevents topic mismatches (e.g. placement vs eligibility) and branch mismatches (e.g. ECE vs CSE).
"""
import os
import re
import math
import json
from collections import Counter
import difflib
import numpy as np
from config import UNSTRUCTURED_DATA_JSON

def tokenize(text):
    if not text:
        return []
    return re.findall(r"[a-zA-Z0-9_]{2,}", text.lower())

ADMISSION_VOCAB = [
    "admission", "admissions", "btech", "b.tech", "mtech", "m.tech", "mca", "bca", "bba", "diploma", "tech",
    "department", "departments", "branch", "branches", "stream", "streams", "program", "programs",
    "seat", "seats", "intake", "capacity", "fee", "fees", "semester", "tuition", "hostel", "uniform",
    "eligibility", "eligible", "cutoff", "percentage", "scholarship", "scholarships", "waiver",
    "placement", "placements", "package", "salary", "recruiter", "recruiters",
    "document", "documents", "certificate", "verification", "principal", "director", "founder", "narula"
]

def normalize_typos(query):
    words = re.findall(r"[a-zA-Z0-9_.]+|[^a-zA-Z0-9_.\s]+", query)
    corrected = []
    for w in words:
        lw = w.lower().strip(".")
        if len(lw) >= 5 and lw.isalpha() and lw not in ADMISSION_VOCAB:
            matches = difflib.get_close_matches(lw, ADMISSION_VOCAB, n=1, cutoff=0.80)
            corrected.append(matches[0] if matches else w)
        else:
            corrected.append(w)
    return " ".join(corrected)

def detect_query_intent(query):
    q = query.lower()

    if any(w in q for w in [
        "placement", "placements", "placed", "salary", "package", "recruiter", 
        "recruiters", "lpa", "highest package", "average package", 
        "placement rate", "placement percentage", "job offer", "job offers"
    ]):
        return "placement"

    if any(w in q for w in [
        "where is", "located", "location", "address", "railway", "station", 
        "metro", "how to reach", "bus route", "transport", "distance",
        "founder", "founded", "who started", "who established", "history",
        "principal", "director", "head of institute", "hod", "head of department",
        "faculty", "professor", "dean", "teacher", "staff", "chairman", "coordinator",
        "club", "clubs", "fest", "fests", "navodaya", "canteen", "sports",
        "gym", "gymnasium", "wifi speed", "dress code", "uniform rules"
    ]):
        return "unlisted_nit_query"

    if any(w in q for w in [
        "difference between", "difference in", "compare", "vs", "versus", 
        "which is better", "job scope", "better job", "career prospects",
        "roadmap", "how to prepare", "attention mechanism", "transformer"
    ]):
        return "comparison_or_advice"

    if any(w in q for w in ["hostel", "mess", "accommodation", "room fee"]):
        return "hostel"

    if any(w in q for w in ["fee", "fees", "cost", "charge", "tuition", "1st sem", "first sem", "annual fee", "total fee"]):
        return "fee"

    if any(w in q for w in [
        "seat", "seats", "intake", "capacity", "how many seats",
        "department", "departments", "branch", "branches", "stream", "streams",
        "program", "programs", "course", "courses"
    ]):
        return "seat"

    if any(w in q for w in ["document", "documents", "certificate", "mark sheet", "marksheet", "admit card", "verification", "reporting"]):
        return "document"

    if any(w in q for w in ["scholarship", "scholarships", "tfw", "waiver", "freeship", "svmcm", "financial aid"]):
        return "scholarship"

    if any(w in q for w in ["eligibility", "eligible", "cutoff", "cut off", "pcm", "qualification", "pass marks"]):
        return "eligibility"
    if ("percentage" in q or "percent" in q) and any(w in q for w in ["marks", "10+2", "12th", "10th", "board", "academic"]):
        return "eligibility"

    return "general"

ENTITY_ALIASES = {
    "cse": ["cse", "computer science and engineering"],
    "aiml": ["aiml", "ai & ml", "ai and machine learning", "artificial intelligence"],
    "it": ["information technology", " it "],
    "ece": ["ece", "electronics and communication", "electronics and communications"],
    "ee": ["electrical engineering", " ee "],
    "ce": ["civil engineering"],
    "me": ["mechanical engineering"],
    "ds": ["data science"],
    "cst": ["cst", "computer science and technology"],
    "csbs": ["csbs", "business systems"],
    "ecs": ["ecs", "electronics and computer science"],
    "mca": ["mca", "master of computer applications"],
    "bca": ["bca", "bachelor of computer applications"],
    "bba": ["bba", "bachelor of business administration"],
    "btech": ["btech", "b.tech"],
    "mtech": ["m.tech", "mtech", "master of technology"],
    "diploma": ["diploma", "polytechnic"],
    "lateral": ["lateral", "jelet", "2nd year"]
}

def detect_query_entities(query):
    q = f" {query.lower()} "
    matched = []
    for entity, aliases in ENTITY_ALIASES.items():
        if any(a in q for a in aliases):
            matched.append(entity)
    return matched

def is_chunk_relevant_to_query(query, chunk):
    """Guards against false positive matches."""
    q = query.lower()
    text = (chunk.get("title", "") + " " + chunk.get("content", "")).lower()

    if any(w in q for w in ["placement", "package", "salary", "recruiter", "lpa"]):
        if not any(w in text for w in ["placement", "package", "salary", "recruiter", "lpa", "placed", "offers"]):
            return False

    if any(w in q for w in ["location", "located", "where", "railway", "station", "metro", "reach"]):
        if not any(w in text for w in ["located", "address", "railway", "station", "metro", "nilgunj", "agarpara"]):
            return False

    if any(w in q for w in ["fee", "fees", "cost", "tuition"]):
        if not any(w in text for w in ["₹", "rs.", "fee", "fees", "payment", "cost"]):
            return False

    if any(w in q for w in ["seat", "seats", "intake"]):
        if not any(w in text for w in ["seats", "intake", "approved"]):
            return False

    if any(w in q for w in ["document", "documents", "certificate"]):
        if not any(w in text for w in ["document", "documents", "certificate", "checklist"]):
            return False

    return True

class LocalRetriever:
    def __init__(self, json_path=UNSTRUCTURED_DATA_JSON):
        self.json_path = json_path
        self.chunks = []
        self.use_transformer = False
        self.model = None
        self.chunk_embeddings = None
        self.vocabulary = {}
        self.idf = {}
        self.tfidf_matrix = None
        
        self._init_models()
        self.load_and_index()

    def _init_models(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.use_transformer = True
        except ImportError:
            self.use_transformer = False

    def load_and_index(self):
        if not os.path.exists(self.json_path):
            return

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.chunks = data.get("chunks", [])

        if not self.chunks:
            return

        corpus_texts = [f"{c.get('title', '')} {c.get('content', '')}" for c in self.chunks]

        if self.use_transformer and self.model:
            embeddings = self.model.encode(corpus_texts, show_progress_bar=False, normalize_embeddings=True)
            self.chunk_embeddings = np.array(embeddings)
        else:
            self._build_tfidf(corpus_texts)

    def _build_tfidf(self, corpus_texts):
        doc_count = len(corpus_texts)
        df = Counter()
        tokenized_docs = []
        for text in corpus_texts:
            tokens = set(tokenize(text))
            tokenized_docs.append(tokenize(text))
            for t in tokens:
                df[t] += 1

        self.vocabulary = {t: idx for idx, (t, f) in enumerate(df.items()) if f >= 1}
        vocab_size = len(self.vocabulary)
        self.idf = np.zeros(vocab_size)
        for term, idx in self.vocabulary.items():
            self.idf[idx] = math.log(1.0 + (doc_count / (df[term] + 0.5))) + 1.0

        matrix = np.zeros((doc_count, vocab_size), dtype=np.float32)
        for doc_id, tokens in enumerate(tokenized_docs):
            tf = Counter(tokens)
            for token, count in tf.items():
                if token in self.vocabulary:
                    col = self.vocabulary[token]
                    matrix[doc_id, col] = (1.0 + math.log(count)) * self.idf[col]

        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.tfidf_matrix = matrix / norms

    def search(self, query, top_k=3):
        if not self.chunks:
            return []

        query = normalize_typos(query)
        query_intent = detect_query_intent(query)
        query_entities = detect_query_entities(query)

        if query_intent in ["unlisted_nit_query", "comparison_or_advice"]:
            return [{
                "chunk": self.chunks[0],
                "score": 0.10,
                "raw_score": 0.10,
                "is_relevant": False
            }]

        if self.use_transformer and self.model and self.chunk_embeddings is not None:
            query_vec = self.model.encode([query], normalize_embeddings=True)[0]
            raw_scores = np.dot(self.chunk_embeddings, query_vec)
        elif self.tfidf_matrix is not None:
            q_tokens = tokenize(query)
            if not q_tokens:
                return []
            q_vec = np.zeros(len(self.vocabulary), dtype=np.float32)
            tf = Counter(q_tokens)
            for t, cnt in tf.items():
                if t in self.vocabulary:
                    col = self.vocabulary[t]
                    q_vec[col] = (1.0 + math.log(cnt)) * self.idf[col]
            norm = np.linalg.norm(q_vec)
            if norm > 0:
                q_vec = q_vec / norm
                raw_scores = np.dot(self.tfidf_matrix, q_vec)
            else:
                raw_scores = np.zeros(len(self.chunks))
        else:
            return []

        final_scores = np.copy(raw_scores)
        for idx, chunk in enumerate(self.chunks):
            chunk_intent = chunk.get("intent", "")
            chunk_text = f" {(chunk.get('title', '') + ' ' + chunk.get('content', '')).lower()} "

            if query_intent != "general":
                if chunk_intent == query_intent:
                    final_scores[idx] += 0.25
                elif query_intent in ["fee", "hostel"] and chunk_intent == "seat":
                    final_scores[idx] -= 0.30
                elif query_intent == "seat" and chunk_intent in ["fee", "hostel", "lateral_fee"]:
                    final_scores[idx] -= 0.30
                elif query_intent == "placement" and chunk_intent != "placement":
                    final_scores[idx] -= 0.30

            if any(w in query.lower() for w in ["department", "departments", "branches", "streams", "all programs", "courses offered"]) and not query_entities:
                if chunk.get("category") in ["departments_overview", "seat_matrix_overview"]:
                    final_scores[idx] += 0.30

            if query_entities:
                for ent in query_entities:
                    if any(alias in chunk_text for alias in ENTITY_ALIASES[ent]):
                        final_scores[idx] += 0.20
                title_lower = chunk.get('title', '').lower()
                if 'cse' in query_entities and 'ds' not in query_entities and 'csbs' not in query_entities:
                    if 'data science' in title_lower or 'business systems' in title_lower:
                        final_scores[idx] -= 0.25
                if 'btech' in query_entities and 'mtech' not in query_entities and 'lateral' not in query_entities:
                    if 'm.tech' in title_lower or 'lateral' in title_lower:
                        final_scores[idx] -= 0.30
                if 'lateral' in query_entities and 'lateral' not in title_lower:
                    final_scores[idx] -= 0.30

        top_indices = np.argsort(final_scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            chunk_item = self.chunks[idx]
            relevant = is_chunk_relevant_to_query(query, chunk_item)
            results.append({
                "chunk": chunk_item,
                "score": float(final_scores[idx]) if relevant else 0.20,
                "raw_score": float(raw_scores[idx]),
                "is_relevant": relevant
            })
        return results
