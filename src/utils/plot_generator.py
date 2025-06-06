import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def generate_all_plots(result_df: pd.DataFrame, jobs_df: pd.DataFrame, carbon_df: pd.DataFrame, output_dir="plots"):
    os.makedirs(output_dir, exist_ok=True)

    # 1. CO2 Baseline vs Scheduled
    baseline_emissions = (jobs_df["baseline_carbon"] * jobs_df["expected_power_kwh"]).sum()
    scheduled_emissions = (result_df["carbon_intensity"].clip(lower=0) * result_df["power_kwh"]).sum()
    plt.figure()
    plt.bar(["Baseline", "Scheduled"], [baseline_emissions, scheduled_emissions], color=["#69b3a2", "#e9967a"])
    plt.ylabel("kg CO₂")
    plt.title("CO₂ Emissions: Baseline vs Scheduled")
    plt.savefig(os.path.join(output_dir, "Co2_Baseline_vs_Scheduled.png"))
    plt.close()

    # 2. Carbon Intensity Distribution
    plt.figure()
    sns.histplot(result_df["carbon_intensity"], kde=True, bins=30)
    plt.title("Carbon Intensity at Execution Time")
    plt.xlabel("gCO₂/kWh")
    plt.ylabel("Job Count")
    plt.savefig(os.path.join(output_dir, "carbon_intensity.png"))
    plt.close()

    # 3. Job Delay Distribution
    plt.figure()
    result_df["delay_hours"].value_counts().sort_index().plot(kind="bar")
    plt.title("Job Delay Distribution")
    plt.xlabel("Delay (hours)")
    plt.ylabel("Number of Jobs")
    plt.savefig(os.path.join(output_dir, "job_delay_distribution.png"))
    plt.close()

    # 4. Energy Source Breakdown
    plt.figure()
    source_counts = result_df["source"].value_counts()
    source_counts.plot(kind="pie", autopct='%1.1f%%', startangle=90, colors=["#ff9999", "#66b3ff"])
    plt.title("Energy Source Breakdown")
    plt.ylabel("")  # Hide the y-label for pie chart
    plt.savefig(os.path.join(output_dir, "energy_source_breakdown.png"))
    plt.close()
    # 5. Job  Execution Timeline
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=result_df, x="scheduled_time", y="job_id", hue="source", style="source", s=100)
    plt.title("Job Execution Timeline")
    plt.xlabel("Scheduled Time")
    plt.ylabel("Job ID")
    plt.xticks(rotation=45)
    plt.legend(title="Energy Source")
    plt.savefig(os.path.join(output_dir, "job_timeline.png"))
    plt.close()
    # 6. Job Execution Delay   
    plt.figure(figsize=(12, 6))
    sns.barplot(data=result_df, x="job_id", y="delay_hours", hue="source", palette=["#ff9999", "#66b3ff"])
    plt.title("Job Execution Delay by Source")
    plt.xlabel("Job ID")
    plt.ylabel("Delay (hours)")
    plt.xticks(rotation=45)
    plt.legend(title="Energy Source")
    plt.savefig(os.path.join(output_dir, "job_execution_delay.png"))
    plt.close()