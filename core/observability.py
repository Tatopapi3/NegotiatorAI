import uuid
from typing import Optional
from core.database import get_client


def log_request(
    endpoint: str,
    latency_ms: int,
    response_length: int,
    jds_found: int = 0,
    profiles_found: int = 0,
    avg_jd_similarity: Optional[float] = None,
    avg_profile_similarity: Optional[float] = None,
    role: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    salary: Optional[int] = None,
    years_exp: Optional[int] = None,
    session_id: Optional[str] = None,
) -> Optional[str]:
    try:
        result = get_client().table("negotiation_logs").insert({
            "session_id":            session_id or str(uuid.uuid4()),
            "endpoint":              endpoint,
            "latency_ms":            latency_ms,
            "response_length":       response_length,
            "jds_found":             jds_found,
            "profiles_found":        profiles_found,
            "avg_jd_similarity":     avg_jd_similarity,
            "avg_profile_similarity": avg_profile_similarity,
            "role":                  role,
            "company":               company,
            "location":              location,
            "salary":                salary,
            "years_exp":             years_exp,
        }).execute()
        return result.data[0]["id"]
    except Exception:
        return None


def log_feedback(log_id: str, rating: int, comment: Optional[str] = None) -> bool:
    try:
        get_client().table("negotiation_feedback").insert({
            "log_id":  log_id,
            "rating":  rating,
            "comment": comment,
        }).execute()
        return True
    except Exception:
        return False


def get_dashboard_stats() -> dict:
    client = get_client()
    try:
        logs = client.table("negotiation_logs").select(
            "id, created_at, endpoint, latency_ms, jds_found, profiles_found, "
            "avg_jd_similarity, role, salary"
        ).order("created_at", desc=True).limit(500).execute().data or []

        feedback = client.table("negotiation_feedback").select(
            "log_id, rating, created_at"
        ).order("created_at", desc=True).limit(500).execute().data or []

        return {"logs": logs, "feedback": feedback}
    except Exception:
        return {"logs": [], "feedback": []}
