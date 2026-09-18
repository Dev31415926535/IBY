# Exception Pattern Learning System (Version 3)

## Overview
Version 3 is NOT a replacement for Steps 1-3. Instead, Version 3 is a feature enhancement on top of the existing Step 3 automation tool.The Exception Pattern Learning System is a high-leverage feature enhancement that integrates cleanly into the existing automation architecture. It provides intelligent exception categorization and suggests business logic fixes to address risks R-08 (data schema mismatches) and R-11 (business logic violations) from the FINAL_PROPOSAL.md.

## Key Features

1. **Zero-Disruption Integration**: Hooks into `automation_pipeline.py` without modifying the main execution loop
2. **Intelligent Categorization**: Automatically categorizes exceptions into 7 standard failure modes
3. **Risk-Targeted Analysis**: Maps exception patterns directly to documented risks (R-08, R-11, etc.)
4. **Auto-Generated Reports**: Produces both JSON summaries and human-readable markdown reports
5. **Comprehensive Testing**: 31 unit tests ensuring zero disruption to happy-path automation runs

## Installation

```bash
cd version_3
python -m venv venv
venv/Scripts/activate  # On Windows
venv/bin/activate     # On Unix
pip install -r requirements.txt
```

## Usage

### Standalone Analysis

```bash
python exception_learner.py
```

### Running Tests

```bash
pytest tests/test_exception_learner.py -v
```

All 31 tests should pass, verifying:
- Correct exception categorization
- Zero disruption to happy-path automation
- Risk targeting accuracy
- Pattern generation and export
- Integration safety