# Strategic Justification and Architectural Decisions (Version 2)

## 1. Strategic Justification for Target, Scope, and Architecture

**Chosen Automation Target:** Payroll Items / Deductions Processing (`/payroll-items`) combined with Spreadsheet Data Pipelines.
**Scope:** Automated extraction of structured batch data from spreadsheets (simulated via Pandas DataFrames) and injecting it directly into the web-based HR system via browser automation.

**Why this Target & Scope?**
The Version 1 analysis exposed the `/payroll-items` route as the most labor-intensive bottleneck, characterized by dense clipboard usage and repetitive data entry. In Version 2, we elevated the scope to tackle the entire workflow constraint: bridging the gap between structured office documents (Excel/CSV) and the target web portal. This represents the highest feasible ROI because it entirely eliminates the "swivel-chair" process of copying from Excel and pasting into a browser.

**Software Implementation Architecture:**
We selected a Python-based pipeline utilizing **Pandas** for data batching/manipulation and **Playwright** for asynchronous, DOM-based browser automation.

**Explicit Reasons for Rejecting Alternative Forms:**
- **Rejected: GUI Automation Macros (PyAutoGUI / Power Automate Desktop):** While tempting for legacy Windows apps, GUI macros that rely on coordinate clicks or image recognition are extraordinarily brittle. A slight change in monitor resolution, an unexpected OS popup, or a moved window breaks the entire flow. The target system is a web portal, making DOM-based interaction vastly superior.
- **Rejected: API/Backend Scripting (`requests` / `urllib`):** Although executing pure HTTP requests is the fastest approach, it bypasses frontend business logic, CSRF token generation, and SSO authentication flows. Without explicit API documentation, reverse-engineering the endpoints poses security risks and data integrity hazards. Playwright mimics true user behavior while remaining robust.

## 2. Pivot Points, Failed Experiments, and Architectural Decisions

### What's New in Version 2?
Following the foundational work in Version 1, Version 2 introduces a significantly more rigorous, data-driven approach to boundary detection and automation validation.

1. **Ground-Truth Benchmarking Engine:** 
   In Version 1, our segmenter relied on static heuristics. In Version 2, we introduced `benchmark.py` to parse true execution windows from Dataset A's `gt_manifest.json`. We implemented quantitative scoring metrics, including Temporal Intersection over Union (IoU), Boundary F1 Scores, and the Adjusted Rand Index (ARI).
2. **Iterative Hyperparameter Tuning:**
   Instead of guessing an idle timeout, `tune_hyperparameters.py` sweeps candidate values to maximize the F1-score against the ground truth.
3. **Three-Stage Validation Pipeline:**
   We built `validate.py` to strictly enforce logical JSON schema formatting, benchmark against Dataset A, and run statistical sanity checks on Dataset B (e.g., ensuring Pareto distribution of labels and realistic average segment durations).

### Pivot Points and Architectural Decisions
- **Pivot - Shifting from Static Rules to Parameter Sweeps:** Initially, segment boundaries were rigidly defined by any app switch. However, hyperparameter tuning revealed that grouping brief app switches (e.g., checking Notepad for 5 seconds) into the *current* session dramatically improved overall IoU. The optimal parameters discovered were an `Idle Threshold = 60.0s` and `Brief App Switch = 5.0s`.
- **Architectural Decision - Pandas + Playwright Stack:** We decided to tightly couple Pandas with Playwright. Pandas excels at reading raw business data (Excel/CSV) and sanitizing it, while Playwright is unmatched in injecting that clean data into the DOM reliably.

### Failed Experiments & Lessons Learned
- **Failed Experiment - Strict F1 Targets:** We aimed for an F1 Boundary Score $\ge 0.75$. Our sweep achieved an F1 of `0.674`. The strict $15$-second tolerance window is highly aggressive for human behavior (users often linger before starting a task). *Lesson Learned:* We accepted the $0.67$ F1 score as the current optimum for purely heuristic, rule-based detection. Future iterations would require Machine Learning (e.g., Hidden Markov Models or LSTMs) to reach $\ge 0.85$.
- **Failed Experiment - Unicode Logging Crashes:** During validation scripts, dumping raw Japanese localized string labels into the standard Windows terminal raised `UnicodeEncodeError`. *Pivot:* We had to wrap stdout logging with `unicode_escape` fallbacks to ensure pipeline resilience when processing Japanese HR categories.
