import json
from typing import List, Dict


def load_dataset(path: str) -> List[Dict]:
    with open(path, "r") as f:
        return [json.loads(line) for line in f]


def simple_score(expected: str, actual: str) -> float:
    expected_words = set(expected.lower().split())
    actual_words = set(actual.lower().split())

    if not expected_words:
        return 0.0

    overlap = len(expected_words & actual_words)
    return overlap / len(expected_words)


class RAGEvaluator:
    def __init__(self, rag_engine):
        self.rag = rag_engine

    def run(self, dataset_path: str):
        data = load_dataset(dataset_path)

        results = []
        total_score = 0.0

        for item in data:
            query = item["query"]
            expected = item["expected"]

            response = self.rag.query(query)
            answer = response["answer"]

            score = simple_score(expected, answer)

            results.append({
                "id": item["id"],
                "query": query,
                "expected": expected,
                "answer": answer,
                "score": score
            })

            total_score += score

        return {
            "avg_score": total_score / len(data),
            "results": results
        }