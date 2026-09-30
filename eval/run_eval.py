import json
import sys
import time
from pathlib import Path
from typing import Dict, List

# Ensure backend modules can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from langchain_community.vectorstores import FAISS
from app.services.embeddings import get_embedding_model
from app.services.ingestion import chunk_document_pages, parse_pdf_pages


def run_evaluation():
    pdf_path = Path(__file__).resolve().parent / "sample.pdf"
    qa_path = Path(__file__).resolve().parent / "qa_pairs.json"
    results_path = Path(__file__).resolve().parent / "results.json"

    if not pdf_path.exists():
        raise FileNotFoundError(f"Sample PDF not found at {pdf_path}")
    if not qa_path.exists():
        raise FileNotFoundError(f"QA pairs not found at {qa_path}")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    pages = parse_pdf_pages(pdf_bytes)

    with open(qa_path, "r", encoding="utf-8") as f:
        qa_pairs = json.load(f)

    total_questions = len(qa_pairs)
    print("=" * 80)
    print(f"DocuMind Retrieval Evaluation Benchmark ({total_questions} Questions, {len(pages)} Pages)")
    print("=" * 80)

    embedding_model = get_embedding_model()

    configurations = [
        {"chunk_size": 500, "chunk_overlap": 100, "label": "Small Chunks (500)"},
        {"chunk_size": 800, "chunk_overlap": 150, "label": "Baseline Chunks (800)"},
        {"chunk_size": 1200, "chunk_overlap": 200, "label": "Large Chunks (1200)"},
    ]

    all_metrics = []

    for cfg in configurations:
        chunk_size = cfg["chunk_size"]
        overlap = cfg["chunk_overlap"]

        # Chunk the document with current parameters
        chunks = chunk_document_pages(
            pages=pages,
            document_id="eval-doc",
            filename="sample.pdf",
            chunk_size=chunk_size,
            chunk_overlap=overlap,
        )

        # Build FAISS index for this configuration
        vector_store = FAISS.from_documents(chunks, embedding_model)

        hits_at_1 = 0
        hits_at_5 = 0
        reciprocal_ranks = []
        latencies = []

        for item in qa_pairs:
            q = item["question"]
            target_page = item["target_page"]

            start_t = time.perf_counter()
            retrieved = vector_store.max_marginal_relevance_search(q, k=5, fetch_k=15)
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            latencies.append(elapsed_ms)

            retrieved_pages = [doc.metadata.get("page") for doc in retrieved]

            # Check Hit@1
            if retrieved_pages and retrieved_pages[0] == target_page:
                hits_at_1 += 1

            # Check Hit@5
            if target_page in retrieved_pages:
                hits_at_5 += 1
                rank = retrieved_pages.index(target_page) + 1
                reciprocal_ranks.append(1.0 / rank)
            else:
                reciprocal_ranks.append(0.0)

        hit_rate_at_1 = (hits_at_1 / total_questions) * 100.0
        hit_rate_at_5 = (hits_at_5 / total_questions) * 100.0
        mrr = sum(reciprocal_ranks) / total_questions
        avg_latency = sum(latencies) / total_questions

        metric_record = {
            "chunk_size": chunk_size,
            "chunk_overlap": overlap,
            "chunk_count": len(chunks),
            "hit_at_1": round(hit_rate_at_1, 1),
            "hit_rate": round(hit_rate_at_5, 1),
            "mrr": round(mrr, 4),
            "avg_latency_ms": round(avg_latency, 2),
        }
        all_metrics.append(metric_record)

    # Determine best configuration
    best_config = max(all_metrics, key=lambda m: (m["hit_rate"], m["mrr"], -m["avg_latency_ms"]))

    # Print Formatted Markdown Table
    print("\nBenchmark Results Table:")
    print("-" * 85)
    print(f"| {'Chunk Size':<12} | {'Overlap':<9} | {'Chunks':<8} | {'Hit@1 (%)':<11} | {'Hit@5 (%)':<11} | {'MRR':<8} | {'Latency (ms)':<14} |")
    print("|" + "-" * 14 + "|" + "-" * 11 + "|" + "-" * 10 + "|" + "-" * 13 + "|" + "-" * 13 + "|" + "-" * 10 + "|" + "-" * 16 + "|")
    for m in all_metrics:
        is_best = " * BEST" if m["chunk_size"] == best_config["chunk_size"] else ""
        print(
            f"| {m['chunk_size']:<12} | {m['chunk_overlap']:<9} | {m['chunk_count']:<8} | "
            f"{m['hit_at_1']:<11.1f} | {m['hit_rate']:<11.1f} | {m['mrr']:<8.4f} | {m['avg_latency_ms']:<14.2f} |{is_best}"
        )
    print("-" * 85)

    print(f"\nConclusion: Chunk size {best_config['chunk_size']} achieved the highest retrieval performance")
    print(f"with a Hit@5 of {best_config['hit_rate']}% and Mean Reciprocal Rank (MRR) of {best_config['mrr']}.")

    # Save real measured numbers for README and resume citation
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "best_chunk_size": best_config["chunk_size"],
                "total_questions": total_questions,
                "metrics": all_metrics,
            },
            f,
            indent=2,
        )
    print(f"\nSaved raw measured evaluation data to: {results_path}")


if __name__ == "__main__":
    run_evaluation()
