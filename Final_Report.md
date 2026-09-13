# Automation Proposal: Internal Operations

## 1. Executive Summary

This report details the findings from our analysis of the company's internal PC operation logs (Datasets A and B) to identify high-ROI automation candidates. By analyzing the work patterns, application usage, and time spent on various business processes, we have identified **Payroll Adjustments / Deductions (`/payroll-items`)** as the highest priority candidate for immediate automation. 

To demonstrate feasibility, we have provided a working Python Playwright prototype that automates the data entry for this process. A baseline segmentation script (`segmenter.py`) was also developed to parse raw event logs into execution blocks, allowing us to map unstructured events to specific business cases.

---

## 2. Analysis of Business Processes

Using our log segmentation and analysis scripts, we extracted the frequency, application usage, and interaction patterns for various processes. The following processes emerged as the most significant drivers of manual effort in the production environment (Dataset B):

1. **Payroll Items / Deductions Processing (`/payroll-items`)**
   - **Volume:** 43 executions (highest frequency)
   - **Manual Effort:** 307 clipboard copy-paste events recorded.
   - **Pattern:** The user frequently switches between Microsoft Excel/Edge and the internal HR system. This indicates a "swivel-chair" process where an employee reads tabular data (e.g., from an Excel tracking sheet) and manually inputs it into the web form.

2. **Leave Applications Approval (`/leave-applications`)**
   - **Volume:** 37 executions
   - **Manual Effort:** 191 clipboard copy-paste events.
   - **Pattern:** High frequency of switching between Microsoft Word (likely policy documents or justification forms) and the internal web system.

3. **Social Insurance Adjustments (`/social-insurance`)**
   - **Volume:** 26 executions
   - **Pattern:** Users toggle between Excel (`budget_analysis`), Word, and the web system, often copying small amounts of data.

4. **Onboarding / New Hire Registrations (`/onboarding`)**
   - **Volume:** 24 executions
   - **Pattern:** Requires cross-referencing Word documents (`nyusha_checklist`) with the web interface.

**Conclusion:** The **Payroll Items** process stands out not only because of its highest frequency but also due to the sheer volume of clipboard changes (307 events vs. 191 for the next highest). This implies highly repetitive data transcription which is extremely susceptible to human error and perfectly suited for automation.

---

## 3. Automation Candidate & ROI Rationale

### Recommended Candidate: Payroll Items Data Entry Automation

**Why this maximizes ROI:**
- **High Repetition & Volume:** It is the most frequently executed task in the observed production dataset.
- **Rule-Based & Deterministic:** The process involves copying data from an Excel spreadsheet into a fixed set of web form fields (`employee_name`, `item_name`, `amount`).
- **Error Reduction:** With over 300 copy-paste actions in a short window, the risk of mis-pasting numerical data (e.g., deducting 500,000 instead of 50,000) is high. Automation guarantees 100% transcription accuracy.
- **Time Savings:** Based on the logs, users spend a significant portion of their day on this repetitive task. Automating it frees up HR personnel for higher-value activities.

---

## 4. Working Prototype

We have developed a Python-based automation script using **Playwright** (`prototype.py`) to demonstrate the automation of the `/payroll-items` route. 

### How it Works:
1. **Data Ingestion:** The script reads a structured dataset (simulating an Excel/CSV file exported from another system or maintained by HR).
2. **System Authentication:** It navigates to the mock SSO login page and authenticates automatically.
3. **Data Entry Loop:** For each row in the spreadsheet, it:
   - Navigates to `/#/payroll-items`
   - Clicks the 'Register' button (`#btn-pi-register`)
   - Fills in the target fields (`input[name='employee_name']`, `input[name='amount']`, etc.)
   - Submits the form (`#btn-pi-ok`)

This deterministic approach perfectly mirrors the human operations observed in the logs, but executes in seconds rather than minutes.

---

## 5. Remaining Manual Work & Risks

While the prototype handles the core data entry loop, a fully productionized solution will need to account for the following:

### Remaining Manual Work
- **Exception Handling:** If an employee name is not found in the HR system, or if a deduction exceeds a legal limit, the bot should flag the record. A human operator will still need to review and resolve these exceptions.
- **Data Preparation:** The input Excel spreadsheet must be standardized. If the source data is currently received in unstructured emails or varying formats, HR staff will need to collate it into a standard template before running the script.

### Risks
- **UI Changes:** The script relies on specific CSS selectors (e.g., `#btn-pi-register`, `input[name='amount']`). If the internal web system is updated and these selectors change, the script will break and require maintenance.
- **Session Management & Timeouts:** The prototype assumes an active, fast connection. In production, we must handle slow page loads, SSO token expirations, and unexpected pop-ups (e.g., system maintenance alerts).
- **Security & Permissions:** The bot will require its own set of credentials or API access with appropriate write permissions to the HR system. Storing these credentials securely (e.g., in a secrets manager rather than plain text) is critical before deployment.
