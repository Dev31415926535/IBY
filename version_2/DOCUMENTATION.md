# Version 2 Documentation

## Overview

Version 2 represents the ML-inspired segmentation engine and advanced automation pipeline for the intern selection project. This version significantly improves upon Version 1 by incorporating ground truth validation, hyperparameter tuning, and a production-ready automation architecture.

## Architecture

### Core Components

1. **segmenter_v2.py** - ML-inspired segmentation engine with soft boundaries
2. **benchmark.py** - Ground truth validation against Dataset A
3. **tune_hyperparameters.py** - Automated hyperparameter optimization
4. **validate.py** - Three-stage validation pipeline
5. **automation_pipeline.py** - Production automation prototype

### Data Flow

```
Dataset A (Ground Truth) → benchmark.py → Performance Metrics
                         ↓
                      tune_hyperparameters.py → Optimal Parameters
                         ↓
Dataset B (Production) → segmenter_v2.py → segments.jsonl
                         ↓
                      automation_pipeline.py → Automated Processing
```

## Key Improvements Over Version 1

### 1. Ground Truth Validation
- **File:** `benchmark.py`
- **Purpose:** Validate segmentation accuracy against Dataset A ground truth
- **Metrics:**
  - Temporal Intersection over Union (IoU): 0.715
  - Boundary F1 Score: 0.674
  - Adjusted Rand Index (ARI): 0.447

### 2. Hyperparameter Optimization
- **File:** `tune_hyperparameters.py`
- **Purpose:** Automatically sweep threshold values to find optimal segmentation parameters
- **Optimal Parameters:**
  - `idle_threshold`: 60.0 seconds
  - `brief_switch`: 5.0 seconds
- **Key Insight:** Grouping brief app-switches (<5s) drastically improved temporal alignment

### 3. Three-Stage Validation
- **File:** `validate.py`
- **Stage 1:** Schema integrity validation via jsonschema
- **Stage 2:** Quantitative benchmark against Dataset A
- **Stage 3:** Statistical sanity checks on Dataset B output

### 4. Advanced Automation Pipeline
- **File:** `automation_pipeline.py`
- **Architecture:** Python + Playwright + Pandas
- **Features:**
  - Batch processing from structured data
  - SSO authentication handling
  - Error recovery and simulation fallback
  - Japanese character encoding support

## File Descriptions

### segmenter_v2.py

**Purpose:** Core segmentation algorithm that converts raw event logs into business process segments.

**Key Features:**
- Route-based labeling using URL fragment analysis
- Idle threshold detection for boundary detection
- Brief app-switch grouping (soft boundaries)
- Unicode-safe processing for Japanese content

**Parameters:**
- `idle_threshold`: Minimum idle time (seconds) to consider a segment boundary
- `brief_switch`: Maximum duration (seconds) to group as brief app-switch

**Output:** `segments.jsonl` - One JSON object per segment with fields:
- `session_id`: Session identifier
- `start`: Segment start time (ISO 8601 UTC)
- `end`: Segment end time (ISO 8601 UTC)
- `label`: Business process name (Japanese)

### benchmark.py

**Purpose:** Validate segmentation accuracy against Dataset A ground truth.

**Metrics Calculated:**
- **Temporal IoU:** Measures temporal overlap between predicted and ground truth segments
- **Boundary F1 Score:** Precision/recall for segment boundaries
- **Adjusted Rand Index:** Clustering similarity metric

**Usage:**
```bash
python benchmark.py
```

**Output:** Console output with performance metrics and dataset coverage statistics.

### tune_hyperparameters.py

**Purpose:** Automated hyperparameter sweep to find optimal segmentation parameters.

**Approach:**
- Grid search over candidate threshold values
- Evaluates each combination against Dataset A ground truth
- Selects parameters maximizing IoU and F1 Score

**Search Space:**
- `idle_threshold`: 30.0s to 120.0s (step 10.0s)
- `brief_switch`: 2.0s to 10.0s (step 1.0s)

**Usage:**
```bash
python tune_hyperparameters.py
```

**Output:** Optimal parameters and performance metrics to console.

### validate.py

**Purpose:** Three-stage validation pipeline for segmentation output.

**Stage 1 - Schema Validation:**
- Verifies JSONL structure
- Checks mandatory fields (session_id, start, end, label)
- Validates timestamp format (ISO 8601 UTC)
- Ensures start < end for all segments
- Detects overlapping intervals within sessions

**Stage 2 - Quantitative Benchmark:**
- Runs benchmark.py against Dataset A
- Reports IoU, F1, and ARI metrics
- Compares against target thresholds

**Stage 3 - Statistical Sanity:**
- Analyzes segment distribution across Dataset B
- Checks for over-fragmentation or under-segmentation
- Validates label consistency

**Usage:**
```bash
python validate.py
```

**Output:** Detailed validation report to console and `outputs/validate_out.txt`.

### automation_pipeline.py

**Purpose:** Production automation prototype for payroll items entry.

**Architecture:**
- **Data Layer:** Pandas DataFrame for structured data ingestion
- **Browser Layer:** Playwright with Chromium for web automation
- **Integration Layer:** Async pipeline with error handling

**Selectors Used:**
- `#btn-pi-register` - New record button
- `input[name='employee_name']` - Employee name field
- `input[name='item_name']` - Item name field
- `input[name='amount']` - Amount field
- `#pi-note` - Note field
- `#btn-pi-ok` - Submit button

**Authentication:**
- SSO mock endpoint: `http://127.0.0.1:5132/sso-mock.html`
- Fallback to simulation when portal unavailable

**Usage:**
```bash
python automation_pipeline.py
```

**Output:** Console processing report and `outputs/pipeline_out.txt`.

### Strategic_Justification_v2.md

**Purpose:** Documents architectural decisions and technology choices.

**Key Sections:**
- Why Python + Playwright + Pandas was chosen
- Why backend API scripting was rejected
- Why LLM agents were rejected for core automation
- Why desktop macros were rejected
- Risk mitigation strategies

## Output Files

### segments.jsonl

**Location:** `version_2/segments.jsonl`
**Size:** 339 segments from 15 Dataset B sessions
**Format:** JSONL (one JSON object per line)

**Sample:**
```json
{"session_id": "ses_20260701-164424-CHAITANYA0BCF", "start": "2026-07-01T16:44:42.584000+00:00", "end": "2026-07-01T16:47:44.122000+00:00", "label": "給与備考・控除整備"}
```

### outputs/ Directory

- `pipeline_out.txt` - Automation pipeline execution log
- `tuning_out.txt` - Hyperparameter tuning results
- `validate_out.txt` - Validation pipeline report

## Process Labels

The segmentation identifies 11 distinct business processes:

1. **給与備考・控除整備** (Payroll Remarks & Deduction Maintenance) - 37.8% of working time
2. **育児・産休申請確認** (Childcare/Maternity Leave Application Confirmation)
3. **社保・年金補正対応** (Social Insurance/Pension Adjustment Response)
4. **入社照合・手当確認** (Onboarding Verification & Allowance Confirmation)
5. **住民税通知確認** (Resident Tax Notification Confirmation)
6. **契約解除手続き** (Contract Termination Procedures)
7. **休暇申請確認** (Leave Application Confirmation)
8. **通勤手当申請** (Commuting Allowance Application)
9. **経費精算** (Expense Reimbursement)
10. **給与計算** (Payroll Calculation)
11. **システム設定** (System Configuration)

## Performance Metrics

### Segmentation Accuracy (Dataset A)
- **Temporal IoU:** 0.715 (target: 0.75)
- **Boundary F1:** 0.674 (target: 0.75)
- **ARI:** 0.447
- **Segmentation Ratio:** 0.770 (slight under-segmentation)

### Dataset B Statistics
- **Total Segments:** 339
- **Total Sessions:** 15
- **Classified Working Time:** 143.1 minutes
- **Process Diversity:** 11 distinct labels
- **Average Segments per Session:** 22.6

### Automation Performance
- **Manual Handling Time:** 13.5 seconds per record
- **Automated Handling Time:** 4.0 seconds per record (estimated)
- **Time Reduction:** 70.7%
- **Clipboard Operations Eliminated:** 307 per 240 payroll records

## Dependencies

### Virtual Environment Setup
```bash
cd version_2
python -m venv venv
venv/Scripts/activate  # Windows
venv/bin/activate     # Unix/Linux
```

### Required Packages
```bash
pip install pandas>=1.5.0
pip install playwright>=1.40.0
pip install scikit-learn>=1.3.0
pip install jsonschema>=4.17.0
```

### Playwright Browser Setup
```bash
playwright install chromium
```

## Execution Workflow

### Complete Pipeline Execution

```bash
# 1. Tune hyperparameters (optional - use pre-tuned values)
python tune_hyperparameters.py

# 2. Run validation
python validate.py

# 3. Execute automation pipeline
python automation_pipeline.py
```

### Step-by-Step Execution

```bash
# Step 1: Generate segments from Dataset B
python segmenter_v2.py

# Step 2: Validate segmentation accuracy
python validate.py

# Step 3: Run automation on processed data
python automation_pipeline.py
```

## Technical Decisions

### Why ML-Inspired Over Pure Heuristics?
- Ground truth availability in Dataset A enables quantitative validation
- Hyperparameter tuning provides objective parameter selection
- Soft boundaries better match real-world work patterns
- Measurable performance metrics enable iterative improvement

### Why Python + Playwright + Pandas?
- **Pandas:** Robust data manipulation and ETL capabilities
- **Playwright:** Modern, reliable browser automation with good selector stability
- **Python:** Rich ecosystem, good async support, production-ready

### Why Rejected Alternatives?
- **Backend API Scripting:** Lack of CSRF tokens, missing documentation
- **LLM Agents:** Non-deterministic, auditability risks, unnecessary for deterministic form filling
- **Desktop Macros:** Brittle, platform-specific, poor error handling

## Risk Mitigation

### Technical Risks
- **Selector Stability:** Use ID-based selectors, implement health checks
- **Data Schema Variations:** Canonical template enforcement, schema validation
- **Network Failures:** Retry logic with exponential backoff, circuit breaker pattern

### Operational Risks
- **Policy Violations:** Pre-flight validation, human review for edge cases
- **Authentication Failures:** Service account with scoped permissions, credential rotation
- **Process Variants:** Exception queue, continuous pattern learning (Version 3)

## Future Enhancements

### Version 3 Integration
- Exception pattern learning system
- Automated business rule encoding
- Continuous improvement from runtime data

### Phase 2 Extensions
- Route extension to other payroll processes
- Direct source system integration
- Advanced business rule encoding
- Japanese language note generation assistance

## Troubleshooting

### Common Issues

**Segmentation under-fragmentation:**
- Reduce `idle_threshold` parameter
- Increase `brief_switch` parameter

**Browser automation failures:**
- Verify portal availability at `http://127.0.0.1:5132`
- Check selector stability in staging environment
- Increase timeout values in automation_pipeline.py

**Unicode encoding errors:**
- Ensure UTF-8 encoding in file operations
- Use unicode_escape for console output on Windows
- Verify Japanese character support in terminal

## References

- **Dataset Schema:** `../DATA_SCHEMA.md`
- **Final Report:** `../FINAL_REPORT.md`
- **Work Log:** `../work_log.md`
- **Version 1 Documentation:** `../version_1/DOCUMENTATION.md`
- **Version 3 Documentation:** `../version_3/README.md`

## Contact & Support

For questions about Version 2 implementation, refer to:
- Strategic justification: `Strategic_Justification_v2.md`
- Validation results: `outputs/validate_out.txt`
- Pipeline logs: `outputs/pipeline_out.txt`