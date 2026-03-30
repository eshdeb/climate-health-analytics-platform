# Climate–Health and Health Systems Analytics Platform — Version 10

## Final pre-backend release
This is the final public-facing version before backend engineering and live processing integration.

## Key features
- generic homepage and sidebar modules: Flood, Heatwaves, Multi-Hazard
- Brazil and Zambia positioned as case-study showcase datasets inside pages and documentation
- users can choose demo datasets or upload their own CSV/ZIP files
- supports multiple demo files per workflow
- filtered CSV download and narrative PDF download
- AI guidance and interpretation support
- AOI-based job specification page for later backend integration

## Demo data expected in `sample_data/`
- `demo_brazil_flood.csv`
- `demo_brazil_flood_2.csv`
- `demo_brazil_heat.csv`
- `demo_brazil_heat_2.csv`
- `demo_zambia_multihazard.csv`
- `demo_zambia_multihazard_month.csv`

## Run
python -m pip install -r requirements.txt
python -m streamlit run app.py
