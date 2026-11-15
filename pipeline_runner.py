"""
Pipeline Runner
"""
import sys
import os

def run_pipeline():
    print("\n" + "=" * 70)
    print("🚀 EXECUTING COMPLETE NIT ADMISSION QA PIPELINE")
    print("=" * 70)

    import step1_admission_page_scraper
    if hasattr(step1_admission_page_scraper, "scrape_full_admission_portal"):
        step1_admission_page_scraper.scrape_full_admission_portal()
    else:
        step1_admission_page_scraper.scrape_nit_admission_page()

    import step2_pdf_parser
    step2_pdf_parser.parse_all_pdfs()

    import step3_build_unstructured_json
    step3_build_unstructured_json.build_knowledge_base()

    from step4_local_retriever import LocalRetriever
    retriever = LocalRetriever()
    print(f"Retriever indexed {len(retriever.chunks)} chunks.")

    from step5_hybrid_qa_engine import HybridAdmissionQA
    bot = HybridAdmissionQA()

    test_queries = [
        "What is the overall placement percentage at Narula Institute of Technology?",
        "What is the 1st semester fee for B.Tech Computer Science and Engineering?",
        "How many seats are there in Computer Science and Engineering CSE?"
    ]

    for q in test_queries:
        res = bot.ask(q)
        print(f"\nQuery: '{q}'")
        print(f"Decision: [{res['status']}] | Score: {res['confidence_score']}")
        print(f"Section: {res['citation']['title']}")
        print(f"Answer:\n{res['answer'][:180]}...")

    print("\n" + "=" * 70)
    print("✅ PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_pipeline()
