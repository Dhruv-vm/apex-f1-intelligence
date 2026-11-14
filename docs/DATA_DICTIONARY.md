# APEX — F1 Intelligence: Data Dictionary

> **Status:** PROVISIONAL SPECIFICATION — Field definitions, units, and availability checkpoints represent planned schemas subject to verification during Milestone 1 data availability audits.

---

## 1. Field Documentation Template

Every entity in APEX is documented according to this standardized structure:

| Field Name | Type | Unit / Format | Time Semantics | Source Feed | Availability Checkpoint | Nullable? | Validation Rules |
|---|---|---|---|---|---|---|---|
| `field_name` | DataType | e.g. `ms`, `km/h`, `ISO-8601` | Event vs Ingestion time | Provider | Checkpoint where available | Yes / No | Logical constraints |

---

## 2. Core Entities & Field Specifications

### 2.1 Entity: `Circuit`
Represents permanent race track venues.

| Field Name | Type | Unit / Format | Time Semantics | Source Feed | Availability Checkpoint | Nullable? | Validation Rules |
|---|---|---|---|---|---|---|---|
| `circuit_id` | String | Slug (e.g. `silverstone`) | Static | Jolpica / FastF1 | Pre-Weekend | No | Unique, alphanumeric lowercase |
| `circuit_name` | String | Text | Static | Jolpica | Pre-Weekend | No | Non-empty string |
| `country` | String | ISO-3166-1 alpha-3 | Static | Jolpica | Pre-Weekend | No | 3 uppercase letters |
| `track_length_km` | Float | Kilometers (`km`) | Static | FastF1 / FIA | Pre-Weekend | No | $3.0 \le x \le 8.0$ |
| `corners_count` | Integer | Count | Static | FIA Docs | Pre-Weekend | No | $x > 0$ |
| `altitude_m` | Float | Meters (`m`) | Static | Track Survey | Pre-Weekend | Yes | $-30 \le x \le 2500$ |
| `avg_pit_delta_s` | Float | Seconds (`s`) | Rolling Historical | Historical Store | Pre-Weekend | Yes | $15.0 \le x \le 35.0$ |

---

### 2.2 Entity: `SeasonEvent`
Represents an individual Grand Prix round within a championship calendar.

| Field Name | Type | Unit / Format | Time Semantics | Source Feed | Availability Checkpoint | Nullable? | Validation Rules |
|---|---|---|---|---|---|---|---|
| `event_id` | String | Slug (`YYYY_round_slug`) | Calendar release | Jolpica | Pre-Weekend | No | Matches regex `^\d{4}_\d{2}_[a-z0-9_-]+$` |
| `year` | Integer | Year (`YYYY`) | Calendar release | Jolpica | Pre-Weekend | No | $1950 \le x \le 2030$ |
| `round_number` | Integer | Index ($1 \dots 25$) | Calendar release | Jolpica | Pre-Weekend | No | $1 \le x \le 30$ |
| `official_name` | String | Text | Calendar release | Jolpica | Pre-Weekend | No | Non-empty string |
| `format` | String | Enum: `standard`, `sprint` | Calendar release | FIA Regulations | Pre-Weekend | No | Member of allowed set |
| `date_start` | Timestamp | ISO-8601 UTC | Scheduled | Jolpica | Pre-Weekend | No | Valid UTC timestamp |

---

### 2.3 Entity: `Session`
Represents a track session (e.g., FP1, FP2, Qualifying, Race).

| Field Name | Type | Unit / Format | Time Semantics | Source Feed | Availability Checkpoint | Nullable? | Validation Rules |
|---|---|---|---|---|---|---|---|
| `session_id` | String | Slug (`YYYY_round_session`) | Scheduled | FastF1 / Jolpica | Pre-Weekend | No | Unique |
| `event_id` | String | Foreign Key -> `SeasonEvent`| Scheduled | Jolpica | Pre-Weekend | No | Valid `event_id` |
| `session_type` | String | Enum: `FP1`, `FP2`, `FP3`, `Q`, `SQ`, `S`, `R` | Scheduled | FastF1 | Pre-Weekend | No | Allowed enum |
| `scheduled_start`| Timestamp | ISO-8601 UTC | Scheduled | Jolpica | Pre-Weekend | No | Valid UTC timestamp |
| `actual_start` | Timestamp | ISO-8601 UTC | Session Start | FastF1 | Post-Session | Yes | After `scheduled_start - 1h` |
| `actual_end` | Timestamp | ISO-8601 UTC | Session End | FastF1 | Post-Session | Yes | Greater than `actual_start` |

---

### 2.4 Entity: `LapRecord`
Lap-level performance, compound state, and track status.

| Field Name | Type | Unit / Format | Time Semantics | Source Feed | Availability Checkpoint | Nullable? | Validation Rules |
|---|---|---|---|---|---|---|---|
| `lap_id` | String | UUID or composite key | Event Time | FastF1 | In-Session / Post | No | Unique per driver/session/lap |
| `session_id` | String | Foreign Key -> `Session` | Static | FastF1 | Pre-Session | No | Valid `session_id` |
| `driver_number`| Integer | Integer ($1 \dots 99$) | Static | FastF1 | Pre-Session | No | In driver roster |
| `lap_number` | Integer | Lap count ($1 \dots 80$) | Event Time | FastF1 | Checkpoint Lap | No | $1 \le x \le 100$ |
| `lap_time_ms` | Integer | Milliseconds (`ms`) | Lap Completion | FastF1 | Lap Completion | Yes | $50000 \le x \le 200000$ or null (in/out) |
| `sector_1_ms` | Integer | Milliseconds (`ms`) | Sector Completion | FastF1 | Sector 1 Cutoff | Yes | $10000 \le x \le 80000$ |
| `sector_2_ms` | Integer | Milliseconds (`ms`) | Sector Completion | FastF1 | Sector 2 Cutoff | Yes | $15000 \le x \le 80000$ |
| `sector_3_ms` | Integer | Milliseconds (`ms`) | Sector Completion | FastF1 | Sector 3 Cutoff | Yes | $10000 \le x \le 80000$ |
| `compound` | String | Enum: `SOFT`, `MEDIUM`, `HARD`, `INTERMEDIATE`, `WET` | Stint Start | FastF1 | Pit Exit / Outlap | Yes | Valid compound |
| `tire_age_laps`| Integer | Laps run on set | Stint Start | FastF1 | Lap Start | No | $x \ge 0$ |
| `is_pit_in_lap`| Boolean | True / False | Lap Completion | FastF1 | Lap Completion | No | Boolean |
| `is_pit_out_lap`| Boolean | True / False | Lap Start | FastF1 | Lap Start | No | Boolean |
| `track_status` | String | Flags (`1`=Green, `4`=SC, `6`=VSC, `5`=Red) | Event Time | FastF1 / OpenF1 | Live / Post | No | Bitmask or string code |

---

### 2.5 Entity: `TelemetrySample`
Synchronized high-frequency time series (typically sampled at 10 Hz to 50 Hz).

| Field Name | Type | Unit / Format | Time Semantics | Source Feed | Availability Checkpoint | Nullable? | Validation Rules |
|---|---|---|---|---|---|---|---|
| `sample_id` | String | UUID | Event Time | FastF1 / OpenF1 | Post-Session / Live | No | Unique |
| `lap_id` | String | Foreign Key -> `LapRecord` | Event Time | FastF1 | Live / Post | No | Valid `lap_id` |
| `elapsed_time_s`| Float | Seconds (`s`) | Session Time | FastF1 | Live / Post | No | Monotonically increasing per lap |
| `distance_m` | Float | Meters (`m`) | Distance along track | FastF1 | Live / Post | No | $0.0 \le x \le track\_length$ |
| `speed_kmh` | Float | Kilometers per hour (`km/h`) | Instantaneous | FastF1 | Live / Post | No | $0.0 \le x \le 380.0$ |
| `throttle_pct` | Float | Percent ($0.0 \dots 100.0$) | Instantaneous | FastF1 | Live / Post | No | $0.0 \le x \le 100.0$ |
| `brake_flag` | Boolean | True (Active) / False | Instantaneous | FastF1 | Live / Post | No | Binary flag |
| `gear` | Integer | Index ($1 \dots 8$, `0`=Neutral, `-1`=Reverse) | Instantaneous | FastF1 | Live / Post | No | $-1 \le x \le 8$ |
| `rpm` | Integer | Engine RPM | Instantaneous | FastF1 | Live / Post | No | $0 \le x \le 16000$ |
| `drs_status` | Integer | Enum / Flag ($0 \dots 14$) | Instantaneous | FastF1 | Live / Post | No | Defined DRS state |

---

### 2.6 Entity: `ForecastSnapshot`
Immutably serialized output of a model at an explicit information cutoff.

| Field Name | Type | Unit / Format | Time Semantics | Source Feed | Availability Checkpoint | Nullable? | Validation Rules |
|---|---|---|---|---|---|---|---|
| `snapshot_id` | String | UUID | Prediction Time | Internal Forecaster | Output Time | No | Unique |
| `event_id` | String | Foreign Key -> `SeasonEvent`| Prediction Time | Internal Forecaster | Output Time | No | Valid `event_id` |
| `checkpoint_id`| String | Enum: `T0_PRE_WEEKEND`, `T1_POST_FP1`, `T2_POST_FP2`, `T3_POST_FP3`, `T4_POST_QUALI`, `T5_PRE_RACE`, `T6_LAP_K` | Prediction Time | Internal Forecaster | Output Time | No | Valid checkpoint enum |
| `cutoff_utc` | Timestamp | ISO-8601 UTC | Information Boundary | Internal Forecaster | Output Time | No | Maximum timestamp permitted |
| `model_id` | String | Semantic ID (e.g. `lgbm_seq_v1.0.2`) | Stamped | Model Registry | Output Time | No | Valid model version |
| `target_name` | String | Enum: `RACE_WINNER`, `PODIUM`, `TOP_6`, `TOP_10`, `DNF` | Stamped | Model Registry | Output Time | No | Valid target enum |
| `probabilities`| JSON / Dict | Map: `{driver_id: float}` | Stamped | Model Output | Output Time | No | Values sum to 1.0 (for winner) or bounded [0,1] |
| `brier_score` | Float | Score ($0.0 \dots 2.0$) | Post-Event Evaluation | Evaluation Engine | Post-Race Evaluation | Yes | Computed only after ground truth |

---

### 2.7 Entity: `PreRaceFeatureVector` ($T_5$ Forecast Checkpoint)
The 16 verified static features used in `EXP-0002` (Models 3 and 4) to predict race victory prior to formation lap.

| Field Name | Category | Type | Unit / Format | Availability Checkpoint | Anti-Leakage Constraint / Definition |
|---|---|---|---|---|---|
| `effective_grid` | Starting Grid | Float | Position ($1.0 \dots 25.0$) | $T_5$ (Final Grid) | Actual positive grid position, or $\max(\text{grid}_{>0}) + 1$ for grid-zero entries. |
| `log_grid` | Starting Grid | Float | Natural log | $T_5$ | $\ln(\text{effective\_grid})$. Nonlinear compression of grid disadvantage. |
| `is_front_row` | Starting Grid | Integer | Binary (`0` or `1`) | $T_5$ | `1` if $\text{effective\_grid} \in \{1.0, 2.0\}$, else `0`. |
| `is_pole` | Starting Grid | Integer | Binary (`0` or `1`) | $T_5$ | `1` if $\text{effective\_grid} == 1.0$, else `0`. |
| `is_grid_zero` | Starting Grid | Integer | Binary (`0` or `1`) | $T_5$ | `1` if API raw grid was 0 (provisional pit start / grid penalty proxy). |
| `driver_prior_races` | Driver Form | Float | Count | $T_0$ | Number of historical races entered strictly prior to current Grand Prix. |
| `driver_win_rate_all` | Driver Form | Float | Rate ($0.0 \dots 1.0$) | $T_0$ | Historical career wins divided by prior starts strictly prior to current race. |
| `driver_win_rate_last5`| Driver Form | Float | Rate ($0.0 \dots 1.0$) | $T_0$ | Wins across the driver's previous 5 completed Grand Prix entries. |
| `driver_mean_finish_last5` | Driver Form | Float | Position ($1.0 \dots 20.0$) | $T_0$ | Mean finishing position across previous 5 finishes (fallback: `20.0` for cold start). |
| `driver_finish_std_last5` | Driver Form | Float | Standard Deviation | $T_0$ | Sample standard deviation of finishes across previous 5 races (`0.0` if $<2$ finishes). |
| `constructor_prior_races` | Constructor Form| Float | Count | $T_0$ | Number of historical Grand Prix weekends entered by constructor prior to current race. |
| `constructor_win_rate_all` | Constructor Form| Float | Rate ($0.0 \dots 1.0$) | $T_0$ | Historical constructor wins divided by prior weekends entered. |
| `constructor_win_rate_last5` | Constructor Form| Float | Rate ($0.0 \dots 1.0$) | $T_0$ | Constructor wins across the team's previous 5 Grand Prix weekends. |
| `constructor_mean_finish_last5` | Constructor Form| Float | Position ($1.0 \dots 20.0$) | $T_0$ | Mean finishing position of all constructor cars over last 5 weekends (fallback: `20.0`). |
| `driver_mean_points_last5` | Points Form | Float | Points | $T_0$ | Mean championship points scored per race over driver's last 5 entries. |
| `constructor_mean_points_last5` | Points Form | Float | Points | $T_0$ | Mean team points scored per weekend over constructor's last 5 weekends. |
