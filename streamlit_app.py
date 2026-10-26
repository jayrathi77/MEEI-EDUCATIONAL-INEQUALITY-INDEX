"""Streamlit dashboard for the MEEI synthetic demonstration project."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "data" / "processed"


@st.cache_data
def load_data():
    meei_path = PROCESSED / "meei_results.csv"
    priority_path = PROCESSED / "priority_districts.json"
    if not meei_path.exists():
        raise FileNotFoundError(f"Missing processed results: {meei_path}")
    meei = pd.read_csv(meei_path)
    priorities = []
    if priority_path.exists():
        with priority_path.open(encoding="utf-8") as source:
            priorities = json.load(source).get("districts", [])
    return meei, pd.DataFrame(priorities)


st.set_page_config(page_title="MEEI | Educational Equality", page_icon="📚", layout="wide")
st.title("Multidimensional Educational Equality Index")
st.caption("District level educational equality explorer for India")
st.warning(
    "Demo mode: figures shown here are based on synthetic demonstration data, "
    "not official government statistics."
)

try:
    meei, priorities = load_data()
except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
    st.error(f"Could not load the project results. {error}")
    st.info("Run the project pipeline to generate data/processed/meei_results.csv.")
    st.stop()

valid = meei.dropna(subset=["meei"]).copy()
states = sorted(valid["state_name"].dropna().unique().tolist())
page = st.sidebar.radio("Explore", ["Overview", "District explorer", "Priority districts"])
state_options = ["All India", *states]
selected_state = st.sidebar.selectbox("State / UT", state_options)
scope = valid if selected_state == "All India" else valid[valid.state_name == selected_state]

if page == "Overview":
    st.subheader(f"Overview · {selected_state}")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Districts", f"{len(scope):,}")
    col2.metric("States / UTs", f"{scope.state_name.nunique():,}")
    col3.metric("Mean MEEI", f"{scope.meei.mean():.3f}")
    col4.metric("Median MEEI", f"{scope.meei.median():.3f}")

    left, right = st.columns(2)
    with left:
        st.markdown("#### Highest equality scores")
        st.dataframe(
            scope.nlargest(10, "meei")[["district_name", "state_name", "meei", "meei_rank"]],
            hide_index=True, use_container_width=True,
        )
    with right:
        st.markdown("#### Lowest equality scores")
        st.dataframe(
            scope.nsmallest(10, "meei")[["district_name", "state_name", "meei", "meei_rank"]],
            hide_index=True, use_container_width=True,
        )

    if selected_state == "All India":
        st.markdown("#### Average MEEI by state / UT")
        state_means = valid.groupby("state_name")["meei"].mean().sort_values(ascending=False)
        st.bar_chart(state_means, horizontal=True)
    else:
        st.markdown("#### Sub-index averages")
        subindices = ["perf_subindex", "infra_subindex", "equity_subindex", "circ_subindex"]
        st.bar_chart(scope[subindices].mean().rename({
            "perf_subindex": "Performance", "infra_subindex": "Infrastructure",
            "equity_subindex": "Equity", "circ_subindex": "Circumstances",
        }))

elif page == "District explorer":
    st.subheader("District explorer")
    filtered = scope.sort_values("district_name")
    choices = filtered["district_name"].dropna().tolist()
    if not choices:
        st.info("No districts found for this selection.")
    else:
        district_name = st.selectbox("District", choices)
        district = filtered[filtered.district_name == district_name].iloc[0]
        st.markdown(f"### {district.district_name}, {district.state_name}")
        st.metric("MEEI score", f"{district.meei:.3f}", f"Rank {int(district.meei_rank)}")
        subs = {
            "Performance": district.perf_subindex,
            "Infrastructure": district.infra_subindex,
            "Equity": district.equity_subindex,
            "Circumstances": district.circ_subindex,
        }
        st.bar_chart(pd.Series(subs, name="Score"))
        st.caption("Scores range from 0 to 1; higher MEEI indicates greater educational equality.")

else:
    st.subheader("Priority districts")
    st.caption("Higher priority score indicates greater estimated disadvantage.")
    if priorities.empty:
        st.info("Priority results are not available. Run the pipeline to generate them.")
    else:
        priority_scope = priorities
        if selected_state != "All India":
            priority_scope = priority_scope[priority_scope.state_name == selected_state]
        display_cols = [
            col for col in ["priority_rank", "district_name", "state_name", "priority_score",
                            "predicted_equality", "meei", "infra_subindex", "equity_subindex"]
            if col in priority_scope.columns
        ]
        st.metric("Districts shown", f"{len(priority_scope):,}")
        st.dataframe(priority_scope[display_cols], hide_index=True, use_container_width=True)
        csv = priority_scope.drop(columns=["top_drivers"], errors="ignore").to_csv(index=False)
        st.download_button("Download priority list as CSV", csv, "priority_districts.csv", "text/csv")
