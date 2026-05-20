import time
import statistics
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.embeddings import embed
from core.database import search_job_descriptions, search_candidate_profiles
from core.claude import get_negotiation_coaching, get_free_negotiation_coaching
from core.observability import log_request, log_feedback

router = APIRouter(prefix="/negotiate", tags=["negotiate"])


class OfferInput(BaseModel):
    role: str
    company: str
    location: str = "New York, NY"
    salary: int
    years_exp: int
    notes: str = ""
    session_id: str = ""


class NegotiationResponse(BaseModel):
    market_rate: str
    counter_range: str
    negotiation_script: str
    key_points: str
    raw: str
    similar_jds_found: int
    similar_profiles_found: int
    log_id: str = ""


@router.post("", response_model=NegotiationResponse, summary="Get AI salary negotiation coaching")
async def negotiate(offer: OfferInput):
    t0 = time.monotonic()

    query = (
        f"{offer.role} engineer {offer.years_exp} years experience "
        f"{offer.location} salary ${offer.salary:,} {offer.notes}"
    )
    query_embedding = embed(query)

    similar_jds      = search_job_descriptions(query_embedding, limit=5)
    similar_profiles = search_candidate_profiles(query_embedding, limit=3)

    coaching = get_negotiation_coaching(
        offer=offer.model_dump(),
        similar_jds=similar_jds,
        similar_profiles=similar_profiles,
    )

    latency_ms = int((time.monotonic() - t0) * 1000)

    avg_jd_sim = (
        statistics.mean(j["similarity"] for j in similar_jds if "similarity" in j)
        if similar_jds else None
    )
    avg_prof_sim = (
        statistics.mean(p["similarity"] for p in similar_profiles if "similarity" in p)
        if similar_profiles else None
    )

    log_id = log_request(
        endpoint="salary",
        latency_ms=latency_ms,
        response_length=len(coaching.get("raw", "")),
        jds_found=len(similar_jds),
        profiles_found=len(similar_profiles),
        avg_jd_similarity=avg_jd_sim,
        avg_profile_similarity=avg_prof_sim,
        role=offer.role,
        company=offer.company,
        location=offer.location,
        salary=offer.salary,
        years_exp=offer.years_exp,
        session_id=offer.session_id or None,
    ) or ""

    return NegotiationResponse(
        **coaching,
        similar_jds_found=len(similar_jds),
        similar_profiles_found=len(similar_profiles),
        log_id=log_id,
    )


class FreeNegotiateInput(BaseModel):
    situation: str
    session_id: str = ""


class FreeNegotiationResponse(BaseModel):
    strategy: str
    script: str
    tactics: str
    log_id: str = ""


@router.post("/free", response_model=FreeNegotiationResponse, summary="Negotiate anything")
async def negotiate_free(body: FreeNegotiateInput):
    t0 = time.monotonic()

    coaching = get_free_negotiation_coaching(situation=body.situation)

    latency_ms = int((time.monotonic() - t0) * 1000)

    log_id = log_request(
        endpoint="free",
        latency_ms=latency_ms,
        response_length=len(coaching.get("script", "") + coaching.get("strategy", "")),
        session_id=body.session_id or None,
    ) or ""

    return FreeNegotiationResponse(**coaching, log_id=log_id)


class FeedbackInput(BaseModel):
    log_id: str
    rating: int   # 1 = thumbs up, -1 = thumbs down
    comment: str = ""


@router.post("/feedback", summary="Submit feedback on a negotiation response")
async def feedback(body: FeedbackInput):
    if body.rating not in (1, -1):
        raise HTTPException(400, "rating must be 1 or -1")
    ok = log_feedback(body.log_id, body.rating, body.comment or None)
    if not ok:
        raise HTTPException(500, "Failed to save feedback")
    return {"message": "Feedback recorded"}
