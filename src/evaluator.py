from .matching_agent import JobResumeMatcher
from .rag_pipeline import InternshipRAG


STUDENT_PROFILES = [
    {
        "name": "ML & Computer Vision Profile",
        "preferred_role": "Data Science / ML Intern",
        "preferred_location": "Remote",
        "education": "B.E. Computer Engineering",
        "skills": [
            "Python",
            "Pandas",
            "Scikit-learn",
            "TensorFlow",
            "Keras",
            "OpenCV",
            "SQL",
        ],
        "projects": [
            "Home Loan Default Prediction",
            "Rice Leaf Disease Classification",
            "Dog Breed Classifier",
        ],
        "expected_keywords": ["data science", "machine learning", "data engineering", "analyst"],
    },
    {
        "name": "Data Analytics & BI Profile",
        "preferred_role": "Data Analyst Intern",
        "preferred_location": "Remote",
        "education": "B.E. / B.Sc. Data Analytics",
        "skills": [
            "Python",
            "SQL",
            "Data analysis",
            "Data Analytics",
            "Data visualization",
            "Power BI",
        ],
        "projects": [
            "Sales KPI Dashboard",
            "Customer Churn SQL Analysis",
        ],
        "expected_keywords": ["data", "analyst", "analytics", "science"],
    },
    {
        "name": "Software & Backend Profile",
        "preferred_role": "Software / Backend Intern",
        "preferred_location": "Remote",
        "education": "B.E. Information Technology",
        "skills": [
            "Python",
            "Git",
            "APIs",
            "Agile",
            "SQL",
        ],
        "projects": [
            "REST API Service",
            "Workflow Automation Tool",
        ],
        "expected_keywords": ["engineer", "developer", "software", "data"],
    },
]


def run_evaluation(matcher: JobResumeMatcher, top_k: int = 5) -> list[dict]:
    summary_rows: list[dict] = []

    for profile in STUDENT_PROFILES:
        # 1. Run twice to confirm score consistency across repeated runs
        first_run = matcher.match(profile, top_k=top_k)
        second_run = matcher.match(profile, top_k=top_k)

        scores_1 = [r.match_score for r in first_run]
        scores_2 = [r.match_score for r in second_run]
        consistent = scores_1 == scores_2
        properly_ranked = all(
            scores_1[i] >= scores_1[i + 1] for i in range(len(scores_1) - 1)
        )

        # 2. Top-K relevance against expected role keywords
        expected_kw = profile["expected_keywords"]
        relevant_count = sum(
            1
            for r in first_run
            if any(kw in r.job_title.lower() for kw in expected_kw)
        )
        relevance_at_k = round((relevant_count / max(1, len(first_run))) * 100, 1)

        # 3. Skill coverage & explanation completeness
        avg_skill_match = round(
            sum(
                len(r.matched_skills)
                / max(1, len(r.matched_skills) + len(r.missing_skills))
                for r in first_run
            )
            / max(1, len(first_run))
            * 100,
            1,
        )
        valid_explanations = sum(
            1 for r in first_run if len(r.reasoning.strip()) >= 25
        )
        explanation_rate = round(
            (valid_explanations / max(1, len(first_run))) * 100, 1
        )

        top_pick = first_run[0] if first_run else None
        expected_match = bool(
            top_pick
            and any(kw in top_pick.job_title.lower() for kw in expected_kw)
        )

        row = {
            "profile": profile["name"],
            "top_k_relevance_pct": relevance_at_k,
            "avg_skill_coverage_pct": avg_skill_match,
            "score_consistent": consistent,
            "sorted_high_to_low": properly_ranked,
            "explanation_quality_pct": explanation_rate,
            "matches_expected_top_role": expected_match,
            "top_result": (
                f"{top_pick.job_title} @ {top_pick.company} ({top_pick.match_score})"
                if top_pick
                else "None"
            ),
        }
        summary_rows.append(row)

        print(f"=== {profile['name']} ===")
        print(
            f"Top-{top_k} Relevance: {relevance_at_k}% | "
            f"Avg Skill Match: {avg_skill_match}% | "
            f"Consistent: {consistent} | "
            f"Sorted: {properly_ranked} | "
            f"Explanations: {explanation_rate}%"
        )
        print(f"Expected Top Role Match: {expected_match} -> Top #1: {row['top_result']}")
        for r in first_run[:3]:
            print(
                f"  #{r.rank} {r.job_title} @ {r.company} ({r.match_score}) | "
                f"Matched: {r.matched_skills} | Missing: {r.missing_skills}"
            )
        print()

    return summary_rows


if __name__ == "__main__":
    rag = InternshipRAG()
    jobs = rag.load_jobs("data/internships.json")
    rag.index_jobs(jobs)

    matcher = JobResumeMatcher(rag)
    run_evaluation(matcher, top_k=5)