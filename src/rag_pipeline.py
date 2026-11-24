import hashlib
import json
import os
import chromadb
import numpy as np
from google import genai
from google.genai import types


def make_job_text(job: dict) -> str:
    skills = ", ".join(job.get("required_skills", []))
    perks = ", ".join(job.get("perks", []))
    return (
        f"Title: {job.get('job_title', '')}\n"
        f"Company: {job.get('company', '')}\n"
        f"Location: {job.get('location', '')}\n"
        f"Job Type: {job.get('job_type', '')}\n"
        f"Experience: {job.get('experience_requirements', '')}\n"
        f"Required Skills: {skills}\n"
        f"Perks: {perks}\n"
        f"Description: {job.get('job_description', '')}"
    )


def _local_fallback_vector(text: str, size: int = 768) -> list[float]:
    vec = np.zeros(size, dtype=np.float32)
    for word in text.lower().split():
        digest = hashlib.sha256(word.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "little") % size
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[idx] += sign
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


class InternshipRAG:
    def __init__(self, db_path: str = "data/chroma_db", collection_name: str = "internships"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

        os.makedirs(db_path, exist_ok=True)
        self.chroma = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.jobs_by_id: dict[str, dict] = {}

    def load_jobs(self, json_path: str = "data/internships.json") -> list[dict]:
        with open(json_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        self.jobs_by_id = {job["job_id"]: job for job in jobs}
        return jobs

    def embed(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        if not texts:
            return []

        if self.client:
            try:
                vectors = []
                batch_size = 25
                for start in range(0, len(texts), batch_size):
                    batch = texts[start : start + batch_size]
                    res = self.client.models.embed_content(
                        model="gemini-embedding-001",
                        contents=batch,
                        config=types.EmbedContentConfig(task_type=task_type),
                    )
                    for item in res.embeddings:
                        vectors.append(list(item.values))
                if len(vectors) == len(texts):
                    return vectors
            except Exception as err:
                print(f"[INFO] Using fallback embeddings because API call failed: {err}")

        return [_local_fallback_vector(t) for t in texts]

    def index_jobs(self, jobs: list[dict], rebuild: bool = False) -> int:
        self.jobs_by_id = {job["job_id"]: job for job in jobs}

        if rebuild and self.collection.count() > 0:
            existing = self.collection.get()
            if existing and existing.get("ids"):
                self.collection.delete(ids=existing["ids"])

        if self.collection.count() >= len(jobs) and not rebuild:
            return self.collection.count()

        ids = [job["job_id"] for job in jobs]
        docs = [make_job_text(job) for job in jobs]
        metas = [
            {
                "job_id": job["job_id"],
                "job_title": job.get("job_title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "skills": ", ".join(job.get("required_skills", [])),
            }
            for job in jobs
        ]
        vectors = self.embed(docs, task_type="RETRIEVAL_DOCUMENT")
        self.collection.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=vectors)
        return len(ids)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        query_vec = self.embed([query], task_type="RETRIEVAL_QUERY")[0]
        results = self.collection.query(
            query_embeddings=[query_vec],
            n_results=top_k,
            include=["metadatas", "distances"],
        )

        matches = []
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        for job_id, dist, meta in zip(ids, distances, metadatas):
            score = round(max(0.0, min(1.0, 1.0 - float(dist))), 4)
            job = self.jobs_by_id.get(job_id, meta)
            matches.append({
                "job_id": job_id,
                "similarity": score,
                "job": job,
            })

        return matches


if __name__ == "__main__":
    rag = InternshipRAG()
    jobs = rag.load_jobs("data/internships.json")
    total = rag.index_jobs(jobs)
    print(f"Indexed {total} internships into ChromaDB.")

    test_query = "Python data science machine learning internship"
    top_hits = rag.search(test_query, top_k=5)
    print(f"\nTop {len(top_hits)} results for: '{test_query}'")
    for i, hit in enumerate(top_hits, start=1):
        j = hit["job"]
        print(f"{i}. {j.get('job_title')} at {j.get('company')} ({j.get('location')}) | similarity={hit['similarity']}")