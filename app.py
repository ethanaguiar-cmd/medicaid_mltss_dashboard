import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ---------------------------------------------------------
# PAGE SETUP
# ---------------------------------------------------------

st.set_page_config(
    page_title="Medicaid MLTSS Dashboard",
    layout="wide"
)

st.title("Medicaid Managed Long-Term Services and Supports")

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

#Annual MLTSS dataset
df = pd.read_csv("medicaid_MLTSS_analysis.csv")

#Monthly total Medicaid enrollment dataset
monthly_df = pd.read_csv("medicaid_monthly_enrollment_clean.csv")

# Monthly dual-eligibility dataset
dual_df = pd.read_csv("medicaid_dual_monthly_clean.csv")

dual_df.loc[
    dual_df["data_quality_flag"] == "Unusable",
    ["dual_pct", "full_dual_pct", "partial_dual_pct", "nondual_pct"]
] = pd.NA

# Convert Stata heatmap category labels back to numeric codes
heatcat_map = {
    "0%": 0,
    ">0-1%": 1,
    ">1-2%": 2,
    ">2-3%": 3,
    ">3-4%": 4,
    ">4-5%": 5,
    ">5-7.5%": 6,
    ">7.5-10%": 7,
    ">10%": 8
}

df["mltss_heatcat_num"] = df["mltss_heatcat"].map(heatcat_map)

# ---------------------------------------------------------
# HEATMAP
# ---------------------------------------------------------

st.subheader("MLTSS Enrollment by State and Year")

st.caption(
    "MLTSS enrollment as a percentage of total Medicaid managed care enrollment. "
    "Hover over a cell for enrollment details."
)

# ---------------------------------------------------------
# HEATMAP CATEGORIES
# ---------------------------------------------------------

heat_labels = {
    0: "0%",
    1: ">0–1%",
    2: ">1–2%",
    3: ">2–3%",
    4: ">3–4%",
    5: ">4–5%",
    6: ">5–7.5%",
    7: ">7.5–10%",
    8: ">10%"
}

states = sorted(df["state"].unique())
years = sorted(df["year"].unique())

# ---------------------------------------------------------
# CREATE STATE × YEAR MATRICES
# ---------------------------------------------------------

heat_matrix = (
    df.pivot(
        index="state",
        columns="year",
        values="mltss_heatcat_num"
    )
    .reindex(index=states, columns=years)
)

# Use category 9 specifically for missing data
# This allows "No data" to have its own gray color and legend entry
display_matrix = heat_matrix.fillna(9)

pct_matrix = (
    df.pivot(
        index="state",
        columns="year",
        values="total_mltss_pct"
    )
    .reindex(index=states, columns=years)
)

# ---------------------------------------------------------
# HOVER INFORMATION
# ---------------------------------------------------------

hover_text = []

for state in states:

    row = []

    for year in years:

        obs = df[
            (df["state"] == state) &
            (df["year"] == year)
        ].iloc[0]

        total_pct = obs["total_mltss_pct"]
        national_pct = obs["national_mltss_pct"]
        total_mc = obs["total_mc"]
        comp_count = obs["comp_count"]
        only_count = obs["only_count"]
        comp_pct = obs["comp_pct"]
        only_pct = obs["only_pct"]

        # -----------------------------
        # Missing MLTSS observation
        # -----------------------------

        if pd.isna(total_pct):

            quality_flag = obs["data_quality_flag"]

            text = (
                f"<b>{state} — {year}</b><br>"
                f"<br>"
                f"<b>MLTSS:</b> Data unavailable<br>"
            )

            if not pd.isna(national_pct):
                text += (
                    f"<b>National MLTSS:</b> "
                    f"{national_pct:.2f}%<br>"
                )

            if not pd.isna(total_mc):
                text += (
                    f"<b>Total managed care:</b> "
                    f"{total_mc:,.0f}"
                )

            if (
                not pd.isna(quality_flag)
                and quality_flag != "OK"
            ):
                text += (
                    f"<br><b>Data note:</b> "
                    f"{quality_flag}"
                )

        # -----------------------------
        # Available MLTSS observation
        # -----------------------------

        else:

            text = (
                f"<b>{state} — {year}</b><br>"
                f"<br>"
                f"<b>Total MLTSS:</b> {total_pct:.2f}%<br>"
            )

            if not pd.isna(national_pct):
                text += (
                    f"<b>National MLTSS:</b> "
                    f"{national_pct:.2f}%<br>"
                )

            text += "<br>"

            if not pd.isna(total_mc):
                text += (
                    f"<b>Total managed care:</b> "
                    f"{total_mc:,.0f}<br>"
                )

            if not pd.isna(comp_count):
                text += (
                    f"<b>Comprehensive MLTSS:</b> "
                    f"{comp_count:,.0f}"
                )

                if not pd.isna(comp_pct):
                    text += f" ({comp_pct:.1f}%)"

                text += "<br>"

            if not pd.isna(only_count):
                text += (
                    f"<b>MLTSS-only:</b> "
                    f"{only_count:,.0f}"
                )

                if not pd.isna(only_pct):
                    text += f" ({only_pct:.1f}%)"

        row.append(text)

    hover_text.append(row)

# ---------------------------------------------------------
# DISCRETE COLOR SCALE
# ---------------------------------------------------------

colors = [
    "#440154",  # 0%
    "#482878",  # >0–1%
    "#3E4989",  # >1–2%
    "#31688E",  # >2–3%
    "#26828E",  # >3–4%
    "#1F9E89",  # >4–5%
    "#35B779",  # >5–7.5%
    "#90D743",  # >7.5–10%
    "#FDE725",  # >10%
    "#D9D9D9"   # No data
]

# Create a truly discrete Plotly color scale
n_colors = len(colors)

discrete_colorscale = []

for i, color in enumerate(colors):

    lower = i / n_colors
    upper = (i + 1) / n_colors

    discrete_colorscale.append([lower, color])
    discrete_colorscale.append([upper, color])

# ---------------------------------------------------------
# MAIN HEATMAP
# ---------------------------------------------------------

fig = go.Figure()

fig.add_trace(
    go.Heatmap(
        z=display_matrix.to_numpy(),
        x=[str(y) for y in years],
        y=states,
        text=hover_text,
        hovertemplate="%{text}<extra></extra>",

        zmin=-0.5,
        zmax=9.5,

        colorscale=discrete_colorscale,
        showscale=True,

        xgap=1,
        ygap=1,

        colorbar=dict(
            title="MLTSS %",
            tickmode="array",

            tickvals=list(range(10)),

            ticktext=[
                "0%",
                ">0–1%",
                ">1–2%",
                ">2–3%",
                ">3–4%",
                ">4–5%",
                ">5–7.5%",
                ">7.5–10%",
                ">10%",
                "No data"
            ],

            thickness=20,
            len=0.85
        )
    )
)

# ---------------------------------------------------------
# LAYOUT
# ---------------------------------------------------------

fig.update_layout(
    height=1250,
    margin=dict(
        l=160,
        r=120,
        t=20,
        b=60
    ),
    xaxis=dict(
        title="Year",
        side="bottom",
        tickfont=dict(size=12)
    ),
    yaxis=dict(
        title="",
        autorange="reversed",
        tickfont=dict(size=11)
    ),
    template="plotly_white",
    hoverlabel=dict(
    bgcolor="#FFFFFF",
    bordercolor="#333333",
    font=dict(
        color="#111111",
        size=13,
        family="Arial"
         )
    )
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "displayModeBar": True,
        "scrollZoom": False
    }
)

# ---------------------------------------------------------
# DASHBOARD CONTROLS
# ---------------------------------------------------------

st.divider()

st.subheader("Dashboard Controls")

control_col1, control_col2 = st.columns(2)

with control_col1:
    selected_state = st.selectbox(
        "Select a state",
        options=states,
        index=states.index("Rhode Island")
    )

with control_col2:
    selected_year = st.selectbox(
        "Select a year",
        options=years,
        index=years.index(2024)
    )

# ---------------------------------------------------------
# STATE TRAJECTORY
# ---------------------------------------------------------

st.divider()

st.subheader("State MLTSS Trend")

st.caption(
    "Select a state to compare its MLTSS enrollment percentage with the "
    "enrollment-weighted national percentage."
)

# Pull selected state's observations
state_df = (
    df[df["state"] == selected_state]
    .sort_values("year")
    .copy()
)

# ---------------------------------------------------------
# CREATE STATE TRAJECTORY FIGURE
# ---------------------------------------------------------

state_fig = go.Figure()

# Selected state
# Build clean hover labels for the selected state
state_hover = []

for _, obs in state_df.iterrows():

    if pd.isna(obs["total_mltss_pct"]):
        text = (
            f"<b>{selected_state} — {int(obs['year'])}</b><br><br>"
            f"<b>MLTSS:</b> Data unavailable"
        )

    else:
        text = (
            f"<b>{selected_state} — {int(obs['year'])}</b><br><br>"
            f"<b>Total MLTSS:</b> {obs['total_mltss_pct']:.2f}%<br>"
        )

        if not pd.isna(obs["total_mc"]):
            text += (
                f"<br><b>Total managed care:</b> "
                f"{obs['total_mc']:,.0f}<br>"
            )

        if not pd.isna(obs["comp_count"]):
            text += (
                f"<b>Comprehensive MLTSS:</b> "
                f"{obs['comp_count']:,.0f}<br>"
            )

        if not pd.isna(obs["only_count"]):
            text += (
                f"<b>MLTSS-only:</b> "
                f"{obs['only_count']:,.0f}"
            )

    state_hover.append(text)


# Selected-state line
state_fig.add_trace(
    go.Scatter(
        x=state_df["year"],
        y=state_df["total_mltss_pct"],
        mode="lines+markers",
        name=selected_state,
        line=dict(
            width=3,
            color="#56B4E9"
        ),
        marker=dict(
            size=8,
            color="#56B4E9"
        ),
        text=state_hover,
        hovertemplate="%{text}<extra></extra>",
        connectgaps=False
    )
)

# National comparison
state_fig.add_trace(
    go.Scatter(
        x=state_df["year"],
        y=state_df["national_mltss_pct"],
        mode="lines",
        name="National",
        line=dict(
            width=2,
            dash="dash",
            color="#B8B8B8"
        ),
        hovertemplate=(
            "<b>National — %{x}</b><br><br>"
            "<b>MLTSS:</b> %{y:.2f}%"
            "<extra></extra>"
        )
    )
)

# ---------------------------------------------------------
# ADAPTIVE Y-AXIS
# ---------------------------------------------------------

state_max = state_df["total_mltss_pct"].max()
national_max = state_df["national_mltss_pct"].max()

plot_max = max(state_max, national_max)

# Give ordinary states a consistent 0–10% view.
# Expand automatically only when a state exceeds 10%.
if plot_max <= 10:
    y_max = 10
else:
    y_max = plot_max * 1.10

# ---------------------------------------------------------
# TRAJECTORY LAYOUT
# ---------------------------------------------------------

state_fig.update_layout(
    height=500,
    margin=dict(
        l=70,
        r=40,
        t=30,
        b=60
    ),
    xaxis=dict(
        title="Year",
        tickmode="array",
        tickvals=years,
        dtick=1
    ),
    yaxis=dict(
        title="MLTSS enrollment (% of managed care)",
        range=[0, y_max],
        ticksuffix="%",
        gridcolor="rgba(255,255,255,0.12)",
        zeroline=True
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0
    ),
    hoverlabel=dict(
        bgcolor="#FFFFFF",
        bordercolor="#333333",
        font=dict(
            color="#111111",
            size=13,
            family="Arial"
        )
    )
)

st.plotly_chart(
    state_fig,
    use_container_width=True,
    config={
        "displayModeBar": True,
        "scrollZoom": False
    }
)

st.caption(
    "The y-axis uses a 0–10% range for states within that range "
    "and expands automatically when a state exceeds 10%."
)

# ============================================================
# MONTHLY MEDICAID ENROLLMENT
# ============================================================

st.divider()

st.subheader("Monthly Medicaid Enrollment")

st.caption(
    "Total Medicaid enrollment by month for the selected state and year. "
    "Monthly enrollment is shown separately from the annual managed-care "
    "and MLTSS measures above."
)

monthly_selected = monthly_df[
    (monthly_df["state"] == selected_state) &
    (monthly_df["year"] == selected_year)
].copy()

monthly_selected = monthly_selected.sort_values("month")

month_labels = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec"
}

monthly_selected["month_name"] = monthly_selected["month"].map(month_labels)

valid_monthly = monthly_selected.dropna(subset=["total_medicaid"])

if not valid_monthly.empty:

    min_enrollment = valid_monthly["total_medicaid"].min()
    max_enrollment = valid_monthly["total_medicaid"].max()

    change_enrollment = (
        valid_monthly.iloc[-1]["total_medicaid"]
        - valid_monthly.iloc[0]["total_medicaid"]
    )

    change_pct = (
        100
        * change_enrollment
        / valid_monthly.iloc[0]["total_medicaid"]
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "First available month",
        f"{valid_monthly.iloc[0]['total_medicaid']:,.0f}"
    )

    col2.metric(
        "Latest available month",
        f"{valid_monthly.iloc[-1]['total_medicaid']:,.0f}"
    )

    col3.metric(
        "Change",
        f"{change_pct:+.1f}%"
    )

else:
    st.warning(
        f"No monthly Medicaid enrollment data are available for "
        f"{selected_state} in {selected_year}."
    )

# Create monthly enrollment figure
monthly_fig = go.Figure()

monthly_fig.add_trace(
    go.Bar(
        x=monthly_selected["month_name"],
        y=monthly_selected["total_medicaid"],
        hovertemplate=(
            "<b>%{x} " + str(selected_year) + "</b><br>"
            "<b>Total Medicaid enrollment:</b> %{y:,.0f}"
            "<extra></extra>"
        ),
        name="Total Medicaid enrollment"
    )
)

monthly_fig.update_layout(
    height=450,
    margin=dict(
        l=80,
        r=40,
        t=50,
        b=60
    ),
    title=dict(
        text=f"{selected_state} — {selected_year}",
        x=0
    ),
    xaxis=dict(
        title="Month",
        categoryorder="array",
        categoryarray=[
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]
    ),
    yaxis=dict(
        title="Total Medicaid enrollment",
        tickformat=","
    ),
    template="plotly_white",
    showlegend=False,
    hoverlabel=dict(
        bgcolor="#FFFFFF",
        bordercolor="#333333",
        font=dict(
            color="#111111",
            size=13,
            family="Arial"
        )
    )
)

st.plotly_chart(
    monthly_fig,
    use_container_width=True,
    config={
        "displayModeBar": True,
        "scrollZoom": False
    }
)

missing_months = monthly_selected[
    monthly_selected["total_medicaid"].isna()
]

if not missing_months.empty:
    missing_names = missing_months["month_name"].tolist()

    st.info(
        "Enrollment data unavailable for: "
        + ", ".join(missing_names)
        + ". Missing values are not treated as zero."
    )

# ---------------------------------------------------------
# MONTHLY DUAL ELIGIBILITY
# ---------------------------------------------------------

st.divider()
st.subheader("Monthly Dual-Eligible Enrollment")

st.caption(
    "Monthly share of enrollees with full or partial dual eligibility. "
    "Each stacked bar represents total dual enrollment as a percentage of "
    "full-dual, partial-dual, and non-dual enrollment in the CMS dual-status dataset."
)

dual_selected = dual_df[
    (dual_df["state"] == selected_state) &
    (dual_df["year"] == selected_year)
].copy()

dual_selected = dual_selected.sort_values("month")

# Add readable month labels
dual_selected["month_name"] = dual_selected["month"].map(month_labels)

# Keep only months with usable percentage data for summary metrics
valid_dual = dual_selected.dropna(subset=["dual_pct"])

if not valid_dual.empty:

    first_dual_pct = valid_dual.iloc[0]["dual_pct"]
    latest_dual_pct = valid_dual.iloc[-1]["dual_pct"]

    first_month_name = valid_dual.iloc[0]["month_name"]
    latest_month_name = valid_dual.iloc[-1]["month_name"]

    dual_change_pp = latest_dual_pct - first_dual_pct

    col1, col2, col3 = st.columns(3)

    col1.metric(
        f"{first_month_name} dual share",
        f"{first_dual_pct:.1f}%"
    )

    col2.metric(
        f"{latest_month_name} dual share",
        f"{latest_dual_pct:.1f}%"
    )

    col3.metric(
        "Change",
        f"{dual_change_pp:+.1f} pp"
    )

    # ---------------------------------------------------------
    # CREATE 100% STACKED BAR CHART
    # ---------------------------------------------------------

    dual_fig = go.Figure()

    dual_fig.add_trace(
        go.Bar(
            x=dual_selected["month_name"],
            y=dual_selected["full_dual_pct"],
            name="Full dual",
            customdata=dual_selected[
                ["full_dual", "dual_pct", "data_quality_flag"]
            ].to_numpy(),
            hovertemplate=(
                "<b>%{x} " + str(selected_year) + "</b><br>"
                "<b>Full dual:</b> %{customdata[0]:,.0f}<br>"
                "<b>Share:</b> %{y:.1f}%<br>"
                "<b>Total dual:</b> %{customdata[1]:.1f}%<br>"
                "<b>Data quality:</b> %{customdata[2]}"
                "<extra></extra>"
            )
        )
    )

    dual_fig.add_trace(
        go.Bar(
            x=dual_selected["month_name"],
            y=dual_selected["partial_dual_pct"],
            name="Partial dual",
            customdata=dual_selected[
                ["partial_dual", "dual_pct", "data_quality_flag"]
            ].to_numpy(),
            hovertemplate=(
                "<b>%{x} " + str(selected_year) + "</b><br>"
                "<b>Partial dual:</b> %{customdata[0]:,.0f}<br>"
                "<b>Share:</b> %{y:.1f}%<br>"
                "<b>Total dual:</b> %{customdata[1]:.1f}%<br>"
                "<b>Data quality:</b> %{customdata[2]}"
                "<extra></extra>"
            )
        )
    )

    dual_fig.update_layout(
        barmode="stack",
        height=500,
        margin=dict(l=80, r=40, t=85, b=60),
        title=dict(
            text=f"{selected_state} — {selected_year}",
            x=0
        ),
        xaxis=dict(
            title="Month",
            categoryorder="array",
            categoryarray=[
                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
            ]
        ),
        yaxis=dict(
            title="Share of total enrollment (%)",
            rangemode="tozero",
            ticksuffix="%"
        ),
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="right",
            x=1,
            traceorder="normal"
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#333333",
            font=dict(
                color="#111111",
                size=13,
                family="Arial"
            )
        )
    )

    st.plotly_chart(
        dual_fig,
        use_container_width=True,
        config={
            "displayModeBar": True,
            "scrollZoom": False
        }
    )

    # Flag months with data-quality concerns
# ---------------------------------------------------------
# DATA QUALITY NOTES
# ---------------------------------------------------------

# Quietly note months whose data quality was not assessed
not_assessed = dual_selected[
    dual_selected["data_quality_flag"] == "Not assessed"
]

if not not_assessed.empty:
    not_assessed_months = ", ".join(
        not_assessed["month_name"].tolist()
    )

    st.caption(
        "CMS data quality was not assessed for: "
        + not_assessed_months
        + "."
    )

# More prominently flag months with actual data-quality concerns
concern_dual = dual_selected[
    dual_selected["data_quality_flag"].isin(
        ["High Concern", "Unusable"]
    )
]

if not concern_dual.empty:
    concern_text = ", ".join(
        concern_dual.apply(
            lambda row: (
                f"{row['month_name']} "
                f"({row['data_quality_flag']})"
            ),
            axis=1
        )
    )

    st.warning(
        "CMS data-quality concern: "
        + concern_text
    )

else:
    st.info(
        f"Usable dual-eligibility data are not available for "
        f"{selected_state} in {selected_year}."
    )

# ---------------------------------------------------------
# YEAR DISTRIBUTION
# ---------------------------------------------------------

st.divider()

st.subheader("State Distribution by Year")

st.caption(
    "Select a year to compare MLTSS enrollment percentages across states. "
    "States are ranked from highest to lowest among those with usable data."
)

# Pull observations for selected year
year_df = (
    df[df["year"] == selected_year]
    .copy()
)

# Separate usable observations from missing observations
year_available = (
    year_df[year_df["total_mltss_pct"].notna()]
    .sort_values("total_mltss_pct", ascending=True)
    .copy()
)

year_missing = (
    year_df[year_df["total_mltss_pct"].isna()]
    .sort_values("state")
    .copy()
)

# National percentage for selected year
national_year_pct = year_df["national_mltss_pct"].dropna().iloc[0]

# ---------------------------------------------------------
# YEAR-DISTRIBUTION HOVER LABELS
# ---------------------------------------------------------

distribution_hover = []

for _, obs in year_available.iterrows():

    text = (
        f"<b>{obs['state']} — {selected_year}</b><br><br>"
        f"<b>Total MLTSS:</b> {obs['total_mltss_pct']:.2f}%<br>"
        f"<b>National MLTSS:</b> {national_year_pct:.2f}%<br>"
    )

    if not pd.isna(obs["total_mc"]):
        text += (
            f"<br><b>Total managed care:</b> "
            f"{obs['total_mc']:,.0f}<br>"
        )

    if not pd.isna(obs["comp_count"]):
        text += (
            f"<b>Comprehensive MLTSS:</b> "
            f"{obs['comp_count']:,.0f}<br>"
        )

    if not pd.isna(obs["only_count"]):
        text += (
            f"<b>MLTSS-only:</b> "
            f"{obs['only_count']:,.0f}"
        )

    distribution_hover.append(text)

year_available["hover_text"] = distribution_hover

# ---------------------------------------------------------
# CREATE YEAR-DISTRIBUTION FIGURE
# ---------------------------------------------------------

distribution_fig = go.Figure()

# All states
distribution_fig.add_trace(
    go.Scatter(
        x=year_available["total_mltss_pct"],
        y=year_available["state"],
        mode="markers",
        name="States/DC",
        marker=dict(
            size=9,
            color="#56B4E9",
            opacity=0.8
        ),
        text=year_available["hover_text"],
        hovertemplate="%{text}<extra></extra>"
    )
)

# National reference line
distribution_fig.add_vline(
    x=national_year_pct,
    line_width=2,
    line_dash="dash",
    line_color="#B8B8B8",
    annotation_text=f"National: {national_year_pct:.2f}%",
    annotation_position="top"
)

# ---------------------------------------------------------
# HIGHLIGHT SELECTED STATE
# ---------------------------------------------------------

selected_state_year = year_available[
    year_available["state"] == selected_state
]

if not selected_state_year.empty:

    selected_obs = selected_state_year.iloc[0]

    distribution_fig.add_trace(
        go.Scatter(
            x=[selected_obs["total_mltss_pct"]],
            y=[selected_state],
            mode="markers",
            name=selected_state,
            marker=dict(
                size=15,
                color="#E69F00",
                line=dict(
                    color="white",
                    width=2
                )
            ),
            hovertemplate=(
                f"<b>{selected_state} — {selected_year}</b><br><br>"
                f"<b>Total MLTSS:</b> "
                f"{selected_obs['total_mltss_pct']:.2f}%"
                "<extra></extra>"
            )
        )
    )

# ---------------------------------------------------------
# YEAR-DISTRIBUTION LAYOUT
# ---------------------------------------------------------

distribution_fig.update_layout(
    height=1050,
    margin=dict(
        l=160,
        r=60,
        t=50,
        b=60
    ),

    xaxis=dict(
        title="MLTSS enrollment (% of managed care)",
        ticksuffix="%",
        rangemode="tozero",
        gridcolor="rgba(255,255,255,0.12)"
    ),

    yaxis=dict(
        title="",
        tickfont=dict(size=11)
    ),

    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0
    ),

    hoverlabel=dict(
        bgcolor="#FFFFFF",
        bordercolor="#333333",
        font=dict(
            color="#111111",
            size=13,
            family="Arial"
        )
    )
)

st.plotly_chart(
    distribution_fig,
    use_container_width=True,
    config={
        "displayModeBar": True,
        "scrollZoom": False
    }
)

# ---------------------------------------------------------
# MISSING STATES NOTE
# ---------------------------------------------------------

if len(year_missing) > 0:

    missing_states = ", ".join(year_missing["state"].tolist())

    st.caption(
        f"No usable MLTSS percentage in {selected_year}: "
        f"{missing_states}."
    )