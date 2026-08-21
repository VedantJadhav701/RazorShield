# RAZORSHIELD — DATA PREPARATION IMPLEMENTATION TASK

You are working on a fintech defensive AI project called "RazorShield" for a Razorpay Buildathon.

Selected track:
AI Risk Manager

Track objective:
"Stop the merchant losing money to fraud, returns and chargebacks."

Our chosen problem:
DEFENSIVE FRAUD-SPIKE DETECTION.

The system will eventually detect abnormal merchant-level fraud activity and trigger a defensive response. However, this task is ONLY about DATA PREPARATION.

DO NOT implement model training, model evaluation beyond dataset validation, FastAPI, frontend, risk engine, LLM explanation, agents, or deployment in this task.

============================================================
1. PRIMARY OBJECTIVE
============================================================

Build a reproducible data pipeline that creates exactly two datasets:

Dataset A — Model Dataset
Dataset B — Scenario/Evaluation Dataset

Dataset A is for transaction-level fraud modeling.

Dataset B is for merchant-level temporal fraud-spike detection and hard-negative evaluation.

The pipeline must be reproducible, leakage-aware, documented, and executable from the command line.

============================================================
2. DATA SOURCES
============================================================

DATASET A SOURCE:

Use the publicly available IEEE-CIS Fraud Detection dataset from Kaggle.

Official competition:
https://www.kaggle.com/competitions/ieee-fraud-detection

Required files:
- train_transaction.csv
- train_identity.csv

Do NOT commit the raw Kaggle dataset to Git.

The data must be downloaded programmatically by the pipeline.

Use KaggleHub where possible.

Expected authentication:
KAGGLE_API_TOKEN

Never hardcode credentials.

If Kaggle authentication or competition access is unavailable:
- fail clearly
- explain exactly what environment variable/configuration is missing
- do NOT fabricate the public dataset

DATASET B SOURCE:

Dataset B will be generated synthetically.

Use NVIDIA Build API only for generating bounded SCENARIO SPECIFICATIONS.

NVIDIA must NOT be used to generate millions of individual transaction rows.

NVIDIA API:
https://integrate.api.nvidia.com/v1

Environment variable:
NVIDIA_API_KEY

Model:
Use NVIDIA_MODEL environment variable if provided.
Otherwise use the model defined in data.py/default configuration.

IMPORTANT:
The LLM generates scenario parameters.
Python/NumPy generates actual transaction records.

This is intentional for:
- reproducibility
- cost control
- deterministic row generation
- controllable labels
- avoiding hallucinated numerical datasets

============================================================
3. REQUIRED PROJECT STRUCTURE
============================================================

Create or maintain:

razorshield/
│
├── data.py
├── requirements.txt
├── .env.example
├── .gitignore
│
├── data/
│   ├── raw/
│   │   └── ieee_cis/
│   │       ├── train_transaction.csv
│   │       └── train_identity.csv
│   │
│   └── processed/
│       ├── dataset_a_model.parquet
│       ├── dataset_b_scenarios.parquet
│       ├── scenario_specs.json
│       ├── metadata.json
│       └── validation_report.json
│
└── docs/
    └── DATA.md

Do not unnecessarily create ML/model/frontend directories yet.

This task ends after the datasets and validation report are successfully produced.

============================================================
4. DATASET A — MODEL DATASET
============================================================

Build Dataset A from IEEE-CIS.

Dataset A represents transaction-level fraud detection.

Do NOT pretend IEEE-CIS directly provides merchant-level fraud-spike labels.

It does not.

Dataset A should primarily be used for:
P(fraud | transaction)

Target:
isFraud

Use the transaction and identity data.

Join:
train_transaction.csv
LEFT JOIN
train_identity.csv

on:
TransactionID

============================================================
5. DATASET A CANONICAL SCHEMA
============================================================

Create a clean canonical schema containing, where available:

IDENTIFIERS:
- transaction_id
- customer_proxy_id
- device_proxy_id

TIME:
- event_time
- hour
- day_of_week
- is_weekend

TRANSACTION:
- amount
- amount_log1p
- ProductCD

CARD:
- card1
- card2
- card3
- card4
- card5
- card6

ADDRESS:
- addr1
- addr2

EMAIL:
- P_emaildomain
- R_emaildomain

DEVICE:
- DeviceType
- DeviceInfo
- identity_available

TARGET:
- isFraud

SPLIT:
- split

Do not expose unnecessary raw personal information.

Do not introduce real IP addresses, names, email addresses, or other PII.

Proxy identifiers must be deterministic and non-reversible.

============================================================
6. DATASET A TIME HANDLING
============================================================

IEEE-CIS TransactionDT is a relative time value.

Convert it to a synthetic reference timestamp only for temporal processing.

Document clearly:

"The resulting timestamp is a synthetic reference time derived from TransactionDT and must not be interpreted as the original real-world timestamp."

Do NOT claim it represents actual calendar dates.

Sort Dataset A chronologically.

============================================================
7. DATASET A SPLIT
============================================================

Do NOT use random train_test_split as the primary split.

Use chronological splitting:

70% earliest observations:
train

15% next observations:
validation

15% latest observations:
test

The test period must represent future observations relative to training.

Verify:

max(train.event_time) <= min(validation.event_time)

max(validation.event_time) <= min(test.event_time)

Allow exact boundary equality only if caused by timestamp resolution.

Document why temporal splitting is used.

============================================================
8. DATASET A VALIDATION
============================================================

After creating Dataset A, calculate and save:

- total rows
- total columns
- fraud count
- fraud percentage
- missing percentage per column
- duplicate transaction IDs
- min/max event_time
- train rows
- validation rows
- test rows
- fraud count per split
- fraud percentage per split

Check for:

1. Duplicate transaction IDs
2. Invalid target values
3. Impossible negative transaction amounts
4. Missing event_time
5. Broken chronological split
6. Unexpected data types
7. Infinite values

DO NOT silently delete suspicious data.

If cleaning is performed, record:
- column
- operation
- number of affected rows

============================================================
9. DATASET B — SCENARIO/EVALUATION DATASET
============================================================

Dataset B is our custom defensive synthetic dataset.

Its purpose is:

"Can the system distinguish a genuine fraud spike from ordinary volume/amount changes?"

It must contain multiple scenario classes.

Required scenario types:

1. normal
2. fraud_spike
3. volume_only_spike
4. amount_shift

These scenarios are intentionally designed to include hard negatives.

============================================================
10. SCENARIO DEFINITIONS
============================================================

NORMAL:

Normal transaction volume and normal fraud rate.

Expected:
fraud_spike = 0

------------------------------------------------------------

FRAUD_SPIKE:

Transaction behavior changes and fraud rate materially increases during a
defined temporal window.

Expected:
fraud_spike = 1

Example conceptual behavior:

baseline fraud rate:
~1%

spike fraud rate:
~10%

Do NOT hardcode exactly these numbers for every scenario.

Use bounded variability.

------------------------------------------------------------

VOLUME_ONLY_SPIKE:

Transaction volume increases substantially but fraud rate remains close to
baseline.

This is a HARD NEGATIVE.

Expected:
fraud_spike = 0

The model must not learn:

"high transaction volume = fraud."

------------------------------------------------------------

AMOUNT_SHIFT:

Transaction amount distribution changes substantially but fraud rate does
not necessarily increase.

This is another HARD NEGATIVE.

Expected:
fraud_spike = 0

============================================================
11. NVIDIA SCENARIO GENERATION
============================================================

Use NVIDIA Build API to generate scenario specifications.

The model should output JSON only.

Each scenario specification should contain:

- scenario_type
- duration_minutes
- spike_start_minute
- spike_duration_minutes
- baseline_txn_per_minute
- spike_txn_multiplier
- baseline_fraud_rate
- spike_fraud_rate
- amount_mean
- amount_std
- customer_count
- device_count
- new_device_rate
- seed

All values MUST be validated by Python.

Never trust LLM-generated values directly.

Apply strict bounds.

Example bounds:

duration_minutes:
120–360

baseline_txn_per_minute:
3–30

spike_txn_multiplier:
1–10

baseline_fraud_rate:
0.002–0.03

spike_fraud_rate:
0.002–0.30

amount_mean:
100–5000

amount_std:
20–2500

new_device_rate:
0–0.25

If scenario_type is:
normal
then spike_txn_multiplier should be approximately 1.

If scenario_type is:
volume_only_spike
then spike_txn_multiplier should be materially > 1 but fraud rate should remain approximately baseline.

If scenario_type is:
fraud_spike
then spike_fraud_rate must materially exceed baseline_fraud_rate.

If scenario_type is:
amount_shift
amount distribution should change while fraud rate remains approximately baseline.

============================================================
12. NVIDIA WORKERS
============================================================

Support concurrent NVIDIA API requests.

CLI option:

--workers

Example:

python data.py --generate-scenarios --scenarios 60 --workers 4 --batch-size 5

Start conservatively.

Recommended default:
workers = 4

Recommended batch size:
5

Implement:
- retries
- exponential backoff
- timeout
- JSON parsing validation
- failed batch logging

Do not create uncontrolled concurrency.

If NVIDIA API fails repeatedly:
- fail clearly
- preserve successful scenario specifications
- do not silently replace NVIDIA results with random data unless explicit offline mode is enabled

============================================================
13. OFFLINE DEVELOPMENT MODE
============================================================

Support:

--offline-synthetic

When enabled:
do not call NVIDIA.

Generate deterministic fallback scenario specifications locally using NumPy.

Clearly mark metadata:

"offline_fallback": true

This is only for development/testing.

The official buildathon dataset generation should use NVIDIA-generated scenario specifications.

============================================================
14. SYNTHETIC TRANSACTION GENERATION
============================================================

After receiving validated scenario specifications from NVIDIA:

Generate actual transactions locally using NumPy.

Do NOT ask NVIDIA to generate transaction rows.

Each synthetic transaction should contain:

- transaction_id
- scenario_id
- scenario_type
- merchant_id
- event_time
- customer_id
- device_id
- amount
- payment_method
- transaction_type
- is_new_device
- is_fraud
- spike_window
- fraud_spike

Use deterministic seeds.

For the same:
scenario specification + seed

the generated rows should be reproducible.

============================================================
15. DATASET B TEMPORAL FEATURES
============================================================

Generate merchant-level temporal features.

At minimum:

- merchant_txn_count_15m
- rolling_txn_15m
- rolling_fraud_rate_15m
- baseline_txn_15m
- baseline_fraud_rate
- velocity_ratio
- fraud_rate_deviation
- baseline_amount
- amount_deviation

Important:

Baseline features must be calculated using historical/baseline observations.

Do NOT use future spike observations to define the baseline.

Avoid temporal leakage.

============================================================
16. DATASET B LABEL
============================================================

Dataset B must contain:

fraud_spike

Definition:

fraud_spike = 1
ONLY for the intended fraud_spike scenario during the abnormal fraud window.

fraud_spike = 0
for normal, volume_only_spike, and amount_shift scenarios.

This label is for scenario-level evaluation.

============================================================
17. DATASET B SPLIT
============================================================

Do not randomly split transaction rows from the same scenario between train
and test.

That would cause scenario leakage.

Instead split by scenario_id.

Example:

70% scenarios:
train

15% scenarios:
validation

15% scenarios:
test

Therefore:

A scenario must belong to exactly one split.

No transactions from the same scenario may appear in multiple splits.

Verify this programmatically.

============================================================
18. DATASET B HARD-NEGATIVE VALIDATION
============================================================

After generation, explicitly verify:

NORMAL:
fraud rate remains low/stable

FRAUD_SPIKE:
fraud rate increases materially

VOLUME_ONLY_SPIKE:
transaction volume increases but fraud rate remains approximately baseline

AMOUNT_SHIFT:
amount distribution changes but fraud rate remains approximately baseline

Generate a scenario summary table:

scenario_id
scenario_type
rows
baseline_fraud_rate
spike_fraud_rate
baseline_volume
spike_volume
max_velocity_ratio
fraud_spike_label

Save this to validation_report.json or a separate summary file.

============================================================
19. DATA QUALITY CHECKS
============================================================

Both datasets must be checked for:

- duplicate IDs
- null event_time
- invalid amounts
- negative amounts
- infinite values
- invalid target labels
- broken split assignments
- scenario leakage
- missing required columns
- unexpected categorical values

Use fail-fast behavior for structural errors.

Warnings may be used for expected missing values.

Do not hide errors.

============================================================
20. OUTPUT FORMAT
============================================================

Use Parquet for processed datasets.

Required files:

data/processed/dataset_a_model.parquet

data/processed/dataset_b_scenarios.parquet

data/processed/scenario_specs.json

data/processed/metadata.json

data/processed/validation_report.json

Do not use CSV as the primary processed format.

Parquet is preferred for:
- performance
- type preservation
- storage efficiency

============================================================
21. METADATA
============================================================

metadata.json must document:

- project name
- purpose
- Dataset A source
- Dataset A URL
- Dataset B synthetic generation method
- NVIDIA model
- NVIDIA endpoint
- number of scenarios
- worker count
- batch size
- random seed
- split strategy
- generation timestamp
- whether offline mode was used
- schema version
- data cleaning operations

Do not store API keys.

============================================================
22. DATA LICENSE / GIT SAFETY
============================================================

.gitignore MUST include:

data/raw/
*.csv
*.parquet
.env
.env.*
!.env.example

Do not commit:
- Kaggle credentials
- NVIDIA API key
- raw IEEE-CIS files
- generated large datasets

The README/DATA documentation should explain how a new developer can
download/recreate the datasets.

============================================================
23. DATA DOCUMENTATION
============================================================

Create:

docs/DATA.md

Explain:

1. Why IEEE-CIS was selected
2. What Dataset A represents
3. What Dataset B represents
4. Why synthetic scenarios are needed
5. Why NVIDIA generates scenario specifications rather than rows
6. Feature groups
7. Temporal split methodology
8. Leakage prevention
9. Hard-negative scenarios
10. Reproduction commands
11. Environment variables
12. Dataset limitations

Be honest that Dataset B is synthetic.

Do not claim it represents actual Razorpay transaction data.

Do not claim IEEE-CIS timestamps represent real calendar timestamps.

============================================================
24. CLI COMMANDS
============================================================

The following commands must work:

Download public data:

python data.py --download-public

Build Dataset A:

python data.py --build-model

Generate Dataset B with NVIDIA:

python data.py --generate-scenarios --scenarios 60 --workers 4 --batch-size 5

Generate Dataset B offline:

python data.py --generate-scenarios --scenarios 8 --offline-synthetic

Run everything:

python data.py --all --scenarios 60 --workers 4 --batch-size 5

============================================================
25. REQUIREMENTS
============================================================

requirements.txt should contain only dependencies actually required for the
data pipeline.

At minimum evaluate:

pandas
numpy
pyarrow
kagglehub
openai

Pin versions where appropriate after confirming compatibility.

Do not add ML libraries yet unless required by the data preparation.

============================================================
26. TESTING
============================================================

Create tests for:

1. Scenario specification validation
2. Scenario type validation
3. Bounds validation
4. Deterministic synthetic generation
5. Dataset A chronological split
6. Dataset B scenario-level split
7. No scenario leakage
8. Required columns
9. Invalid target detection
10. Hard-negative semantics

At minimum:

pytest

must pass before considering this task complete.

============================================================
27. IMPORTANT SECURITY RULE
============================================================

This is a DEFENSIVE fraud detection project.

Do not generate:
- attack instructions
- payment bypass instructions
- fraud execution instructions
- credential theft
- authentication bypass
- evasion strategies
- exploit procedures

Synthetic data must represent abstract statistical patterns only.

============================================================
28. IMPORTANT ENGINEERING RULES
============================================================

Do not:
- fabricate public data
- hardcode fake model metrics
- randomly label transactions without documented distributions
- use future data for historical features
- randomly split temporal transactions as the primary evaluation strategy
- mix the same synthetic scenario across train/test
- commit API keys
- commit raw datasets
- make unsupported claims about dataset realism

Prefer:
- deterministic seeds
- explicit schemas
- validation
- logging
- reproducibility
- Parquet
- type-safe processing
- clear failure messages
- small test runs before large generation

============================================================
29. SUCCESS CRITERIA
============================================================

This task is complete ONLY when:

[ ] IEEE-CIS can be downloaded programmatically
[ ] Dataset A can be built automatically
[ ] Dataset A has chronological train/validation/test splits
[ ] Dataset A passes validation
[ ] NVIDIA scenario generation works
[ ] NVIDIA worker configuration works
[ ] NVIDIA retry/backoff works
[ ] Offline synthetic mode works
[ ] Dataset B can be generated deterministically
[ ] Dataset B contains all four scenario classes
[ ] Fraud-spike scenarios actually increase fraud rate
[ ] Volume-only scenarios increase volume without fraud spike
[ ] Amount-shift scenarios change amount distribution without fraud spike
[ ] Dataset B has scenario-level train/validation/test splits
[ ] No scenario leakage exists
[ ] Required metadata is written
[ ] Validation report is written
[ ] Raw data is gitignored
[ ] API keys are gitignored
[ ] Tests pass
[ ] docs/DATA.md exists
[ ] README contains reproduction commands

============================================================
30. STOP CONDITION
============================================================

STOP after the complete data preparation pipeline is working and validated.

Do NOT proceed to:

- XGBoost training
- LightGBM training
- model selection
- threshold optimization
- risk engine
- FastAPI
- frontend
- SLM explanation
- LangGraph
- Docker deployment
- production inference

Those will be implemented in a separate task AFTER we inspect and approve
Dataset A and Dataset B.

============================================================
FINAL RESPONSE REQUIRED FROM YOU
============================================================

When implementation is complete, report:

1. Files created/modified
2. Exact commands executed
3. Dataset A row count
4. Dataset A fraud count and fraud percentage
5. Dataset A train/validation/test counts
6. Dataset B row count
7. Dataset B scenario count
8. Scenario distribution
9. Dataset B train/validation/test scenario counts
10. Hard-negative validation results
11. Any data-quality warnings
12. Test results
13. Whether NVIDIA API was used or offline mode was used
14. Any unresolved issue

Do not report fabricated metrics.

If something cannot be completed, state the exact blocker instead of
pretending the pipeline succeeded.