# Climate–Health and Health Systems Analytics Platform — revised final build

This build refines the current platform without deleting the core structure.

## Main improvements
- clearer dual pathways on the homepage:
  - Visualise existing or uploaded data
  - Create a new data job
- expanded Explore workflow with nested statistical-analysis tabs
- AI-guided analysis free-text support
- figure styling and export panel with journal-style presets
- broader export support: PNG, SVG, PDF, CSV, Excel
- upgraded regression, time-series, and advanced analysis options

## Notes
Some advanced methods are implemented fully, while others are provided as guided partial workflows inside the app so the current version remains stable and usable.


## Final refinements in this version
- homepage organised around two clear pathways
- analysis suite surfaced clearly on the homepage and inside Explore
- documentation explains where to find Summary, Correlation, Regression, Time Series, Spatial, Advanced, AI-Guided Analysis, and Figure & Data Export
- Create Data Job includes region/spatial unit type and temporal resolution
- TIFF export added when Pillow is available


Updated package built from the full version 19 project with latest fixes for homepage cleanup, Health in REACH dataset chooser, unique spatial view keys, multi-panel export controls, correct funder logos, and a static spatial Multi-Hazard preview.