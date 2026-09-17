# Strategic Justification

## 1. Automation Target and Scope
**Chosen Target:** Payroll Items / Deductions Processing (`/payroll-items`)

**Strategic Justification:**
The logs demonstrated that the `/payroll-items` module had the highest interaction frequency (43 discrete process blocks) and incurred the highest volume of copy-paste operations (307 clipboard events). 
- **High ROI:** Automating tasks with high repetition and heavy manual transcription yields the greatest time savings and error reduction.
- **Scope limitation:** We purposefully scoped the initial prototype to data entry rather than full end-to-end reconciliation. Focusing on the bottleneck (manual entry into the web system) allows for rapid deployment, establishing early trust with the operations team before tackling more complex edge cases like discrepancy handling.

## 2. Software Implementation Architecture

**Chosen Architecture:** Local DOM-based UI Automation via Python Playwright (`prototype.py`).

**Why this approach was chosen:**
1. **No API Dependencies:** The internal business systems did not expose a documented backend API in the logs. Attempting to reverse-engineer hidden endpoints introduces significant security and maintenance risks.
2. **True to User Workflow:** Automating the UI exactly replicates the human process. It triggers the exact same frontend validations and state changes as a human operator, ensuring business logic parity.
3. **Resilience & Asynchrony:** Playwright inherently waits for elements to become interactive, which handles the slow network responses and variable load times characteristic of legacy internal systems much better than raw `pyautogui` clicks.

**Explicit Reasons for Rejecting Alternative Forms:**
- **Rejected: Coordinate-based Desktop Automation (e.g., PyAutoGUI/Sikuli)**
  - *Reasoning:* Coordinate clicks break as soon as the user resizes a window, changes their monitor resolution, or a browser update shifts the UI by a few pixels. It is highly brittle and requires constant maintenance.
- **Rejected: Backend API Scripting (e.g., Python `requests`)**
  - *Reasoning:* While faster, we lack authentication schemas (SSO tokens, CSRF tokens) and API documentation. Bypassing the UI means bypassing frontend validations, potentially pushing corrupt or incomplete data into the database.
- **Rejected: Full-stack Web App for Data Ingestion**
  - *Reasoning:* Too heavyweight for a proof-of-concept. The goal is to prove automation value quickly, not to build a parallel HR system.

## 3. Metrics and Baseline for Future Versions

To quantify the success of this and future versions of the automation, we will track the following core metrics against our established baseline:

1. **Average Time Per Transaction (Seconds):**
   - *Baseline (Manual):* ~42.3 seconds per `/payroll-items` block.
   - *Target (Automated v1):* ~2.5 seconds per transaction.
2. **Manual Steps / Keystrokes Per Transaction:**
   - *Baseline (Manual):* ~7 copy-paste actions + numerous clicks.
   - *Target (Automated v1):* 0 manual steps (fully headless execution).
3. **Error Rate (Data Transcription):**
   - *Baseline (Manual):* Expected ~1-3% human transcription error rate over thousands of rows.
   - *Target (Automated v1):* 0% transcription error (assuming valid source data).

We have generated a visualization (`metrics_comparison.png`) that highlights the difference between the manual baseline extracted from Dataset B and the expected performance of `prototype.py`. As future iterations roll out (e.g., adding exception handling queues), these baseline metrics will dictate whether the updates successfully improve operational efficiency.
