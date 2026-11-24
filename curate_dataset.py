import glob
import json
import os
import pandas as pd


def clean_cell(value) -> str:
    if value is None or pd.isna(value):
        return ""
    text = " ".join(str(value).split()).strip()
    return "" if text.lower() in {"nan", "none", "n/a", ""} else text


def collect_columns(row: pd.Series, prefix: str, max_count: int = 6) -> list[str]:
    items = []
    for i in range(1, max_count + 1):
        val = clean_cell(row.get(f"{prefix} {i}"))
        if val and val not in items:
            items.append(val)
    return items


def curate_internships(
    csv_path: str | None = None,
    output_path: str = "data/internships.json",
    limit: int = 180,
) -> list[dict]:
    if csv_path is None:
        csv_files = glob.glob("data/raw/*.csv")
        if not csv_files:
            raise FileNotFoundError("No CSV file found in data/raw/. Place your downloaded CSV there first.")
        csv_path = csv_files[0]

    df = pd.read_csv(csv_path)
    seen = set()
    curated_jobs = []

    for idx, row in df.iterrows():
        company = clean_cell(row.get("Company"))
        title = clean_cell(row.get("Job Title"))
        location = clean_cell(row.get("Location")) or "Not specified"
        job_type = clean_cell(row.get("Job Type")) or "Internship"
        experience = clean_cell(row.get("Experience")) or "Entry-level"

        # Skip incomplete rows
        if not company or not title:
            continue

        skills = collect_columns(row, "Skill", max_count=6)
        perks = collect_columns(row, "Perk", max_count=6)

        # Skip rows with zero skills listed
        if not skills:
            continue

        # Skip duplicates
        dedup_key = (title.lower(), company.lower(), location.lower())
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        # Build a clean description from available fields so RAG chunking has rich text
        description = (
            f"{title} at {company} ({job_type}, {experience}) in {location}. "
            f"Key skills: {', '.join(skills)}."
        )
        if perks:
            description += f" Perks: {', '.join(perks)}."

        curated_jobs.append({
            "job_id": f"JOB-{len(curated_jobs) + 1:03d}",
            "job_title": title,
            "company": company,
            "location": location,
            "job_type": job_type,
            "experience_requirements": experience,
            "required_skills": skills,
            "perks": perks,
            "job_description": description,
        })

        if len(curated_jobs) >= limit:
            break

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(curated_jobs, f, indent=2)

    print(f"Total rows in raw CSV: {len(df)}")
    print(f"Curated & saved postings: {len(curated_jobs)} -> {output_path}")
    return curated_jobs


if __name__ == "__main__":
    curate_internships(limit=180)