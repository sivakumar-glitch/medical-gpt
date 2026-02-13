import pandas as pd

from .rag_service import rag_service

DATASET_PATH = "medDataset_processed.csv"


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def evaluate_top1_accuracy():
    df = pd.read_csv(DATASET_PATH)
    df.fillna("", inplace=True)

    total = len(df)
    hits = 0

    for _, row in df.iterrows():
        query = str(row.get("Question", ""))
        expected = _normalize(str(row.get("Answer", "")))

        results = rag_service.retrieve(query, k=1, mode="hybrid")
        if not results:
            continue

        top_meta = results[0].get("metadata", {})
        got = _normalize(str(top_meta.get("answer", "")))
        if got == expected:
            hits += 1

    accuracy = hits / total if total else 0.0
    print(f"Top-1 accuracy: {accuracy:.4f} ({hits}/{total})")


if __name__ == "__main__":
    evaluate_top1_accuracy()
