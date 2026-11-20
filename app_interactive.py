"""
Interactive Terminal Assistant for NIT Admission Inquiries
With 3-tier routing: Local Data, NIT College API, and General Knowledge API.
"""

from step5_hybrid_qa_engine import HybridAdmissionQA

def main():
    print("=" * 70)
    print("🎓 NARULA INSTITUTE OF TECHNOLOGY (NIT) - SMART ADMISSION ASSISTANT")
    print("=" * 70)
    print("• Tier 1 [GREEN] : Official admission web page data (Fees, Seats, Docs) [$0.00]")
    print("• Tier 2 [BLUE]  : Unlisted NIT college queries (Founder, History, Campus) [API]")
    print("• Tier 3 [YELLOW]: Out-of-domain general knowledge (Coding, Science)     [API]")
    print("• Type 'stats' for metrics, or 'exit' / 'quit' to close.")
    print("=" * 70)

    bot = HybridAdmissionQA()

    while True:
        try:
            q = input("\n👉 Ask Query: ").strip()
            if not q:
                continue
            if q.lower() in ["exit", "quit", "q"]:
                print("\nThank you for using the NIT Admission Assistant! 👋")
                break
            if q.lower() == "stats":
                s = bot.stats
                print("\n📊 --- REAL-TIME COST & ROUTING ANALYTICS ---")
                print(f"Total Student Queries        : {s['total_queries']}")
                print(f"Tier 1: Answered Locally ($0): {s['local_hits']}")
                print(f"Tier 2: NIT-Specific via API : {s.get('nit_api_fallbacks', 0)}")
                print(f"Tier 3: Out-of-Domain via API: {s.get('general_api_fallbacks', 0)}")
                pct = round((s['local_hits'] / max(1, s['total_queries'])) * 100, 1)
                print(f"Local Cost Reduction Rate    : {pct}%")
                print("---------------------------------------------")
                continue

            res = bot.ask(q)
            status = res["status"]

            if status == "LOCAL_WEBSITE_HIT":
                print(f"\n✅ [TIER 1: LOCAL ADMISSION SITE] | Cost: {res['cost']} | Score: {res['confidence_score']}")
                print(f"📌 Section: {res['citation']['title']}")
                print("-" * 70)
                print(res["answer"])

            elif status == "NIT_SPECIFIC_API_FALLBACK":
                print(f"\n🏛️ [TIER 2: NIT COLLEGE API] | Cost: {res['cost']} | Score: {res['confidence_score']}")
                print(f"📌 Context: Verified Information regarding Narula Institute of Technology")
                print("-" * 70)
                print(res["answer"])

            else:
                print(f"\n🌐 [TIER 3: GENERAL KNOWLEDGE API] | Cost: {res['cost']} | Score: {res['confidence_score']}")
                print(f"📌 Notice: Query is outside college scope. Answered via Gemini General Knowledge.")
                print("-" * 70)
                print(res["answer"])

        except (KeyboardInterrupt, EOFError):
            print("\nExiting session...")
            break

if __name__ == "__main__":
    main()
