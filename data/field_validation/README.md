# Field validation template (rabi drought v2)

One row per field visit. **Leave unknown values empty** - never fill with a default
("healthy", 0, "rainfed"). Allowed values:

- `crop_stage`: sowing / emergence / vegetative / flowering / pod-grain filling / maturity / harvested / unknown
- `water_source`: rainfed / borewell / canal / tank / mixed / unknown
- `irrigated_in_last_14_days`, `irrigation_supply_interruption`: yes / no / unknown
- `observed_stress`: none / mild / moderate / severe / crop failed / unknown
- `stress_cause_reported`: water shortage / pest / disease / harvest-maturity / irrigation failure / other / unknown
- `evidence_source`: field visit / farmer interview / UAV / extension officer / other
- Dates ISO `YYYY-MM-DD`; coordinates WGS84 decimal degrees; soil moisture with unit, depth and method.

Use the 1,350 C3 point IDs (`data/gee_exports/C3_points.csv`) or the UAV field IDs where possible.
These records are the only route to field-level drought accuracy; nothing in this repository
substitutes for them.
