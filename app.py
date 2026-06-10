import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from main import load_data, generate_report, METRICS


st.set_page_config(
    page_title="Behavioral Insight Engine",
    page_icon="🧠",
    layout="wide",
)


# -----------------------------
# SESSION STATE
# -----------------------------
if "report_generated" not in st.session_state:
    st.session_state.report_generated = False

if "df" not in st.session_state:
    st.session_state.df = None

if "report" not in st.session_state:
    st.session_state.report = None

if "last_output_path" not in st.session_state:
    st.session_state.last_output_path = None


# -----------------------------
# CSS
# -----------------------------
st.markdown(
    """
    <style>
    .main {
        background-color: #f6f8fb;
    }

    .hero {
        padding: 28px;
        border-radius: 22px;
        background: linear-gradient(135deg, #0f172a, #2563eb);
        color: white;
        margin-bottom: 25px;
    }

    .hero h1 {
        font-size: 42px;
        margin-bottom: 6px;
    }

    .hero p {
        font-size: 17px;
        opacity: 0.9;
    }

    .metric-card {
        padding: 22px;
        border-radius: 18px;
        background-color: white;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
        border: 1px solid #e5e7eb;
    }

    .metric-title {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 8px;
    }

    .metric-value {
        font-size: 32px;
        font-weight: 800;
        color: #0f172a;
    }

    .insight-card {
        padding: 18px;
        border-radius: 16px;
        background-color: white;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.07);
        border-left: 6px solid #2563eb;
        margin-bottom: 14px;
    }

    .anomaly-card {
        padding: 18px;
        border-radius: 16px;
        background-color: white;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.07);
        border-left: 6px solid #ef4444;
        margin-bottom: 14px;
    }

    .abstain-card {
        padding: 18px;
        border-radius: 16px;
        background-color: white;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.07);
        border-left: 6px solid #f59e0b;
        margin-bottom: 14px;
    }

    .badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        color: white;
        background-color: #2563eb;
        margin-bottom: 8px;
    }

    .small-text {
        color: #64748b;
        font-size: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# HEADER
# -----------------------------
st.markdown(
    """
    <div class="hero">
        <h1>Behavioral Insight Engine</h1>
        <p>AI-powered behavioral pattern discovery, anomaly detection, and confidence-based insight reporting.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.title("⚙️ Controls")

    uploaded_file = st.file_uploader(
        "Upload behavior CSV",
        type=["csv"],
        help="CSV must contain user_id, date, steps, sleep_hours, screen_time_hours, deep_work_hours, exercise_minutes",
    )

    default_path = st.text_input(
        "Default CSV path",
        value="data/behavior.csv",
    )

    output_path = st.text_input(
        "Report output path",
        value="results/report.json",
    )

    run_button = st.button("Generate Insights", use_container_width=True)


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def resolve_project_path(path_text: str) -> Path:
    """
    Converts relative path like data/behavior.csv
    into absolute project path.
    """
    path = Path(path_text)

    if path.is_absolute():
        return path

    return ROOT / path


def get_input_path(uploaded_file, default_path: str) -> str:
    """
    If user uploads CSV, use uploaded CSV.
    If no upload, use default CSV file.
    """
    data_folder = ROOT / "data"
    data_folder.mkdir(parents=True, exist_ok=True)

    if uploaded_file is not None:
        upload_path = data_folder / "_uploaded_behavior.csv"

        with open(upload_path, "wb") as file:
            file.write(uploaded_file.getbuffer())

        return str(upload_path)

    default_csv_path = resolve_project_path(default_path)

    if not default_csv_path.exists():
        raise FileNotFoundError(
            f"No uploaded CSV found and default file does not exist: {default_csv_path}"
        )

    return str(default_csv_path)


def prepare_insight_tables(report):
    insights = report.get("insights", [])
    insights_df = pd.DataFrame(insights)

    if insights_df.empty or "type" not in insights_df.columns:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    patterns_df = insights_df[insights_df["type"] == "pattern"]
    anomalies_df = insights_df[insights_df["type"] == "anomaly"]
    abstentions_df = insights_df[insights_df["type"] == "abstention"]

    return patterns_df, anomalies_df, abstentions_df


def render_metric_card(title, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard(df, report):
    patterns_df, anomalies_df, abstentions_df = prepare_insight_tables(report)
    summary = report["dataset_summary"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card("Total Rows", summary["rows"])

    with col2:
        render_metric_card("Users", summary["users"])

    with col3:
        render_metric_card("Patterns Found", len(patterns_df))

    with col4:
        render_metric_card("Anomalies Found", len(anomalies_df))

    st.markdown("")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📊 Dashboard",
            "💡 Insights",
            "🚨 Anomalies",
            "📄 Raw Data",
        ]
    )

    # -----------------------------
    # TAB 1: DASHBOARD
    # -----------------------------
    with tab1:
        st.subheader("Behavior Trend Analysis")

        left, right = st.columns([1, 1])

        with left:
            selected_user = st.selectbox(
                "Select User",
                sorted(df["user_id"].unique()),
            )

        with right:
            selected_metric = st.selectbox(
                "Select Metric",
                list(METRICS.keys()),
                format_func=lambda x: METRICS[x]["name"],
            )

        user_df = df[df["user_id"] == selected_user].sort_values("date")

        fig = px.line(
            user_df,
            x="date",
            y=selected_metric,
            markers=True,
            title=f"{METRICS[selected_metric]['name']} Trend for User {selected_user}",
        )

        fig.update_layout(
            height=430,
            plot_bgcolor="white",
            paper_bgcolor="white",
            title_font_size=22,
            xaxis_title="Date",
            yaxis_title=f"{METRICS[selected_metric]['name']} ({METRICS[selected_metric]['unit']})",
        )

        st.plotly_chart(fig, use_container_width=True)

        if not patterns_df.empty and "change_percentage" in patterns_df.columns:
            st.subheader("Pattern Change Percentage")

            pattern_chart_df = patterns_df.copy()
            pattern_chart_df["label"] = (
                "User "
                + pattern_chart_df["user_id"].astype(str)
                + " - "
                + pattern_chart_df["domain"]
            )

            fig2 = px.bar(
                pattern_chart_df,
                x="label",
                y="change_percentage",
                text="change_percentage",
                title="Meaningful Behavioral Changes",
            )

            fig2.update_layout(
                height=420,
                plot_bgcolor="white",
                paper_bgcolor="white",
                xaxis_title="Pattern",
                yaxis_title="Change Percentage (%)",
            )

            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No meaningful pattern changes found yet.")

    # -----------------------------
    # TAB 2: INSIGHTS
    # -----------------------------
    with tab2:
        st.subheader("Generated Behavioral Insights")

        if patterns_df.empty:
            st.info("No pattern insights were generated.")
        else:
            for _, item in patterns_df.iterrows():
                st.markdown(
                    f"""
                    <div class="insight-card">
                        <div class="badge">PATTERN</div>
                        <h4>User {item.get("user_id", "")} | {item.get("domain", "")}</h4>
                        <p><b>Insight:</b> {item.get("insight", "")}</p>
                        <p><b>Interpretation:</b> {item.get("interpretation", "")}</p>
                        <p><b>Evidence:</b> {item.get("evidence", "")}</p>
                        <p class="small-text">
                            Confidence: {item.get("confidence", "")} |
                            Change: {item.get("change_percentage", "")}%
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        if not abstentions_df.empty:
            st.subheader("Abstentions")

            for _, item in abstentions_df.iterrows():
                st.markdown(
                    f"""
                    <div class="abstain-card">
                        <div class="badge" style="background-color:#f59e0b;">ABSTENTION</div>
                        <h4>User {item.get("user_id", "")} | {item.get("domain", "")}</h4>
                        <p>{item.get("message", "")}</p>
                        <p class="small-text">{item.get("reason", "")}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # -----------------------------
    # TAB 3: ANOMALIES
    # -----------------------------
    with tab3:
        st.subheader("Anomaly Detection")

        if anomalies_df.empty:
            st.success("No unusual behavior detected.")
        else:
            for _, item in anomalies_df.iterrows():
                st.markdown(
                    f"""
                    <div class="anomaly-card">
                        <div class="badge" style="background-color:#ef4444;">ANOMALY</div>
                        <h4>User {item.get("user_id", "")} | {item.get("domain", "")}</h4>
                        <p><b>Date:</b> {item.get("date", "")}</p>
                        <p><b>Insight:</b> {item.get("insight", "")}</p>
                        <p><b>Evidence:</b> {item.get("evidence", "")}</p>
                        <p class="small-text">
                            Confidence: {item.get("confidence", "")} |
                            Z-score: {item.get("z_score", "")}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # -----------------------------
    # TAB 4: RAW DATA
    # -----------------------------
    with tab4:
        st.subheader("Dataset Preview")
        st.dataframe(df, use_container_width=True)

        st.subheader("Generated Report Preview")
        st.json(report)


# -----------------------------
# GENERATE REPORT ONLY WHEN BUTTON IS CLICKED
# -----------------------------
if run_button:
    try:
        input_path = get_input_path(uploaded_file, default_path)

        final_output_path = resolve_project_path(output_path)
        final_output_path.parent.mkdir(parents=True, exist_ok=True)

        df = load_data(input_path)
        report = generate_report(input_path, str(final_output_path))

        st.session_state.df = df
        st.session_state.report = report
        st.session_state.report_generated = True
        st.session_state.last_output_path = str(final_output_path)

        st.success(f"Report saved successfully to {final_output_path}")

    except Exception as error:
        st.session_state.report_generated = False
        st.error("Something went wrong while generating the dashboard.")
        st.exception(error)


# -----------------------------
# DISPLAY DASHBOARD FROM SESSION STATE
# -----------------------------
if st.session_state.report_generated:
    render_dashboard(
        st.session_state.df,
        st.session_state.report,
    )

else:
    st.info("Upload a CSV file or click **Generate Insights** from the sidebar.")