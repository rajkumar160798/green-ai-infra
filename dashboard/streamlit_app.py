import os
import pandas as pd
import streamlit as st
import sys

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
    # override parameters
    sched.SOLAR_KW_PER_JOB = solar_kw
    sched.MAX_DELAY_HOURS = max_delay

    result_df = sched.schedule_jobs(carbon_df, solar_df, jobs_df)
    result_df.to_csv("results/execution_schedule.csv", index=False)
    st.success("Schedule generated and saved to results/execution_schedule.csv")

    # Calculate baseline and scheduled emissions
    carbon_index = carbon_df.set_index("timestamp")["carbon_intensity"]
    jobs_df["baseline_carbon"] = jobs_df["timestamp"].dt.floor("H").map(carbon_index)
    baseline_emissions = (jobs_df["baseline_carbon"] * jobs_df["expected_power_kwh"]).sum()
    result_df["scheduled_emissions"] = result_df["carbon_intensity"].clip(lower=0) * result_df["power_kwh"]
    scheduled_emissions = result_df["scheduled_emissions"].sum()
    savings = baseline_emissions - scheduled_emissions

    delayed_pct = (result_df["delay_hours"] > 0).mean() * 100

    # 📈 Generate fresh plots
    generate_all_plots(result_df, jobs_df, carbon_df, output_dir="plots")
    st.success("Plots generated successfully!")

# ---------------- Display Results ----------------
    st.subheader("Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Jobs", len(result_df))
    col2.metric("Emissions Saved (gCO2)", f"{savings:.2f}")
    col3.metric("% Delayed Jobs", f"{delayed_pct:.1f}%")

    # ---------------- Visualizations ----------------
    st.header("Plots")
    plot_files = [
        "Co2_Baseline_vs_Scheduled.png",
        "carbon_intensity.png",
        "Job_Execution_Delay.png",
        "energy_souce_breakdown.png",
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
