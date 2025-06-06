from __future__ import annotations

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import pandas as pd
from datetime import datetime

from scheduler.scheduler import schedule_jobs, CARBON_PATH, SOLAR_PATH

app = FastAPI(title="Green AI Scheduler API")

# In-memory storage for metrics from the latest run
_last_metrics: dict[str, float] | None = None


def _load_default_datasets() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load carbon intensity and solar generation data from default CSVs."""
    carbon_df = pd.read_csv(CARBON_PATH, parse_dates=["timestamp"])
    solar_df = pd.read_csv(SOLAR_PATH, parse_dates=["timestamp"])
    return carbon_df, solar_df


def _compute_metrics(result_df: pd.DataFrame, jobs_df: pd.DataFrame) -> dict[str, float]:
    """Return basic scheduler metrics."""
    carbon_index = (
        pd.read_csv(CARBON_PATH, parse_dates=["timestamp"])  # baseline carbon
        .set_index("timestamp")["carbon_intensity"]
    )
    jobs_df["baseline_carbon"] = jobs_df["timestamp"].dt.floor("H").map(carbon_index)

    baseline = (jobs_df["baseline_carbon"] * jobs_df["expected_power_kwh"]).sum()
    scheduled = (result_df["carbon_intensity"].clip(lower=0) * result_df["power_kwh"]).sum()
    savings = baseline - scheduled
    delayed_pct = float((result_df["delay_hours"] > 0).mean() * 100)

    return {
        "total_jobs": len(result_df),
        "emissions_saved": float(savings),
        "delayed_pct": delayed_pct,
    }


class Job(BaseModel):
    """Representation of a single inference job."""

    job_id: str
    timestamp: datetime  # <-- Use datetime, not pd.Timestamp
    expected_power_kwh: float

    class Config:
        arbitrary_types_allowed = True


@app.post("/schedule")
def schedule_endpoint(jobs: list[Job]):
    """Schedule a batch of jobs and return the execution plan."""
    jobs_df = pd.DataFrame([job.dict() for job in jobs])
    jobs_df["timestamp"] = pd.to_datetime(jobs_df["timestamp"])  # Ensure pandas Timestamps
    carbon_df, solar_df = _load_default_datasets()

    result_df = schedule_jobs(carbon_df, solar_df, jobs_df)
    global _last_metrics
    _last_metrics = _compute_metrics(result_df, jobs_df)

    return {
        "schedule": result_df.to_dict(orient="records"),
        "metrics": _last_metrics,
    }


@app.get("/metrics")
def metrics_endpoint():
    """Return metrics from the last scheduler run."""
    if _last_metrics is None:
        raise HTTPException(status_code=404, detail="No metrics available")
    return _last_metrics


@app.post("/simulate")
async def simulate_endpoint(
    jobs: UploadFile = File(...),
    solar: UploadFile = File(...),
    carbon: UploadFile = File(...),
):
    """Run a simulation with uploaded CSV datasets."""
    jobs_df = pd.read_csv(jobs.file, parse_dates=["timestamp"])
    solar_df = pd.read_csv(solar.file, parse_dates=["timestamp"])
    carbon_df = pd.read_csv(carbon.file, parse_dates=["timestamp"])

    result_df = schedule_jobs(carbon_df, solar_df, jobs_df)
    metrics = _compute_metrics(result_df, jobs_df)

    return {
        "schedule": result_df.to_dict(orient="records"),
        "metrics": metrics,
    }

