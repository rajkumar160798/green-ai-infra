import pandas as pd
from datetime import datetime, timedelta

# Configurable parameters
CARBON_THRESHOLD = 250  # gCO2eq/kWh
SOLAR_KW_PER_JOB = 0.05
MAX_DELAY_HOURS = 4

# File paths
CARBON_PATH = '../data/carbon_intensity.csv'
SOLAR_PATH = '../data/solar_generation.csv'
JOBS_PATH = '../data/inference_jobs.csv'
OUTPUT_PATH = '../results/execution_schedule.csv'

def load_data():
    carbon_df = pd.read_csv(CARBON_PATH, parse_dates=['timestamp'])
    solar_df = pd.read_csv(SOLAR_PATH, parse_dates=['timestamp'])
    jobs_df = pd.read_csv(JOBS_PATH, parse_dates=['timestamp'])
    return carbon_df, solar_df, jobs_df

def schedule_jobs(carbon_df, solar_df, jobs_df):
    execution_log = []

    for _, job in jobs_df.iterrows():
        job_time = job['timestamp']
        power_needed = job['expected_power_kwh']
        job_run = False

        for delay in range(MAX_DELAY_HOURS + 1):
            scheduled_time = job_time + timedelta(hours=delay)
            carbon_row = carbon_df[carbon_df['timestamp'] == scheduled_time]
            solar_row = solar_df[solar_df['timestamp'] == scheduled_time]

            if not carbon_row.empty and not solar_row.empty:
                carbon_val = carbon_row.iloc[0]['carbon_intensity']
                solar_val = solar_row.iloc[0]['solar_kw_available']

                if carbon_val <= CARBON_THRESHOLD or solar_val >= SOLAR_KW_PER_JOB:
                    execution_log.append({
                        'job_id': job['job_id'],
                        'original_time': job_time,
                        'scheduled_time': scheduled_time,
                        'delay_hours': delay,
                        'carbon_intensity': carbon_val,
                        'solar_kw_used': min(solar_val, SOLAR_KW_PER_JOB),
                        'power_kwh': power_needed,
                        'source': 'solar' if solar_val >= SOLAR_KW_PER_JOB else 'grid'
                    })
                    job_run = True
                    break

        if not job_run:
            print(f"⚠️ Job {job['job_id']} could not be scheduled within the delay limit.")
            # Fallback to the original job time if no suitable delay was found
            job_time = job['timestamp']
            # Use the carbon and solar data at the original job time
            fallback_row = carbon_df[carbon_df['timestamp'] == job_time]
            fallback_solar = solar_df[solar_df['timestamp'] == job_time]
            fallback_carbon = fallback_row.iloc[0]['carbon_intensity'] if not fallback_row.empty else -1
            fallback_solar_val = fallback_solar.iloc[0]['solar_kw_available'] if not fallback_solar.empty else 0.0

            execution_log.append({
                'job_id': job['job_id'],
                'original_time': job_time,
                'scheduled_time': job_time,
                'delay_hours': 0,
                'carbon_intensity': fallback_carbon,
                'solar_kw_used': 0.0,
                'power_kwh': power_needed,
                'source': 'grid'
            })

    return pd.DataFrame(execution_log)

def main():
    carbon_df, solar_df, jobs_df = load_data()
    result_df = schedule_jobs(carbon_df, solar_df, jobs_df)
    result_df.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Schedule saved to {OUTPUT_PATH}")
    print(result_df.head())

if __name__ == "__main__":
    main()
# This code is designed to schedule inference jobs based on carbon intensity and solar generation data.
# It loads the necessary data, checks conditions for scheduling, and outputs a schedule with details.
# The code is modular and can be easily adjusted for different thresholds or parameters.
# The output includes the job ID, original time, scheduled time, delay hours, carbon intensity,