"""
CDC Provisional Natality 2025 Dashboard
Entry point: run with `streamlit run app.py`.

Layout: header -> sidebar filters -> KPI row -> tabs (Overview, Geographic
Analysis, Monthly and Sex Analysis, Data Table and Download, About the Data).
"""

import pandas as pd
import streamlit as st

from charts import (
    choropleth_chart,
    monthly_trend_chart,
    sex_comparison_chart,
    state_month_heatmap,
    state_ranking_chart,
    top_bottom_chart,
)
from data_loader import DataValidationError, load_data
from kpis import compute_kpis
from state_utils import CHOROPLETH_EXCLUDED, MONTH_ORDER

st.set_page_config(
    page_title="CDC Provisional Natality 2025 Dashboard",
    page_icon="\U0001F476",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Data load
# ---------------------------------------------------------------------------
try:
    df = load_data()
except DataValidationError as e:
    st.error(str(e))
    st.stop()

for problem in df.attrs.get("validation_problems", []):
    st.warning(f"Data check: {problem}")

ALL_STATES = sorted(df["state_of_residence"].unique())
ALL_MONTHS = MONTH_ORDER
ALL_SEXES = sorted(df["sex_of_infant"].unique())

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("\U0001F476 CDC Provisional Natality Dashboard \u2014 2025")
st.markdown(
    "Explore 2025 U.S. birth counts by state, month, and infant sex using "
    "provisional CDC WONDER data. Use the sidebar to filter, then browse the "
    "tabs below for geographic, monthly, and sex-based breakdowns."
)
st.info(
    "**Provisional data:** these figures are preliminary and subject to "
    "revision as CDC finalizes reporting for 2025.\n\n"
    "**Counts, not rates:** every number on this dashboard is a raw birth "
    "*count*. It is not adjusted for population size, so it should not be "
    "read as a birth rate or used to compare states' relative fertility."
)
st.caption("Source: CDC WONDER, Provisional Natality 2025 data.")

# ---------------------------------------------------------------------------
# Sidebar filters (session_state-backed so "Reset Filters" can restore them)
# ---------------------------------------------------------------------------
if "state_filter" not in st.session_state:
    st.session_state.state_filter = ALL_STATES.copy()
if "month_filter" not in st.session_state:
    st.session_state.month_filter = ALL_MONTHS.copy()
if "sex_filter" not in st.session_state:
    st.session_state.sex_filter = ALL_SEXES.copy()


def _reset_filters():
    st.session_state.state_filter = ALL_STATES.copy()
    st.session_state.month_filter = ALL_MONTHS.copy()
    st.session_state.sex_filter = ALL_SEXES.copy()


def _select_all_states():
    st.session_state.state_filter = ALL_STATES.copy()


def _select_all_months():
    st.session_state.month_filter = ALL_MONTHS.copy()


with st.sidebar:
    st.header("Filters")

    st.button("Select All States", on_click=_select_all_states, use_container_width=True)
    selected_states = st.multiselect(
        "State / Geography", options=ALL_STATES, key="state_filter",
    )

    st.button("Select All Months", on_click=_select_all_months, use_container_width=True)
    selected_months = st.multiselect(
        "Month", options=ALL_MONTHS, key="month_filter",
    )

    selected_sexes = st.multiselect(
        "Infant Sex", options=ALL_SEXES, key="sex_filter",
    )

    st.divider()
    st.button("\U0001F504 Reset Filters", on_click=_reset_filters, use_container_width=True)

    st.divider()
    n_states_sel = len(selected_states)
    n_months_sel = len(selected_months)
    sex_label = (
        "Both" if set(selected_sexes) == set(ALL_SEXES)
        else (", ".join(selected_sexes) if selected_sexes else "None")
    )
    st.caption(
        f"**Active filters:** {n_states_sel} of {len(ALL_STATES)} states \u00b7 "
        f"{n_months_sel} of {len(ALL_MONTHS)} months \u00b7 Sex: {sex_label}"
    )

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------
filtered_df = df[
    df["state_of_residence"].isin(selected_states)
    & df["month"].isin(selected_months)
    & df["sex_of_infant"].isin(selected_sexes)
]

if filtered_df.empty:
    st.warning(
        "No data matches the current filter selection. Try widening your "
        "state, month, or sex filters in the sidebar."
    )
    st.stop()

# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------
kpi = compute_kpis(filtered_df)
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Births", f"{kpi['total_births']:,}")
k2.metric("Geographies Selected", f"{kpi['n_geographies']:,}")
k3.metric("Avg Births / Month", f"{kpi['avg_births_per_month']:,.0f}")
k4.metric("Top Geography", kpi["top_geography"])
k5.metric("Top Month", kpi["top_month"])

st.divider()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_overview, tab_geo, tab_monthly_sex, tab_data, tab_about = st.tabs(
    ["Overview", "Geographic Analysis", "Monthly and Sex Analysis", "Data Table and Download", "About the Data"]
)

with tab_overview:
    st.plotly_chart(monthly_trend_chart(filtered_df), use_container_width=True)
    st.caption(
        "Total births per month across all currently selected states and sexes, "
        "in calendar order."
    )

with tab_geo:
    st.plotly_chart(state_ranking_chart(filtered_df), use_container_width=True)
    st.plotly_chart(choropleth_chart(filtered_df), use_container_width=True)
    if set(selected_states) & CHOROPLETH_EXCLUDED:
        st.caption(
            "Note: District of Columbia is included in the ranking chart and "
            "KPIs but cannot be shown on the state choropleth map."
        )
    top_n = st.slider("Number of states to compare (top/bottom)", min_value=3, max_value=10, value=5)
    st.plotly_chart(top_bottom_chart(filtered_df, n=top_n), use_container_width=True)

with tab_monthly_sex:
    st.plotly_chart(sex_comparison_chart(filtered_df), use_container_width=True)
    st.plotly_chart(state_month_heatmap(filtered_df), use_container_width=True)

with tab_data:
    st.subheader("Filtered Data")
    search = st.text_input("Search state name")
    table_df = filtered_df.copy()
    if search:
        table_df = table_df[
            table_df["state_of_residence"].str.contains(search, case=False, na=False)
        ]
    display_df = table_df[
        ["state_of_residence", "month", "sex_of_infant", "births"]
    ].sort_values(["state_of_residence", "month"]).reset_index(drop=True)
    st.dataframe(display_df, use_container_width=True)
    st.download_button(
        "Download filtered data as CSV",
        data=display_df.to_csv(index=False).encode("utf-8"),
        file_name="natality_2025_filtered.csv",
        mime="text/csv",
    )

with tab_about:
    st.subheader("About This Data")
    st.markdown(
        "- **Source:** CDC WONDER, Provisional Natality 2025.\n"
        "- **Provisional status:** 2025 birth data is preliminary and will "
        "be revised as more complete reporting comes in.\n"
        "- **Counts vs. rates:** all figures are raw birth counts. They are "
        "not normalized by population, so larger states will naturally show "
        "higher counts regardless of underlying fertility rate.\n"
        "- **Geographic coverage:** 50 states plus the District of Columbia.\n"
        "- **DC and the map:** the choropleth visualization uses Plotly's "
        "standard USA state geometry, which does not include a polygon for "
        "DC. DC's data is present everywhere else (KPIs, rankings, table, "
        "heatmap) but omitted from the map only.\n"
        "- **Columns:** `state_of_residence`, `month`, `month_code` "
        "(1\u201312), `year_code`, `sex_of_infant`, `births`."
    )
