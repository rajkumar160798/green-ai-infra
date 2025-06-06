# green-ai-infra
green-ai-infra

```text
green-ai-infra/

├── README.md                # Project overview and usage instructions
├── requirements.txt         # Python dependencies
├── .env.example             # Sample env file for API keys
│
├── 📁 data/                 # Datasets (simulated or real)
│   ├── solar_profile.csv
│   └── carbon_intensity.csv
│
├── 📁 src/                  # Core source code
│   ├── scheduler/           # Carbon-aware job scheduler
│   │   ├── scheduler.py
│   │   └── queue_manager.py
│   ├── monitor/             # GPU/energy/emission monitors
│   │   ├── energy_logger.py
│   │   └── gpu_stats.py
│   ├── api/                 # External API clients
│   │   └── carbon_api.py    # ElectricityMap or WattTime API client
│   ├── simulate/            # Workload simulator
│   │   └── inference_job.py
│   └── utils/               # Shared utility functions
│       └── time_utils.py
│
├── 📁 notebooks/            # Jupyter notebooks for analysis and visualization
│   └── emissions_analysis.ipynb
│
├── 📁 dashboard/            # Optional frontend (Streamlit/React)
│   └── streamlit_app.py     # Streamlit app for results visualization
│
├── 📁 results/              # Output plots and logs
│   ├── emission_savings.png
│   └── delay_vs_emissions.csv
│
└── 📁 tests/                # Unit tests (pytest)
    └── test_scheduler.py

```

## Streamlit Dashboard

Launch the interactive dashboard with:

```bash
streamlit run dashboard/streamlit_app.py
```