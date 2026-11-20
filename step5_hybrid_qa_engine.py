"""
STEP 5: Auto-Adapting Hybrid QA Engine with Real-Time Token Tracking
"""
import os
import json
import requests
from datetime import datetime
from config import DEFAULT_CONFIDENCE_THRESHOLD, GEMINI_API_KEY, GEMINI_MODEL, AUDIT_LOG_JSON
from step4_local_retriever import LocalRetriever

NIT_KEYWORDS = [
    "nit", "narula", "institute", "agarpara", "jis", "founder", 
    "principal", "director", "faculty", "hod", "campus", "canteen", 
    "library", "clubs", "fest", "navodaya", "tech fest", "hostel warden",
    "bus route", "transport", "ragging committee", "affiliation", "makaut",
    "autonomous", "accreditation", "history", "established", "location", "address"
]

def is_gibberish(query):
    """Detects random keyboard mash (e.g. hhjstiihth) or non-meaningful inputs so we do not waste an API call."""
    import re
    q = query.strip()
    words = re.findall(r"[a-zA-Z]{2,}", q)
    if not words:
        return True
    if len(words) == 1 and len(words[0]) >= 5:
        w = words[0].lower()
        vowels = sum(1 for ch in w if ch in "aeiou")
        if vowels / len(w) < 0.25 or re.search(r"[bcdfghjklmnpqrstvwxyz]{5,}", w):
            return True
    if len(words) == 1 and re.search(r"[bcdfghjklmnpqrstvwxyz]{5,}", words[0].lower()):
        return True
    return False

def is_nit_related(query):
    q = query.lower()
    return any(k in q for k in NIT_KEYWORDS)

class HybridAdmissionQA:
    def __init__(self, threshold=None, api_key=None):
        self.retriever = LocalRetriever()
        
        if threshold is not None:
            self.threshold = threshold
        elif self.retriever.use_transformer:
            self.threshold = 0.58
        else:
            self.threshold = 0.28
            
        self.api_key = api_key or GEMINI_API_KEY
        self.active_model = GEMINI_MODEL
        self.active_api_version = "v1beta"
        
        self._auto_detect_model()

        self.stats = {
            "total_queries": 0, 
            "local_hits": 0, 
            "nit_api_fallbacks": 0, 
            "general_api_fallbacks": 0,
            "total_prompt_tokens": 0,
            "total_output_tokens": 0,
            "total_api_tokens": 0
        }
        self._load_stats()

    def _auto_detect_model(self):
        if not self.api_key:
            return

        candidate_versions = ["v1beta", "v1"]
        for ver in candidate_versions:
            try:
                list_url = f"https://generativelanguage.googleapis.com/{ver}/models?key={self.api_key}"
                resp = requests.get(list_url, timeout=5)
                if resp.status_code == 200:
                    models_data = resp.json().get("models", [])
                    available_names = [
                        m["name"].replace("models/", "") 
                        for m in models_data 
                        if "generateContent" in m.get("supportedGenerationMethods", [])
                    ]
                    # Respect explicit GEMINI_MODEL env var first if available
                    env_model = os.environ.get("GEMINI_MODEL", "").strip()
                    if env_model and env_model in available_names:
                        self.active_model = env_model
                        self.active_api_version = ver
                        return
                    for pref in ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-3.1-flash-lite", "gemma-4-26b-a4b-it", "gemini-3.5-flash"]:
                        for avail in available_names:
                            if pref == avail:
                                self.active_model = avail
                                self.active_api_version = ver
                                return
            except Exception:
                pass

    def _load_stats(self):
        if os.path.exists(AUDIT_LOG_JSON):
            try:
                with open(AUDIT_LOG_JSON, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    loaded = data.get("summary", {})
                    for k in self.stats:
                        if k in loaded:
                            self.stats[k] = loaded[k]
            except Exception:
                pass

    def _save_log(self, record):
        logs = []
        if os.path.exists(AUDIT_LOG_JSON):
            try:
                with open(AUDIT_LOG_JSON, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logs = data.get("logs", [])
            except Exception:
                logs = []
        logs.append(record)
        summary = {
            "total_queries": self.stats["total_queries"],
            "local_hits": self.stats["local_hits"],
            "nit_api_fallbacks": self.stats.get("nit_api_fallbacks", 0),
            "general_api_fallbacks": self.stats.get("general_api_fallbacks", 0),
            "cost_savings_pct": round((self.stats["local_hits"] / max(1, self.stats["total_queries"])) * 100, 1),
            "total_prompt_tokens": self.stats.get("total_prompt_tokens", 0),
            "total_output_tokens": self.stats.get("total_output_tokens", 0),
            "total_api_tokens": self.stats.get("total_api_tokens", 0)
        }
        with open(AUDIT_LOG_JSON, "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "logs": logs}, f, indent=4)

    def _call_gemini_api(self, query, routing_tier="nit_specific"):
        empty_tokens = {"prompt_tokens": 0, "output_tokens": 0, "thoughts_tokens": 0, "total_tokens": 0}
        if not self.api_key:
            msg = (
                "[Gemini API Standby Mode]\n"
                "API key not detected. Set your key in PowerShell using:\n"
                "  $env:GEMINI_API_KEY='your_actual_key'"
            )
            return msg, empty_tokens

        if routing_tier == "nit_specific":
            system_prompt = (
                "You are the official student guidance counselor for Narula Institute of Technology (NIT Agarpara, Kolkata, under MAKAUT and JIS Group).\n\n"
                "OFFICIAL INSTITUTIONAL RECORDS & LEADERSHIP:\n"
                "- Institution: Narula Institute of Technology (NIT)\n"
                "- Principal: Prof. (Dr.) Subhram Das\n"
                "- Director: Sardar Simarpreet Singh\n"
                "- Founder / Founding Chairman: Late Sardar Jodh Singh (JIS Group)\n"
                "- Campus Location: 81, Nilgunj Road, Agarpara, Kolkata, West Bengal 700109\n"
                "- Nearest Transit: Agarpara Railway Station (1.5 km, Sealdah North section), Noapara / Dakshineswar Metro\n"
                "- Affiliation & Status: Autonomous Institute affiliated to MAKAUT, approved by AICTE, NAAC 'A' Accredited, NBA Accredited, NIRF Ranked\n\n"
                "INSTRUCTION: Answer the student's question accurately, professionally, and concisely using the official records above. Do not invent, substitute, or guess leadership names.\n\n"
                f"Student Question: {query}"
            )
        else:
            system_prompt = (
                "You are an academic and technical AI assistant. A student asked a general, out-of-domain question that is outside the scope of Narula Institute of Technology admissions. "
                "Provide a clear, detailed, and complete answer to their question.\n\n"
                f"Student Question: {query}"
            )

        models_to_try = [
            (self.active_api_version, self.active_model),
            ("v1beta", "gemini-2.5-flash-lite"),
            ("v1beta", "gemini-3.5-flash-lite"),
            ("v1beta", "gemini-3.1-flash-lite"),
            ("v1", "gemini-2.5-flash"),
            ("v1beta", "gemma-4-26b-a4b-it"),
            ("v1beta", "gemini-3.5-flash")
        ]

        payload = {
            "contents": [{"parts": [{"text": system_prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1024,
                "thinkingConfig": {
                    "thinkingBudget": 128
                }
            }
        }
        headers = {"Content-Type": "application/json"}

        last_error = "No endpoints attempted."
        seen = set()
        for ver, mod in models_to_try:
            if (ver, mod) in seen:
                continue
            seen.add((ver, mod))
            url = f"https://generativelanguage.googleapis.com/{ver}/models/{mod}:generateContent?key={self.api_key}"
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=45)
                if resp.status_code == 200:
                    self.active_api_version = ver
                    self.active_model = mod
                    data = resp.json()
                    
                    usage = data.get("usageMetadata", {})
                    token_info = {
                        "prompt_tokens": usage.get("promptTokenCount", 0),
                        "output_tokens": usage.get("candidatesTokenCount", 0),
                        "thoughts_tokens": usage.get("thoughtsTokenCount", 0),
                        "total_tokens": usage.get("totalTokenCount", 0)
                    }
                    
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip(), token_info
                    last_error = f"{ver}/{mod} returned 200 but empty candidates."
                else:
                    last_error = f"{ver}/{mod} HTTP {resp.status_code}: {resp.text[:250]}"
                    if resp.status_code in (400, 401, 403):
                        break
            except Exception as e:
                last_error = f"{ver}/{mod} error: {e}"
                continue

        return f"Gemini API could not generate a response. Details: {last_error}", empty_tokens

    def ask(self, query):
        self.stats["total_queries"] += 1
        if is_gibberish(query):
            token_info = {"prompt_tokens": 0, "output_tokens": 0, "thoughts_tokens": 0, "total_tokens": 0}
            res = {
                "query": query,
                "status": "LOCAL_WEBSITE_HIT",
                "cost": "$0.00 (Input Guard - No API call)",
                "confidence_score": 0.0,
                "threshold": self.threshold,
                "tokens": token_info,
                "answer": (
                    "I could not understand that query. Please ask a valid question about "
                    "Narula Institute of Technology (e.g., fees, seats, departments, eligibility, placements, or campus info)."
                ),
                "citation": {
                    "source": "Local Input Validation Guard",
                    "title": "Invalid / Unrecognized Query",
                    "category": "input_guard"
                }
            }
            self.stats["local_hits"] += 1
            self._save_log({
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "status": res["status"],
                "score": 0.0,
                "tokens": token_info
            })
            return res

        results = self.retriever.search(query, top_k=3)
        top_match = results[0] if results else None
        top_score = top_match["score"] if top_match else 0.0

        if top_score >= self.threshold and top_match:
            self.stats["local_hits"] += 1
            chunk = top_match["chunk"]
            token_info = {"prompt_tokens": 0, "output_tokens": 0, "thoughts_tokens": 0, "total_tokens": 0}
            res = {
                "query": query,
                "status": "LOCAL_WEBSITE_HIT",
                "cost": "$0.00 (Zero API cost)",
                "confidence_score": round(top_score, 4),
                "threshold": self.threshold,
                "tokens": token_info,
                "answer": chunk.get("content", ""),
                "citation": {
                    "source": "Narula Institute of Technology Admission Portal",
                    "title": chunk.get("title", ""),
                    "category": chunk.get("category", "")
                }
            }
        else:
            if is_nit_related(query):
                self.stats["nit_api_fallbacks"] = self.stats.get("nit_api_fallbacks", 0) + 1
                api_answer, token_info = self._call_gemini_api(query, routing_tier="nit_specific")
                res = {
                    "query": query,
                    "status": "NIT_SPECIFIC_API_FALLBACK",
                    "cost": "1 Gemini API Request",
                    "confidence_score": round(top_score, 4),
                    "threshold": self.threshold,
                    "tokens": token_info,
                    "answer": api_answer,
                    "citation": {
                        "source": f"Narula Institute of Technology Knowledge Base (via Gemini {self.active_model})",
                        "title": "College Institutional Context",
                        "category": "nit_institutional_info"
                    }
                }
            else:
                self.stats["general_api_fallbacks"] = self.stats.get("general_api_fallbacks", 0) + 1
                api_answer, token_info = self._call_gemini_api(query, routing_tier="general_domain")
                res = {
                    "query": query,
                    "status": "GENERAL_OUT_OF_DOMAIN_API",
                    "cost": "1 Gemini API Request",
                    "confidence_score": round(top_score, 4),
                    "threshold": self.threshold,
                    "tokens": token_info,
                    "answer": api_answer,
                    "citation": {
                        "source": f"Google Gemini ({self.active_model})",
                        "title": "General Knowledge (Outside College Scope)",
                        "category": "out_of_domain"
                    }
                }

            self.stats["total_prompt_tokens"] = self.stats.get("total_prompt_tokens", 0) + token_info["prompt_tokens"]
            self.stats["total_output_tokens"] = self.stats.get("total_output_tokens", 0) + token_info["output_tokens"]
            self.stats["total_api_tokens"] = self.stats.get("total_api_tokens", 0) + token_info["total_tokens"]

        self._save_log({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "status": res["status"],
            "score": res["confidence_score"],
            "tokens": res["tokens"]
        })
        return res
