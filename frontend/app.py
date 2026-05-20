import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="NegotiateIQ", page_icon="💼", layout="centered")

st.markdown("""
<style>
    .main { max-width: 720px; }
    .stTextArea textarea { font-size: 14px; }
</style>
""", unsafe_allow_html=True)

st.title("💼 NegotiateIQ")
st.caption("AI salary negotiation coach powered by Claude + real market data")

tab_negotiate, tab_free, tab_ingest, tab_obs = st.tabs([
    "💰 Salary Negotiation", "🧠 Negotiate Anything", "📥 Ingest Data", "📊 Observability"
])


def feedback_buttons(log_id: str, key_prefix: str):
    if not log_id:
        return
    st.markdown("**Was this advice helpful?**")
    c1, c2, _ = st.columns([1, 1, 6])
    with c1:
        if st.button("👍", key=f"{key_prefix}_up"):
            requests.post(f"{API_URL}/negotiate/feedback",
                          json={"log_id": log_id, "rating": 1}, timeout=5)
            st.success("Thanks!")
    with c2:
        if st.button("👎", key=f"{key_prefix}_down"):
            requests.post(f"{API_URL}/negotiate/feedback",
                          json={"log_id": log_id, "rating": -1}, timeout=5)
            st.info("Noted — we'll improve.")


# ── Tab 1: Salary Negotiation ──────────────────────────────────────────────────
with tab_negotiate:
    st.subheader("Get your negotiation playbook")
    st.caption("We'll pull real market comps from our database and have Claude coach you.")

    col1, col2 = st.columns(2)
    with col1:
        role      = st.text_input("Job Title", placeholder="Senior Software Engineer")
        company   = st.text_input("Company", placeholder="Acme Corp")
        location  = st.text_input("Location", value="New York, NY")
    with col2:
        salary    = st.number_input("Offered Salary ($)", min_value=50000, max_value=1000000,
                                     value=150000, step=5000)
        years_exp = st.number_input("Your Years of Experience", min_value=0, max_value=40, value=3)

    notes = st.text_area("Additional context (optional)",
                          placeholder="e.g. I have a competing offer from Stripe for $175k. "
                                      "I'm currently at $140k. The role is fully remote.",
                          height=80)

    if st.button("🚀 Get My Negotiation Coaching", type="primary", use_container_width=True):
        if not role or not company:
            st.warning("Please fill in at least the job title and company.")
        else:
            with st.spinner("Pulling market comps and generating your playbook..."):
                try:
                    res = requests.post(f"{API_URL}/negotiate", json={
                        "role": role, "company": company, "location": location,
                        "salary": salary, "years_exp": years_exp, "notes": notes,
                    }, timeout=60)
                    data = res.json()
                except Exception as e:
                    st.error(f"API error: {e}")
                    st.stop()

            st.success(f"Found {data['similar_jds_found']} market comps · {data['similar_profiles_found']} similar candidates")

            st.markdown("### 📊 Market Rate Assessment")
            st.markdown(data["market_rate"])

            st.markdown("### 💰 Counter-Offer Range")
            st.markdown(data["counter_range"])

            st.markdown("### ✉️ Negotiation Script")
            st.markdown(data["negotiation_script"])

            st.markdown("### 🎯 Your Leverage Points")
            st.markdown(data["key_points"])

            with st.expander("Full Claude response"):
                st.markdown(data["raw"])

            st.divider()
            feedback_buttons(data.get("log_id", ""), "salary")


# ── Tab 2: Negotiate Anything ──────────────────────────────────────────────────
with tab_free:
    st.subheader("Negotiate anything")
    st.caption("Rent, freelance rates, vendor contracts — describe your situation and get a word-for-word script.")

    situation = st.text_area(
        "Describe what you're negotiating",
        placeholder=(
            "Example: I'm a freelance developer. A client wants to pay me $75/hr for a 3-month project. "
            "I usually charge $120/hr. They said budget is tight but really need my React and AI skills. "
            "How do I negotiate this?"
        ),
        height=160,
    )

    if st.button("🧠 Get Negotiation Script", type="primary", use_container_width=True):
        if not situation.strip():
            st.warning("Describe your negotiation situation above.")
        else:
            with st.spinner("Crafting your negotiation strategy..."):
                try:
                    res = requests.post(f"{API_URL}/negotiate/free",
                                        json={"situation": situation}, timeout=60)
                    data = res.json()
                except Exception as e:
                    st.error(f"API error: {e}")
                    st.stop()

            st.markdown("### 🎯 Strategy")
            st.markdown(data["strategy"])

            st.markdown("### ✉️ Word-for-Word Script")
            st.markdown(data["script"])

            st.markdown("### 🔑 Key Tactics")
            st.markdown(data["tactics"])

            st.divider()
            feedback_buttons(data.get("log_id", ""), "free")


# ── Tab 3: Ingest Data ─────────────────────────────────────────────────────────
with tab_ingest:
    st.subheader("Add market data")
    col_jd, col_profile = st.columns(2)

    with col_jd:
        st.markdown("**📋 Job Description**")
        jd_title   = st.text_input("Title", key="jd_title", placeholder="Senior Engineer")
        jd_company = st.text_input("Company", key="jd_company")
        jd_loc     = st.text_input("Location", key="jd_loc", value="New York, NY")
        jd_min     = st.number_input("Min Salary", key="jd_min", value=0, step=5000)
        jd_max     = st.number_input("Max Salary", key="jd_max", value=0, step=5000)
        jd_content = st.text_area("JD Text", key="jd_content", height=120)
        if st.button("Add JD", use_container_width=True):
            if jd_title and jd_company and jd_content:
                r = requests.post(f"{API_URL}/ingest/jd", json={
                    "title": jd_title, "company": jd_company, "location": jd_loc,
                    "salary_min": jd_min or None, "salary_max": jd_max or None,
                    "content": jd_content,
                })
                st.success("JD ingested!") if r.ok else st.error(r.text)

    with col_profile:
        st.markdown("**👤 Candidate Profile**")
        p_title   = st.text_input("Title", key="p_title", placeholder="Senior Engineer")
        p_yrs     = st.number_input("Years Exp", key="p_yrs", value=3, min_value=0)
        p_skills  = st.text_input("Skills (comma-separated)", key="p_skills")
        p_content = st.text_area("Profile / Resume Text", key="p_content", height=120)
        if st.button("Add Profile", use_container_width=True):
            if p_title and p_content:
                r = requests.post(f"{API_URL}/ingest/profile", json={
                    "title": p_title, "years_exp": p_yrs,
                    "skills": [s.strip() for s in p_skills.split(",") if s.strip()],
                    "content": p_content,
                })
                st.success("Profile ingested!") if r.ok else st.error(r.text)


# ── Tab 4: Observability Dashboard ────────────────────────────────────────────
with tab_obs:
    st.subheader("📊 Observability Dashboard")
    st.caption("Live metrics from every negotiation request.")

    if st.button("🔄 Refresh", key="refresh_obs"):
        st.rerun()

    try:
        res = requests.get(f"{API_URL}/observe/stats", timeout=10)
        stats = res.json() if res.ok else {}
    except Exception:
        stats = {}

    logs     = stats.get("logs", [])
    feedback = stats.get("feedback", [])

    if not logs:
        st.info("No requests logged yet. Make a negotiation request to see data here.")
    else:
        import pandas as pd

        df = pd.DataFrame(logs)
        fb = pd.DataFrame(feedback) if feedback else pd.DataFrame()

        # ── Top metrics ────────────────────────────────────────────────────────
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Requests", len(df))
        m2.metric("Avg Latency", f"{df['latency_ms'].mean():.0f} ms")

        thumbs_up   = len(fb[fb["rating"] == 1])  if not fb.empty else 0
        thumbs_down = len(fb[fb["rating"] == -1]) if not fb.empty else 0
        total_fb    = thumbs_up + thumbs_down
        score       = f"{thumbs_up}/{total_fb}" if total_fb else "—"
        m3.metric("👍 Feedback", score)

        avg_sim = df["avg_jd_similarity"].dropna().mean()
        m4.metric("Avg RAG Similarity", f"{avg_sim:.3f}" if pd.notna(avg_sim) else "—")

        # ── Latency over time ──────────────────────────────────────────────────
        st.markdown("#### Request Latency (ms)")
        df["created_at"] = pd.to_datetime(df["created_at"])
        latency_chart = df.set_index("created_at")[["latency_ms"]].sort_index()
        st.line_chart(latency_chart)

        # ── Retrieval quality ──────────────────────────────────────────────────
        st.markdown("#### RAG Retrieval Quality")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**JD similarity scores**")
            sim_data = df["avg_jd_similarity"].dropna()
            if not sim_data.empty:
                st.bar_chart(sim_data.value_counts(bins=10).sort_index())
        with c2:
            st.markdown("**Docs retrieved per request**")
            st.bar_chart(df["jds_found"].value_counts().sort_index())

        # ── Endpoint split ─────────────────────────────────────────────────────
        st.markdown("#### Requests by Endpoint")
        st.bar_chart(df["endpoint"].value_counts())

        # ── Recent requests ────────────────────────────────────────────────────
        st.markdown("#### Recent Requests")
        display_cols = ["created_at", "endpoint", "role", "salary", "latency_ms",
                        "jds_found", "avg_jd_similarity"]
        st.dataframe(
            df[[c for c in display_cols if c in df.columns]]
              .sort_values("created_at", ascending=False)
              .head(20),
            use_container_width=True,
        )
