"""
One function per visualization. Every function takes the already-filtered
DataFrame and returns a Plotly figure -- app.py just calls st.plotly_chart
on the result. Kept separate from app.py so each chart can be tested/tweaked
in isolation.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from state_utils import CHOROPLETH_EXCLUDED, MONTH_ORDER, STATE_TO_ABBR

# Colorblind-safe qualitative palette (Okabe-Ito) used everywhere two
# categories (Female/Male) need to be told apart.
SEX_COLORS = {"Female": "#E69F00", "Male": "#0072B2"}
SEQUENTIAL_SCALE = "Viridis"  # colorblind-safe, perceptually uniform


def monthly_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Line chart of total births by month, in chronological order."""
    by_month = (
        df.groupby("month", observed=True)["births"].sum().reindex(MONTH_ORDER).dropna()
    )
    fig = px.line(
        x=by_month.index, y=by_month.values, markers=True,
        labels={"x": "Month", "y": "Births"},
        title="Monthly Birth Trend (Selected Filters)",
    )
    fig.update_traces(hovertemplate="%{x}<br>Births: %{y:,.0f}<extra></extra>")
    fig.update_yaxes(rangemode="tozero", tickformat=",")
    return fig


def sex_comparison_chart(df: pd.DataFrame) -> go.Figure:
    """Grouped bar chart comparing female vs. male births by month."""
    by_month_sex = (
        df.groupby(["month", "sex_of_infant"], observed=True)["births"]
        .sum()
        .reset_index()
    )
    fig = px.bar(
        by_month_sex, x="month", y="births", color="sex_of_infant",
        barmode="group", category_orders={"month": MONTH_ORDER},
        color_discrete_map=SEX_COLORS,
        labels={"month": "Month", "births": "Births", "sex_of_infant": "Sex"},
        title="Female vs. Male Births by Month",
    )
    fig.update_traces(hovertemplate="%{x}<br>Births: %{y:,.0f}<extra></extra>")
    fig.update_yaxes(rangemode="tozero", tickformat=",")
    return fig


def state_ranking_chart(df: pd.DataFrame, top_n: int | None = None) -> go.Figure:
    """Horizontal bar chart ranking geographies by total births (descending)."""
    by_state = (
        df.groupby("state_of_residence", observed=True)["births"]
        .sum()
        .sort_values(ascending=False)
    )
    if top_n:
        by_state = by_state.head(top_n)

    fig = px.bar(
        by_state.sort_values(ascending=True),  # ascending so largest bar is on top visually
        orientation="h",
        labels={"value": "Births", "state_of_residence": "State"},
        title="State Ranking by Total Births (Selected Filters)",
    )
    fig.update_traces(hovertemplate="%{y}<br>Births: %{x:,.0f}<extra></extra>")
    fig.update_layout(showlegend=False, yaxis_title="", xaxis_title="Births")
    fig.update_xaxes(rangemode="tozero", tickformat=",")
    return fig


def choropleth_chart(df: pd.DataFrame) -> go.Figure:
    """US state choropleth of total births. DC is excluded (no map polygon)."""
    map_df = df[~df["state_of_residence"].isin(CHOROPLETH_EXCLUDED)].copy()
    by_state = map_df.groupby("state_of_residence", observed=True)["births"].sum().reset_index()
    by_state["abbr"] = by_state["state_of_residence"].map(STATE_TO_ABBR)

    fig = px.choropleth(
        by_state, locations="abbr", locationmode="USA-states", color="births",
        scope="usa", color_continuous_scale=SEQUENTIAL_SCALE,
        hover_name="state_of_residence",
        labels={"births": "Births"},
        title="Births by State (Selected Filters) \u2014 DC not shown; see About the Data",
    )
    fig.update_traces(hovertemplate="%{hovertext}<br>Births: %{z:,.0f}<extra></extra>")
    return fig


def state_month_heatmap(df: pd.DataFrame) -> go.Figure:
    """Heatmap of births with states on one axis and chronological months on the other."""
    pivot = df.pivot_table(
        index="state_of_residence", columns="month", values="births",
        aggfunc="sum", observed=True,
    ).reindex(columns=MONTH_ORDER)
    # Order states by total descending so the heatmap reads top-to-bottom by volume.
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

    fig = px.imshow(
        pivot, aspect="auto", color_continuous_scale=SEQUENTIAL_SCALE,
        labels={"x": "Month", "y": "State", "color": "Births"},
        title="State-by-Month Birth Heatmap (Selected Filters)",
    )
    fig.update_traces(hovertemplate="%{y}, %{x}<br>Births: %{z:,.0f}<extra></extra>")
    # Height scales with number of states so labels stay legible.
    fig.update_layout(height=max(400, 18 * len(pivot)))
    return fig


def top_bottom_chart(df: pd.DataFrame, n: int = 5) -> go.Figure:
    """Side-by-side comparison of the top-N and bottom-N geographies by total births."""
    by_state = (
        df.groupby("state_of_residence", observed=True)["births"]
        .sum()
        .sort_values(ascending=False)
    )
    top = by_state.head(n).reset_index()
    top["group"] = f"Top {n}"
    bottom = by_state.tail(n).reset_index()
    bottom["group"] = f"Bottom {n}"
    combined = pd.concat([top, bottom], ignore_index=True)

    fig = px.bar(
        combined, x="state_of_residence", y="births", color="group",
        color_discrete_map={f"Top {n}": "#0072B2", f"Bottom {n}": "#D55E00"},
        labels={"state_of_residence": "State", "births": "Births", "group": ""},
        title=f"Top {n} vs. Bottom {n} Geographies by Total Births",
    )
    fig.update_traces(hovertemplate="%{x}<br>Births: %{y:,.0f}<extra></extra>")
    fig.update_yaxes(rangemode="tozero", tickformat=",")
    fig.update_xaxes(title="")
    return fig
