import os
import pandas as pd
import streamlit as st
import sys
import requests
import io

# Ensure the src directory is in the path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.scheduler import scheduler as sched
from src.utils.plot_generator import generate_all_plots

st.set_page_config(page_title="Green AI Scheduler", layout="wide")

st.title("Green AI Dashboard")

# ---------------- Upload Section ----------------
st.sidebar.header("Upload Data")
jobs_file = st.sidebar.file_uploader("Job Trace CSV", type="csv")
solar_file = st.sidebar.file_uploader("Solar Profile CSV", type="csv")

# Load default data if no file uploaded
if jobs_file:
    jobs_df = pd.read_csv(jobs_file, parse_dates=["timestamp"])
else:
    jobs_df = pd.read_csv("data/inference_jobs.csv", parse_dates=["timestamp"])

if solar_file:
    solar_df = pd.read_csv(solar_file, parse_dates=["timestamp"])
else:
    solar_df = pd.read_csv("data/solar_generation.csv", parse_dates=["timestamp"])

carbon_df = pd.read_csv("data/carbon_intensity.csv", parse_dates=["timestamp"])

# ---------------- Sensitivity Controls ----------------
st.sidebar.header("Sensitivity Simulation")
solar_kw = st.sidebar.slider("Solar kW per Job", min_value=0.0, max_value=1.0, value=float(sched.SOLAR_KW_PER_JOB), step=0.01)
max_delay = st.sidebar.slider("Max Delay Hours", min_value=0, max_value=12, value=int(sched.MAX_DELAY_HOURS))

# ---------------- Scheduler Trigger ----------------
if st.sidebar.button("Run Scheduler"):
    if jobs_file:
        jobs_file.seek(0)
        jobs_src = jobs_file
    else:
        jobs_src = open("data/inference_jobs.csv", "rb")

    if solar_file:
        solar_file.seek(0)
        solar_src = solar_file
    else:
        solar_src = open("data/solar_generation.csv", "rb")

    carbon_src = open("data/carbon_intensity.csv", "rb")

    response = requests.post(
        "http://127.0.0.1:8000/simulate",
        files={"jobs": jobs_src, "solar": solar_src, "carbon": carbon_src},
    )

    if not isinstance(jobs_file, type(None)):
        pass
    else:
        jobs_src.close()
    if not isinstance(solar_file, type(None)):
        pass
    else:
        solar_src.close()
    carbon_src.close()

    if not response.ok:
        try:
            response == response.json()
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            st.error(f"Error: {e.response.text}")
            st.stop()
    if response.status_code != 200:
        st.error(f"Error: {response.text}")
        st.stop()
    st.success("Scheduler executed successfully!")

    result_json = response.json()
    result_df = pd.DataFrame(result_json["schedule"])
    metrics = result_json.get("metrics", {})

    result_df.to_csv("results/execution_schedule.csv", index=False)
    st.success(
        "Schedule generated via API and saved to results/execution_schedule.csv"
    )
    # Calculate baseline carbon for jobs
    carbon_index = carbon_df.set_index("timestamp")["carbon_intensity"]
    jobs_df["baseline_carbon"] = jobs_df["timestamp"].dt.floor("H").map(carbon_index)
    generate_all_plots(result_df, jobs_df, carbon_df, output_dir="plots")
    st.success("Plots generated successfully!")

# ---------------- Display Results ----------------
    st.subheader("Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Jobs", metrics.get("total_jobs", len(result_df)))
    col2.metric(
        "Emissions Saved (gCO2)", f"{metrics.get('emissions_saved', 0):.2f}"
    )
    col3.metric("% Delayed Jobs", f"{metrics.get('delayed_pct', 0):.1f}%")

    st.download_button(
        label="📥 Download Schedule CSV",
        data=result_df.to_csv(index=False),
        file_name="green_ai_schedule.csv",
        mime="text/csv",
    )

    # ---------------- Visualizations ----------------
    st.header("Plots")
    plot_files = [
        "Co2_Baseline_vs_Scheduled.png",
        "carbon_intensity.png",
        "Job_Execution_Delay.png",
        "energy_source_breakdown.png",
        "Job_Timeline.png",
        "job_delay_distribution.png",
        "Solar_Power_Used_Per_Hour.png",
    ]
    for pf in plot_files:
        img_path = os.path.join("plots", pf)
        if os.path.exists(img_path):
            st.image(img_path, caption=pf)
        else:
            st.warning(f"Plot {pf} not found")
