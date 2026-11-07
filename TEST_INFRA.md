# Orange EcoMobility Intelligence (OEMI) — Test Infrastructure Specification (`TEST_INFRA.md`)

**Target Project**: Orange EcoMobility Intelligence (OEMI)  
**Track**: Dual-Track End-to-End (E2E) & Integration Testing  
**Authors**: Pôle QA & Independent E2E Test Writers (`@qa-e2e`, `test_writer_e2e_1`)  
**Standard**: Opaque-Box, Requirement-Driven, Zero Implementation Internals Dependency  
**Version**: 1.1.0 (Full 4-Tier Test Infrastructure)

---

## 1. Test Architecture & Executive Summary

The OEMI E2E Test Suite provides an independent, requirement-driven opaque-box verification framework for the entire Orange EcoMobility Intelligence decision-support platform. It operates strictly through external interface contracts:
- Public HTTP REST API endpoints (`/api/health`, `/api/zones`, `/api/mobility`, `/api/ipet`, `/api/predictions`, `/api/reports`, etc.)
- PostGIS database spatial queries and schema validation
- Generated binary and tabular artifacts (PDF reports via ReportLab, Excel workbooks via OpenPyXL)
- GeoJSON spatial contracts in WGS 84 (EPSG:4326)

### 1.1 Architectural Layout
```
d:\Workspace\Hackathon OCI\
├── TEST_INFRA.md                        # This test infrastructure specification
├── TEST_READY.md                        # Final test certification & execution summary
└── tests_e2e/                           # Opaque-box E2E test suite root
    ├── conftest.py                      # Global fixtures, OEMIContractClient (mock/live wrapper), spatial validators
    ├── test_runner.py                   # Standalone CLI test runner with JSON reporting
    ├── test_tier1_features.py           # Tier 1: Core Feature Verification (>=5 tests per feature, 28 features)
    ├── test_tier2_boundaries.py         # Tier 2: Boundary, Negative & Privacy Constraints (k < 15, IPET [0,100])
    ├── test_tier3_combinations.py       # Tier 3: Pairwise & Combinatorial Filter / Weight Permutations
    └── test_tier4_scenarios.py          # Tier 4: Real-World Retailer Siting Decision Workflows (Cocody, Yopougon, Marcory)
```

### 1.2 Dual-Mode Execution (Mock/Contract & Live Backend)
The test suite utilizes `OEMIContractClient` implemented in `tests_e2e/conftest.py`:
1. **Live Mode (`E2E_MODE=live`)**: Probes and tests active FastAPI service endpoints running at `http://127.0.0.1:8000`.
2. **Contract / Reference Mode (`E2E_MODE=mock` or auto-fallback)**: Executes tests against specification-faithful contract fixtures derived directly from `PROJECT.md`, `Technical_Specification.md`, and `mld.md`.
3. **Auto Mode (`E2E_MODE=auto`, default)**: Detects if the backend is reachable at `BACKEND_URL`. If online, runs live HTTP verification; if offline or during milestone scaffolding, verifies the contract interfaces, boundary invariants, and algorithms deterministically.

---

## 2. Testing Methodology

The suite implements four complementary software testing methodologies:

### 2.1 Category-Partition Method (Equivalence Partitioning)
For each API endpoint and analytical feature, the input domain is partitioned into mutually exclusive equivalence classes:
- **Spatial Dimension**:
  - Valid pilot communes: `Cocody`, `Yopougon`, `Marcory`
  - Valid sub-zones: `Angré 7e Tranche`, `Riviera Golf`, `Niangon Nord`, `Zone 4C Biétry`, etc.
  - Invalid communes: Non-existent names (`Atlantis`), adjacent non-pilot communes (`Bouaké`, `Grand-Bassam`), malformed strings.
- **Temporal Dimension**:
  - Commuter Peak Mornings: Weekdays 07h00 - 09h00
  - Commuter Peak Evenings: Weekdays 17h00 - 20h00
  - Commercial Midday: Weekdays & Saturdays 12h00 - 14h00
  - Weekend Shopping: Saturdays & Sundays 10h00 - 18h00
  - Late-Night / Off-Peak: 01h00 - 05h00
- **User Roles & RBAC**:
  - `ADMIN`: Full configuration, simulation, and audit review
  - `ANALYSTE`: Dynamic IPET weight calculation, export PDF/Excel
  - `METIER`: Read-only map visualization, pre-calculated rankings
  - Unauthenticated / Invalid token

### 2.2 Boundary Value Analysis (BVA)
Tests specifically evaluate critical boundaries:
- **Ivorian Law n° 2013-450 k-Anonymity Threshold**:
  - $k = 14$: Value strictly masked (`null`/`None`), `seuil_k_anonymat_valide = False`.
  - $k = 15$: Minimum allowable volume, cleartext exposure, `seuil_k_anonymat_valide = True`.
  - $k = 16$: Normal cleartext exposure.
  - $k = 0$: Legitimate zero count or empty slot.
  - $k < 0$: Negative count rejected as invalid input.
- **IPET Normalization Bounds**:
  - Minimum possible score: strictly bounded at $0.0$.
  - Maximum possible score: strictly bounded at $100.0$.
  - Underflow / Negative indicator values: clamped to $0.0$.
  - Overflow indicator values: clamped to $100.0$.
- **Multicriteria Weights Constraint**:
  - $\sum w_i = 1.0$: Valid.
  - $\sum w_i = 0.999$ or $1.001$: HTTP 422 Unprocessable Entity or strict validation error.
  - Single weight $1.0$, others $0.0$: Extreme valid scenario.
  - Negative weight: HTTP 422 rejected.
- **Geographic Bounding Box**:
  - Pilot bounding box: Longitude $[-4.15, -3.85]$, Latitude $[5.25, 5.45]$.
  - Coordinates outside (e.g. $[2.35, 48.85]$ Paris, $[-5.28, 6.82]$ Yamoussoukro) flagged or rejected.

### 2.3 Pairwise & Combinatorial Testing
Tier 3 tests evaluate orthogonal interactions between multiple subsystems:
- `Commune` $\times$ `Time Slot Profile` (e.g., Cocody residential morning outbound vs Plateau business morning inbound)
- `Siting Sector` $\times$ `Custom Weight Profile` (e.g., Discount Supermarket with high demography weight vs Gourmet Express with high competition sensitivity)
- `Forecasting Model` $\times$ `Horizon` (D-7 baseline vs Prophet vs XGBoost across 7-day future horizon)
- `Target Zone Selection` $\times$ `Export Modality` (PDF ReportLab vector output vs XLSX OpenPyXL multi-tab workbook)

### 2.4 Real-World Siting Workflows (Scenario Testing)
Tier 4 reproduces complete commercial end-to-end user journeys:
1. **Scenario 1**: Siting a Flagship Hypermarket in Cocody (comparing Angré vs Deux Plateaux vs Riviera).
2. **Scenario 2**: Hard-Discount Supermarket Network Expansion in Yopougon (Niangon vs Siporex vs Bel Air).
3. **Scenario 3**: Express Gourmet Convenience Store in Marcory (Zone 4 Biétry commercial saturation vs residential pocket).
4. **Scenario 4**: Multi-Commune Portfolio Allocation (Cross-commune prioritization between Cocody, Yopougon, and Marcory).
5. **Scenario 5**: Regulatory Anonymity & Data Protection Audit (Late-night off-peak mobility audit verifying zero PII leakage per Law 2013-450).

---

## 3. Comprehensive Feature Mapping (F01 – F28)

| Feature ID | Feature Name | Description | Target Tier | Spec Source | Interface / Contract | Primary Inputs | Expected Output | Acceptance Criteria |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| **F01** | Geographic Zones Retrieval | WGS84 GeoJSON referential for pilot communes | Tier 1, 2 | `PROJECT.md §1`, `mld.md` | `GET /api/zones?commune=...` | Commune name (`Cocody`, `Yopougon`, `Marcory`) | GeoJSON FeatureCollection with closed Polygon rings in EPSG:4326 | HTTP 200; valid GeoJSON; coords in Abidjan BBox; empty/404 on invalid commune. |
| **F02** | Spatio-Temporal Filtering | Multi-criteria zone/date/time selection | Tier 1, 3 | `PROJECT.md §2`, `CdC EF-01` | `GET /api/mobility?zone_id=...&date_start=...` | `zone_id`, `date_start`, `date_end`, `plage_horaire` | Filtered list of mobility records matching criteria | Records strictly bounded by dates and hours; HTTP 422 on invalid format. |
| **F03** | Aggregate Mobility Display | Presence volume and flow display | Tier 1, 4 | `PROJECT.md §2`, `Tech_Spec §1.2` | `GET /api/mobility` | `zone_id`, time window | Volume presence, inbound flow, outbound flow | Volume $\ge 0$; flux non-negative; proper time slot metadata. |
| **F04** | Dynamic k-Anonymity Masking | Privacy suppression for aggregates $< 15$ | Tier 1, 2 | `Loi CI 2013-450`, `Tech_Spec §4.1` | `GET /api/mobility` | Headcount value $N$ | If $N < 15$: volume `null`, `seuil_k_anonymat_valide = false` | Zero values $0 < N < 15$ exposed; strict legal conformity. |
| **F05** | Synthetic Mobility Engine | Diurnal commuter simulation (7-9h, 17-20h) | Tier 1, 3 | `CdC §13.1`, `PROJECT.md §2` | `GET /api/mobility` | Date range, zone | Generated records with `est_synthetique = true` | Demonstrates morning/evening peaks; weekend commercial profile; realistic volumes. |
| **F06** | Differential Analysis | Temporal comparison T1 vs T2 | Tier 1, 3 | `CdC EF-03`, `PROJECT.md §2` | `GET /api/mobility/differential` | `zone_id`, Period 1, Period 2 | $\Delta$ volume, relative percentage variation | Accurate percentage variation; HTTP 422 if inverted time intervals. |
| **F07** | Naïve D-7 Baseline Model | Historical 7-day lag prediction | Tier 1, 2 | `CdC §9.1`, `PROJECT.md §2` | `GET /api/predictions/{zone_id}?model=NAIVE` | Target date $T$, zone history | Projected volume = volume at $T - 7$ days | Exact numerical match with D-7 time slot; missing history alert. |
| **F08** | Prophet Forecasting Model | Seasonal time series & 95% confidence | Tier 1, 4 | `Tech_Spec §2.1`, `mld.md` | `GET /api/predictions/{zone_id}?model=PROPHET` | Zone time series, horizon 7 days | Point forecast + `[borne_inferieure, borne_superieure]` | Lower $\le$ estimate $\le$ upper; non-negative bounds; trend continuity. |
| **F09** | XGBoost Forecasting Model | Gradient boosting with calendar lags | Tier 1, 4 | `CdC §9.1`, `PROJECT.md §2` | `GET /api/predictions/{zone_id}?model=XGBOOST` | Lag features ($t-1, t-7$), calendar regressors | Point forecast for presence volume | Fast inference ($< 500\text{ms}$); non-negative output. |
| **F10** | Precision Metrics Calculation | MAE, RMSE, WAPE calculation | Tier 1, 2 | `CdC Annexe A`, `mld.md` | `GET /api/predictions/metrics` | Actual vector $y$, forecast vector $\hat{y}$ | Calculated MAE, RMSE, WAPE | $\text{WAPE} = \sum |y - \hat{y}| / \sum y$; zero-division guard. |
| **F11** | Demographic Integration | Resident population INS RGPH 2021 | Tier 1, 2 | `INS RGPH 2021`, `mld.md` | `GET /api/demography?zone_id=...` | `zone_id` or `commune` | `population_totale`, `nombre_menages`, `densite_hab_km2` | Values $> 0$; density = pop / area; source tagged `'INS_RGPH_2021'`. |
| **F12** | Commercial POI Cartography | OSM supermarkets and competitors | Tier 1, 2 | `OSM ODbL`, `mld.md` | `GET /api/pois?commune=...` | Bounding box or commune | Commercial points with GeoJSON Point coordinates | Valid Point in Abidjan BBox; categories match supermarket/retail. |
| **F13** | Road Accessibility Scoring | Network connectivity score | Tier 1, 3 | `Tech_Spec §3.1`, `mld.md` | `GET /api/infrastructure/connectivity` | Zone geometry, OSM highway graph | `score_connectivite` $\in [0, 100]$, major road proximity | Clamped in $[0, 100]$; higher near arterial crossroads. |
| **F14** | Territorial Clustering | Non-supervised K-Means clustering | Tier 1, 3 | `CdC §9.2`, `PROJECT.md §2` | `GET /api/clusters?k=3` | Multi-criteria zone matrix | Cluster labels ($k \in [2, 5]$), silhouette score, inertia | Silhouette $\in [-1, 1]$; deterministic with fixed seed. |
| **F15** | IPET Supermarket Scoring | Normalized score [0, 100] (30/25/20/15/10) | Tier 1, 2 | `Tech_Spec §3.1`, `CdC §9.3` | `POST /api/ipet/calculate` | Sector, default criteria weights | IPET score $\in [0.0, 100.0]$ per zone | Strictly clamped $[0, 100]$; linear combination mathematically exact. |
| **F16** | Interactive Weight Tuning | Custom weight vector ($\sum w_i = 1.0$) | Tier 1, 2 | `Tech_Spec §3.1`, `PROJECT.md §2` | `POST /api/ipet/calculate` | Custom $\{w_i\}$ weights | Dynamic score recalculation and re-ranking | HTTP 422 if $\sum w_i \ne 1.0 \pm 0.001$; score sensitivity verified. |
| **F17** | Opportunity Ranking | Deterministic descending zone ranking | Tier 1, 3 | `sequences.md`, `mld.md` | `POST /api/ipet/calculate` | Zone candidate pool | Sorted list (Rank 1 to $N$) with tie-breakers | Monotonically decreasing IPET; Rank 1 is maximum score. |
| **F18** | Decision Explainability | Top-3 positive drivers and limitations | Tier 1, 2 | `Tech_Spec §3.2`, `mld.md` | `POST /api/ipet/calculate` | Evaluated zone score | Top 3 positive factors, limiting factors | Exactly $\le 3$ positive factors; human-readable strings. |
| **F19** | Data Completeness & Meta | Source traceability and completeness ratio | Tier 1, 2 | `CdC §13.2`, `mld.md` | `POST /api/ipet/calculate` | Evaluated zone source inputs | `taux_completude` $\in [0.0, 1.0]$, timestamp, model | Ratio reflects non-null inputs; warning if $< 0.70$. |
| **F20** | 3D Zone Polygon Extrusion | Catchment area polygon 3D mesh | Tier 1, 4 | `Tech_Spec §2.1`, `PROJECT.md §3` | Frontend Three.js canvas payload | Zone GeoJSON + height metric | 3D extruded mesh coordinates / height attribute | Height proportional to metric; 2D fallback on context loss. |
| **F21** | 3D Density Pillars & Columns | Vertical pillars for IPET/presence | Tier 1, 4 | `Tech_Spec §2.1`, `PROJECT.md §3` | Frontend Three.js canvas payload | Zone centroid + IPET/presence volume | 3D cylinder/column at centroid with scalar color | Pillar anchored at centroid; height clamped; non-negative. |
| **F22** | 3D Mobility Flow Lines | Dynamic 3D curves of movement | Tier 1, 4 | `Tech_Spec §2.1`, `PROJECT.md §3` | Frontend Three.js canvas payload | OD flow matrix | 3D quadratic Bezier curves between centroids | Arc height $> 0$; speed proportional to volume; valid coords. |
| **F23** | shadcn/ui Dashboard UI | Interactive control panel & responsive UI | Tier 1, 4 | `Tech_Spec §2.1`, `PROJECT.md §3` | Dashboard UI state & components | Filter controls, sliders, KPIs | WCAG accessible; state sync across map and panels. |
| **F24** | PDF Executive Report Export | Automated decision report in PDF | Tier 1, 2 | `Tech_Spec §2.1`, `PROJECT.md §2` | `GET /api/reports/pdf?zone_id=...` | `zone_id`, sector, active weights | Binary PDF stream (`%PDF-1.4+`) | Valid magic bytes `%PDF-`; contains metadata and legal disclaimer. |
| **F25** | Excel Data Export (XLSX) | Analytical tabular workbook | Tier 1, 2 | `Tech_Spec §2.1`, `PROJECT.md §2` | `GET /api/reports/excel?zone_id=...` | `zone_id` or commune | Binary XLSX OpenXML stream | Valid ZIP/OpenXML magic bytes; includes demographic and IPET sheets. |
| **F26** | Audit Trail & Security | Logging of sensitive queries/exports | Tier 1, 2 | `CdC EF-10`, `mld.md` | `POST /api/audit/logs` | User action, timestamp, filter params | Persistent record in `journaux_audit` | Synchronous creation; action aborted if audit fails. |
| **F27** | Authentication & RBAC | Role-based access control | Tier 1, 2 | `CdC §3.1`, `mld.md` | `POST /api/auth/token` | User credentials / JWT token | Token with role claim (`ADMIN`, `ANALYSTE`, `METIER`) | Segregated permissions; HTTP 401/403 on invalid access. |
| **F28** | 4-Point Connectivity Suite | Database, Health, API, CORS diagnostics | Tier 1, 2 | `AGENTS.md`, `CdC §13.2` | Connectivity probes | DB probe, Health probe, REST probe, CORS probe | 4/4 passing diagnostics with latencies $< 1500\text{ms}$ | All 4 probes return passing status within thresholds. |

---

## 4. Pytest Test Runner & Execution Guide

### 4.1 Running the Entire E2E Suite via Pytest
```powershell
pytest tests_e2e -v
```

### 4.2 Running Specific Tiers
```powershell
# Tier 1: Feature Coverage (F01 - F28)
pytest tests_e2e/test_tier1_features.py -v

# Tier 2: Boundary & Corner Cases (IPET bounds, k < 15, weights sum)
pytest tests_e2e/test_tier2_boundaries.py -v

# Tier 3: Pairwise Combinations
pytest tests_e2e/test_tier3_combinations.py -v

# Tier 4: Real-World Siting Scenarios
pytest tests_e2e/test_tier4_scenarios.py -v
```

### 4.3 Running via Custom Standalone Runner
```powershell
python tests_e2e/test_runner.py
python tests_e2e/test_runner.py --tier 1
python tests_e2e/test_runner.py --json-report test_report.json
```

---

## 5. Regulatory & Privacy Compliance Specifications

1. **Ivorian Law n° 2013-450 Compliance**:
   - Every mobility aggregation query enforces strict $k$-anonymity: any spatial-temporal slice with headcount $N < 15$ MUST have `volume_presence: null` and `seuil_k_anonymat_valide: false`.
   - Cleartext headcounts are only permissible when $N \ge 15$.
   - Zero storage or presentation of personal identifiers (PII, phone numbers, IMSI, IMEI, individual raw GPS tracks).
2. **Mathematical Invariant Guarantees**:
   - IPET Supermarket Score: $\forall z, \text{IPET}(z) \in [0.0, 100.0]$.
   - Multicriteria Weights: $\sum_{i=1}^5 w_i = 1.0 \pm 0.001$.
   - Opportunity Ranking: $\text{Rank}(z_i) < \text{Rank}(z_j) \iff \text{IPET}(z_i) \ge \text{IPET}(z_j)$.
