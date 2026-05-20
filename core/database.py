from typing import Optional
from supabase import create_client, Client
from core.config import SUPABASE_URL, SUPABASE_KEY

_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_client() -> Client:
    return _client


def insert_job_description(title: str, company: str, location: str,
                           salary_min: Optional[int], salary_max: Optional[int],
                           content: str, embedding: list[float]) -> dict:
    result = _client.table("job_descriptions").insert({
        "title": title,
        "company": company,
        "location": location,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "content": content,
        "embedding": embedding,
    }).execute()
    return result.data[0]


def insert_candidate_profile(name: Optional[str], title: str, years_exp: int,
                              skills: list[str], content: str,
                              embedding: list[float]) -> dict:
    result = _client.table("candidate_profiles").insert({
        "name": name,
        "title": title,
        "years_exp": years_exp,
        "skills": skills,
        "content": content,
        "embedding": embedding,
    }).execute()
    return result.data[0]


def search_job_descriptions(query_embedding: list[float], limit: int = 5) -> list[dict]:
    result = _client.rpc("match_job_descriptions", {
        "query_embedding": query_embedding,
        "match_count": limit,
    }).execute()
    return result.data or []


def search_candidate_profiles(query_embedding: list[float], limit: int = 3) -> list[dict]:
    result = _client.rpc("match_candidate_profiles", {
        "query_embedding": query_embedding,
        "match_count": limit,
    }).execute()
    return result.data or []
