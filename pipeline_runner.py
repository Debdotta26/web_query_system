"""
Master Pipeline Runner for NIT Admission QA System
Executes:
1. Admission Page & Tab Scraping
2. PDF Text Extraction
3. Unstructured Knowledge Base Assembly
4. Local Vector Search Verification
5. Real test benchmark queries across seats, fees, eligibility, and out-of-scope questions
"""

import sys
import os

def run_pipeline():
    print("\n" + "=" * 70)
    print("🚀 EXECUTING COMPLETE NIT ADMISSION QA PIPELINE")
    print("=" * 70)

    # 1. Scrape Admission Page
    print("\n[STEP 1/5] Scraping NIT Admission Portal & Program Tabs...")
    import step1_admission_page_scraper
    if hasattr(step1_admission_page_scraper, "scrape_full_admission_portal"):
        step1_admission_page_scraper.scrape_full_admission_portal()
    else:
        step1_admission_page_scraper.scrape_nit_admission_page()

    # 2. Extract PDF Text
    print("\n[STEP 2/5] Parsing Downloaded Brochure / Prospectus PDFs...")
    import step2_pdf_parser
    step2_pdf_parser.parse_all_pdfs()

    # 3. Build Unstructured Knowledge Base
    print("\n[STEP 3/5] Compiling Unstructured Admission Data JSON...")
    import step3_build_unstructured_json
    step3_build_unstructured_json.build_knowledge_base()

    # 4. Initialize Local Retriever
    print("\n[STEP 4/5] Initializing Vector Search Retriever...")
    from step4_local_retriever import LocalRetriever
    retriever = LocalRetriever()
    print(f"Retriever indexed {len(retriever.chunks)} admission chunks.")

    # 5. Run Verification Benchmark
    print("\n[STEP 5/5] Running Verification Benchmark on Real Queries...")
    from step5_hybrid_qa_engine import HybridAdmissionQA
    bot = HybridAdmissionQA()

    test_queries = [
        "What is the 1st semester fee for B.Tech Computer Science and Engineering?",
        "What is the hostel fee at Narula?",
        "How many seats are there in Computer Science and Engineering CSE?",
        "What is the difference between Computer Science Engineering and Information Technology?"
    ]

    for q in test_queries:
        res = bot.ask(q)
        print(f"\nQuery: '{q}'")
        print(f"Decision: [{res['status']}] | Cost: {res['cost']} | Score: {res['confidence_score']}")
        print(f"Answer Preview:\n{res['answer'][:180]}...")

    print("\n" + "=" * 70)
    print("✅ PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print(f"Analytics Summary: {bot.stats}")
    print("=" * 70)

if __name__ == "__main__":
    run_pipeline()
