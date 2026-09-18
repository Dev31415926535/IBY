# Operation Logs to Automation Proposal
### Forward Deployed Engineering (FDE) Deliverable — Dataset B Process Mining, Candidate Ranking, and Automation Prototype

**Prepared for:** Operations & HR Shared Services leadership
**Prepared by:** Forward Deployed Engineering
**Evidence base:** `dataset_b` desktop operation logs (no ground truth), benchmarked against `dataset_a` ground truth
**Artefacts referenced:** `version_2/segmenter_v2.py`, `version_2/benchmark.py`, `version_2/tune_hyperparameters.py`, `version_2/validate.py`, `version_2/automation_pipeline.py`, `version_2/segments.jsonl`, `version_1/outputs/dataset_b_inventory.json`, `version_1/outputs/dataset_b_actions.txt`

---

## Table of Contents

1. [Executive Summary & ROI Strategy](#1-executive-summary--roi-strategy)
2. [Step 1 & Step 2 — Dataset B Process Mining and Candidate Ranking](#2-step-1--step-2--dataset-b-process-mining-and-candidate-ranking)
3. [Step 3 — Automation Prototype and Technical Rationale](#3-step-3--automation-prototype-and-technical-rationale)
4. [Appendices](#4-appendices)

---

# 1. Executive Summary & ROI Strategy

## 1.1 The proposal in one paragraph

We mined 20,477 desktop and browser events from the 15 unlabelled Dataset B sessions, reconstructed 339 discrete work executions spanning 11 distinct business processes, and ranked them by recoverable operator time. One process dominates: **給与備考・控除整備 — Payroll Remarks & Deduction Maintenance**, transacted through the HR portal route `/#/payroll-items`. It consumes **37.8% of all labelled working time** in the corpus while accounting for only 13.0% of the executions, which is the signature of a long, transcription-heavy task rather than a short navigational one. We propose to automate the record-entry leg of that process with a **Python + Playwright + Pandas batch pipeline**, prototyped in `version_2/automation_pipeline.py`. The prototype reduces per-record human handling from a measured **13.5 seconds to an estimated 4.0 seconds of residual supervisory work — a 70.7% net reduction** — and removes the 307 clipboard transfer operations that currently sit between Excel and the browser.

## 1.2 Headline figures

| Metric | Value | Where it comes from |
|---|---|---|
| Sessions mined | 15 | `dataset_b_inventory.json` |
| Chunks mined | 20 | `dataset_b_inventory.json` |
| Raw events processed | 20,477 | `dataset_b_inventory.json` |
| Distinct operators (machine IDs) | 4 | session directory names in `segments.jsonl` |
| Executions reconstructed | 339 | `version_2/segments.jsonl` |
| Distinct process labels | 11 | Stage 3 of `validate.py` |
| Recorded desk time | 168.0 minutes | first-to-last segment per session |
| Classified working time | 143.1 minutes (85.2% coverage) | sum of segment durations |
| Selected target's share of working time | 37.8% (54.1 minutes) | per-label aggregation |
| Target executions | 44 | per-label aggregation |
| Target record submissions | 240 (`btn-pi-ok` clicks) | `dataset_b_actions.txt` |
| Measured manual cost per record | 13.5 s | 3,248 s ÷ 240 submissions |
| Projected residual human cost per record | 4.0 s | Section 3.5 build-up |
| Net human time reduction | 70.7% | Section 3.5 |
| Segmentation quality vs. Dataset A ground truth | IoU 0.715 · Boundary F1 0.674 · ARI 0.447 | `validate.py` Stage 2 |

## 1.3 Why this target rather than a bigger-sounding one

Three candidate processes generate more *executions* per unit of clock time than the payroll route, and two of them touch more applications. None of them convert into comparable recoverable hours. Ranking by execution count alone would have selected 育児・産休申請確認 (59 executions); ranking by application diversity would have selected the onboarding family. Ranking by **operator seconds recoverable per engineering hour invested** selects the payroll route decisively, because it combines the longest mean handling time (73.8 s per execution against a 25.3 s corpus mean), the densest clipboard traffic (307 events, 1.6× the next process), and the most regular DOM interaction signature (`pi-note` clicked 239 times against 240 submissions — effectively one note per record, every time).

## 1.4 ROI methodology

The ROI model converts three distinct log-derived quantities into recoverable cost. Each is computed independently so that a reviewer can discard any one term without invalidating the others.

**Term 1 — Direct handling time recovered.**
Manual unit cost is measured, not assumed: the 44 payroll executions consumed 3,248 seconds of classified working time and produced 240 confirmed submissions, giving 13.5 seconds of operator attention per record. Post-deployment residual work is built bottom-up in Section 3.5 and totals 4.0 seconds per record. The recovered quantity is therefore 9.57 seconds per record, or 2.66 hours per 1,000 records.

**Term 2 — Error rework avoided.**
Manual numeric transcription across an Excel-to-browser boundary carries a well-documented defect band of 1–3%. We model the conservative end, 1.2%, and assume 25 minutes of fully loaded effort to detect, investigate, correct and re-notify a single mis-keyed deduction. A deterministic pipeline does not mistype; its residual defect rate is bounded by source-data quality, modelled at 0.1%. The recovered quantity is 91.7% of the current rework load.

**Term 3 — Context-switching overhead avoided.**
The corpus shows 270 label transitions across 15 sessions — 18.0 process switches per session, with the payroll route participating in the plurality of them. Batch execution collapses 44 interleaved payroll visits into a single scheduled run, removing re-orientation cost each time an operator returns to a half-finished form. We deliberately assign **zero monetary value** to this term in the scenario table; it is documented as upside, not as justification.

**Costing basis.** Hours are valued at a fully loaded ¥3,800/hour for shared-services staff. Substitute the client's actual loaded rate and every currency figure scales linearly.

## 1.5 Cost recovery scenarios

Annual record volume is the single input we cannot derive from a 2.8-hour, single-day sample, so it is presented as a scenario axis rather than a point estimate. The base case corresponds to roughly 2,500 payroll-item records per month across the four observed operators.

| Annual records | Current handling (h) | Residual handling (h) | Handling hours recovered | Rework hours recovered | Total hours recovered | Value @ ¥3,800/h |
|---|---|---|---|---|---|---|
| 12,000 (low) | 45.1 | 13.2 | 31.9 | 55.0 | 86.9 | ¥330,220 |
| 30,000 (base) | 112.8 | 33.0 | 79.8 | 137.5 | 217.3 | ¥825,740 |
| 60,000 (high) | 225.5 | 66.0 | 159.5 | 275.0 | 434.5 | ¥1,651,100 |

**Investment against return.** Phase 1 as scoped in Section 3.1 costs roughly five and a half engineering sessions in total (itemised in Section 3.10), with no licence spend (Playwright and Pandas are open source) and no infrastructure beyond a scheduled runner with network reach to the HR portal. At the base case the payback horizon is the first quarter of operation, and the marginal cost of extending the same pipeline to the next two ranked processes is materially lower because the authentication, logging, and reconciliation layers are already built.

**Non-financial return.** The deterministic audit trail is arguably worth more than the hours. Today, evidence that a deduction was entered correctly exists only as a screenshot and a clipboard event. After deployment, every record carries a source row hash, a submission timestamp, a portal response assertion, and a reconciliation status — which converts payroll-correction disputes from archaeology into a query.

## 1.6 What this proposal explicitly does not claim

- It does not claim the measured 13.5 s/record generalises to month-end peak load; the corpus covers a single afternoon (2026-07-01, 16:44–19:34 UTC).
- It does not claim the segmenter's process boundaries are exact. Boundary F1 is 0.674 against a 15-second tolerance, and the segmentation ratio of 0.770 indicates mild under-segmentation. Volume figures carry that uncertainty and are validated against portal exports before any SLA is signed (Section 3.6, R-12).
- It does not claim the prototype is production-ready. It is a feasibility artefact that exercises the exact selectors observed in the logs; Section 3.7 describes what must be added before a single live record is written.

---

# 2. Step 1 & Step 2 — Dataset B Process Mining and Candidate Ranking

## 2.1 Corpus characterisation

Dataset B carries no ground truth, a different department, and a different application stack from Dataset A. Before any segmentation logic ran, we inventoried the raw material to understand which signals were dense enough to build on.

**Event composition (20,477 events):**

| Layer | Events | Share | Interpretation |
|---|---|---|---|
| L2 (OS-level) | 12,831 | 62.7% | Keystrokes, clicks, app switches, clipboard — the backbone signal |
| L1 (screen capture) | 4,759 | 23.2% | Smart screenshots, used only for spot verification |
| L3 (browser extension) | 2,764 | 13.5% | DOM-level clicks, form inputs, navigations — the highest-value signal, but intermittent |
| SYSTEM | 123 | 0.6% | Recording lifecycle, extension connectivity, uploads |

**Event-type frequency, ordered:** `screenshot_smart` 4,759 · `keystroke` 4,678 · `mouse_click` 2,133 · `browser_click` 1,914 · `mouse_scroll` 1,724 · `app_switch` 1,654 · `shortcut` 1,386 · `clipboard_change` 872 · `browser_form_input` 608 · `browser_navigation` 204 · `window_title_change` 186 · `window_state_change` 120 · `text_input_complete` 77 · `extension_connected` 42 · `extension_disconnected` 42 · `browser_error` 38 · `session_start` 15 · `session_end` 15 · `upload_started` 5 · `upload_completed` 4 · `mouse_double_click` 1.

Two absences shaped the design. There is not a single `dialog_opened`, `dialog_closed`, or `browser_alert` event in the whole of Dataset B, despite Dataset A containing 28, 28, and 129 respectively — yet Dataset B *does* contain 10 clicks on a DOM element classed `alert-box amber`. Interruption handling is therefore happening inside the page, invisible to the OS-level dialog channel. This directly drives risk R-03.

**Application footprint:** Microsoft Edge 13,300 · Microsoft Word 3,704 · Microsoft Excel 1,201 · OpenWith 757 · Notepad 599 · WindowsTerminal 407 · procmine-desktop-agent 205 · Windows Explorer 78 · ms-teams 73 · prl_cc 28. The work is browser-centric with a heavy document-reference tail, which is exactly the profile that rewards DOM automation and punishes coordinate-based macros.

**Portal landscape, by window-title event volume:** the HR payroll system (`HR人事給与システム`, 5,499 events across its single- and multi-tab title variants), the finance system (`財務会計システム`, 4,340), and the order/inventory system (`受発注在庫管理システム`, 3,314). Three portals, one browser profile, constant tab churn — the reason Phase 1 scope is fenced to a single portal.

## 2.2 Segmentation method

`segmenter_v2.py` reconstructs business executions from raw events using a three-signal rule cascade, chosen because Dataset B offers no labels to learn from and because a rule set is auditable by the operations team that has to trust its output.

1. **Route extraction.** For every event, a URL is resolved from `payload.url`, `payload.target_url`, `payload.href`, or `context.active_browser_tab.url`, then reduced to its fragment route (`#/payroll-items`) or path. Five portal routes map deterministically onto five HR process labels.
2. **Document-context fallback.** When no route is available — the operator is reading a Word procedure or an Excel workbook — the active window title is matched against six document stems (`keiyaku_kaijo`, `settai_keihi`, `gyomu_itaku`, `budget_analysis`, `nyusha_checklist`, `shinkuitorihikisaki`), each mapping to a reference-work label. This is what lifts label coverage to 85.2% of recorded desk time rather than leaving document work unattributed.
3. **Temporal closure.** A segment closes when the inter-event gap exceeds the idle threshold, or when a *differently* labelled event arrives. Unlabelled events do not close a segment, which keeps a five-second glance at Notepad inside the execution it belongs to. Segments shorter than 5 seconds are discarded as noise.

## 2.3 Parameter selection and accuracy benchmark

Thresholds were not guessed. `tune_hyperparameters.py` swept the idle threshold and brief-app-switch tolerance against Dataset A's `gt_manifest.json` execution windows, scoring each configuration on boundary F1 (15-second tolerance), temporal IoU, and Adjusted Rand Index.

| Idle threshold | App-switch tolerance | Boundary F1 | Avg IoU | ARI |
|---|---|---|---|---|
| 15.0 s | 5.0 s | 0.618 | 0.551 | 0.441 |
| 15.0 s | 15.0 s | 0.618 | 0.551 | 0.441 |
| 15.0 s | 30.0 s | 0.618 | 0.551 | 0.441 |
| 30.0 s | 5.0 s | 0.658 | 0.691 | 0.446 |
| 30.0 s | 15.0 s | 0.658 | 0.691 | 0.446 |
| 30.0 s | 30.0 s | 0.658 | 0.691 | 0.446 |
| **60.0 s** | **5.0 s** | **0.674** | **0.715** | **0.447** |
| 60.0 s | 15.0 s | 0.674 | 0.715 | 0.447 |
| 60.0 s | 30.0 s | 0.674 | 0.715 | 0.447 |

The sweep is informative beyond its winner. Score is flat across the app-switch axis and monotone across the idle axis, which tells us that **idle gaps, not application switches, carry the boundary signal** in this data — operators tab between Edge, Word, and Excel continuously *within* a single case, so treating every switch as a boundary shreds real executions. The 60-second configuration was carried into Dataset B.

`validate.py` then gates the output in three stages:

- **Stage 1 — structural integrity.** Every line of `segments.jsonl` validates against the segment schema, every `start` strictly precedes its `end`, no two segments of the same session overlap, and every `session_id` resolves to a real Dataset B directory. Passed.
- **Stage 2 — quantitative benchmark against Dataset A.** Avg IoU 0.715 (target ≥ 0.65, met), Boundary F1 0.674 (target ≥ 0.75, missed), segmentation ratio 0.770 (target ~1.0, under-segmenting), ARI 0.447 (target ≥ 0.70, missed).
- **Stage 3 — statistical sanity on Dataset B.** 339 segments, 11 distinct labels, 25.3 s mean duration.

**Honest reading of the misses.** The F1 shortfall is a boundary-precision problem, not a labelling problem: a 15-second tolerance is aggressive against humans who linger before committing to a task. The low ARI reflects the same effect amplified by the ratio of 0.770, where two adjacent executions of the same process occasionally merge into one. Neither failure mode threatens the ranking in Section 2.5, because **total time per label and clipboard density per route are robust to boundary jitter** — merging two adjacent payroll executions preserves their combined duration. It does mean execution *counts* should be read as a lower bound, and it is why the route-level interaction counts in Section 2.6, which are derived directly from raw clicks rather than from segments, are the primary volume evidence.

## 2.4 Discovered process taxonomy

Eleven labels emerged. Five are portal transactions; six are document-reference activities that sit alongside them.

| Label (JA) | English working name | Nature | Evidence anchor |
|---|---|---|---|
| 給与備考・控除整備 | Payroll remarks & deduction maintenance | Portal transaction | route `/#/payroll-items` |
| 育児・産休申請確認 | Childcare & maternity leave application check | Portal transaction | route `/#/leave-applications` |
| 社保・年金補正対応 | Social insurance & pension correction | Portal transaction | route `/#/social-insurance` |
| 入社照合・手当確認 | Onboarding reconciliation & allowance check | Portal transaction | route `/#/onboarding` |
| 住民税通知確認 | Resident tax notification check | Portal transaction | route `/#/resident-tax` |
| 業務委託経費規定 | Contractor expense policy reference | Document reference | `gyomu_itaku_*` Word documents |
| 入社チェックリスト新卒バッチ | New-graduate onboarding checklist batch | Document reference | `nyusha_checklist_shinsotsu_batch` |
| 契約解除手続き | Contract termination procedure | Document reference | `keiyaku_kaijo_tetsuzuki` |
| 新規取引先登録手続き | New vendor registration procedure | Document reference | `shinkuitorihikisaki_touroku_tetsuzuki` |
| 接待経費規定 | Entertainment expense policy reference | Document reference | `settai_keihi_kitei` |
| 予算差異分析 | Budget variance analysis | Spreadsheet analysis | `budget_analysis - Excel` |

## 2.5 Comparative table of discovered workflows

Structural variability is reported as the coefficient of variation (standard deviation ÷ mean) of execution duration. It is the single most decision-relevant column after time share: a low CV means the work follows one path and can be encoded as a deterministic script, while a high CV means the operator is branching on case content and any automation must carry an exception path.

| # | Process | Executions | Total time | Avg handling time | Median | Std. dev. | Variability (CV) | Operators involved | Sessions | Share of working time |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 給与備考・控除整備 (Payroll remarks & deductions) | 44 | 54.1 min | 73.8 s | 47.0 s | 63.8 s | 0.86 | 4 of 4 | 14 of 15 | 37.8% |
| 2 | 育児・産休申請確認 (Childcare/maternity leave) | 59 | 22.0 min | 22.3 s | 14.1 s | 23.8 s | 1.07 | 4 of 4 | 13 of 15 | 15.4% |
| 3 | 社保・年金補正対応 (Social insurance/pension) | 28 | 16.8 min | 36.1 s | 35.0 s | 23.0 s | 0.64 | 4 of 4 | 8 of 15 | 11.8% |
| 4 | 入社照合・手当確認 (Onboarding reconciliation) | 55 | 11.6 min | 12.6 s | 10.5 s | 6.5 s | 0.52 | 4 of 4 | 9 of 15 | 8.1% |
| 5 | 住民税通知確認 (Resident tax notification) | 31 | 10.6 min | 20.4 s | 17.3 s | 12.5 s | 0.61 | 4 of 4 | 8 of 15 | 7.4% |
| 6 | 業務委託経費規定 (Contractor expense policy) | 36 | 7.7 min | 12.8 s | 10.6 s | 13.2 s | 1.03 | 4 of 4 | 8 of 15 | 5.4% |
| 7 | 入社チェックリスト新卒バッチ (New-grad checklist) | 24 | 6.2 min | 15.5 s | 9.3 s | 21.6 s | 1.39 | 4 of 4 | 9 of 15 | 4.3% |
| 8 | 契約解除手続き (Contract termination) | 29 | 6.0 min | 12.4 s | 10.5 s | 7.8 s | 0.63 | 4 of 4 | 8 of 15 | 4.2% |
| 9 | 新規取引先登録手続き (New vendor registration) | 10 | 4.6 min | 27.4 s | 7.6 s | 55.7 s | 2.03 | 4 of 4 | 7 of 15 | 3.2% |
| 10 | 接待経費規定 (Entertainment expense policy) | 16 | 2.5 min | 9.4 s | 8.9 s | 2.0 s | 0.21 | 2 of 4 | 4 of 15 | 1.8% |
| 11 | 予算差異分析 (Budget variance analysis) | 7 | 1.2 min | 9.8 s | 9.8 s | 0.6 s | 0.06 | 1 of 4 | 1 of 15 | 0.8% |

Reading notes that matter for selection:

- **Row 1 is the only row where mean and median diverge by more than 25 seconds** (73.8 s vs 47.0 s). The distribution is right-skewed with a 279-second maximum: most payroll visits are moderate, a minority are long multi-record batches. That skew is the automation opportunity — the long tail is bulk entry, not complex judgement.
- **Row 2 has the highest execution count but the second-highest CV** (1.07). Leave applications are short, frequent, and inconsistent, consistent with reading a Word justification document and making a case-by-case approval decision. Automating the decision is out of the question; automating the 22-second wrapper around it recovers little.
- **Row 11 is the lowest-variability process in the corpus** (CV 0.06) but is performed by a single operator in a single session for 1.2 minutes total. Perfect regularity at negligible volume is a trap, and it is the clearest illustration of why variability must be read jointly with volume.
- **Row 9 has an extreme CV of 2.03** (median 7.6 s against a 194-second maximum), the signature of a rare, occasionally very involved procedure. Such processes are poor first targets and good candidates for guided-workflow tooling rather than straight-through automation.

## 2.6 Route-level interaction evidence

Segment boundaries can jitter; raw click and clipboard counts cannot. This table is derived directly from `dataset_b_actions.txt` and is the load-bearing evidence for the ranking.

| Route | Visits | Clipboard events | Commit clicks | Note-field clicks | Clipboard per visit | Records per visit | Commit selector |
|---|---|---|---|---|---|---|---|
| `/payroll-items` | 43 | 307 | 240 (`btn-pi-ok`) | 239 (`pi-note`) | 7.14 | 5.58 | `#btn-pi-ok` |
| `/leave-applications` | 37 | 191 | 146 (`btn-la-ok`) | 146 (`la-note`) | 5.16 | 3.95 | `#btn-la-ok` |
| `/onboarding` | 24 | 137 | 92 (`btn-ob-ok`) | 92 (`ob-note`) | 5.71 | 3.83 | `#btn-ob-ok` |
| `/social-insurance` | 26 | 103 | 82 (`btn-si-ok`) | 82 (`si-note`) | 3.96 | 3.15 | `#btn-si-ok` |
| `/resident-tax` | 21 | 70 | 69 (`btn-rt-ok`) | 69 (`rt-note`) | 3.33 | 3.29 | `#btn-rt-ok` |

629 portal records were committed in 2.8 hours of recorded work across four operators. The payroll route alone accounts for 38.2% of them and 45.4% of all clipboard traffic. The near-perfect one-to-one pairing between note-field clicks and commit clicks on every route is a strong structural finding: the note field is not optional decoration, it is part of the record, and any automation that cannot populate it is not actually automating the task.

**Supporting application evidence for the payroll route:** Edge 4,913 events, OpenWith 689, Excel 437, Notepad 351, Word 264. The OpenWith volume is the second-highest of any application on this route and signals repeated file-association prompts when attachments are opened — a desktop-level obstacle that a headless pipeline must design around rather than reproduce (R-10).

## 2.7 Ranking model

Candidates were scored on five weighted dimensions. Weights were set before the scores were computed, to avoid fitting the model to the desired answer.

| Dimension | Weight | Rationale |
|---|---|---|
| Recoverable time (share of working time) | 35% | The direct ROI numerator |
| Transcription density (clipboard events per visit) | 25% | Proxy for swivel-chair work, which automates cleanly and errs frequently |
| Determinism (inverse of duration CV) | 20% | Predicts straight-through rate and inversely predicts exception-queue volume |
| Selector stability (share of interactions on ID-bearing elements) | 10% | Predicts maintenance cost of a DOM-based implementation |
| Breadth of adoption (operators and sessions covered) | 10% | Guards against optimising one person's idiosyncratic workflow |

| Rank | Process | Time | Density | Determinism | Selectors | Breadth | Weighted score |
|---|---|---|---|---|---|---|---|
| 1 | 給与備考・控除整備 | 10.0 | 10.0 | 6.0 | 9.5 | 9.3 | **9.08** |
| 2 | 入社照合・手当確認 | 2.1 | 8.0 | 10.0 | 8.5 | 6.0 | 6.19 |
| 3 | 育児・産休申請確認 | 4.1 | 7.2 | 4.9 | 9.0 | 8.7 | 5.99 |
| 4 | 社保・年金補正対応 | 3.1 | 5.5 | 8.1 | 9.5 | 5.3 | 5.56 |
| 5 | 住民税通知確認 | 2.0 | 4.7 | 8.5 | 9.0 | 5.3 | 5.01 |
| 6 | Document-reference cluster (rows 6–10) | 1.4 | 1.0 | 5.2 | 2.0 | 5.5 | 2.53 |
| 7 | 予算差異分析 | 0.2 | 0.5 | 10.0 | 1.0 | 1.3 | 2.43 |

Scores are normalised to 10 within each dimension, with determinism scaled against the most regular transaction route rather than against the corpus minimum. The gap between rank 1 and rank 2 is 2.89 points — more than double the entire spread across ranks 2 through 5. There is no close second, which is the ideal condition for a first deployment: no stakeholder is left arguing that a different process should have gone first.

## 2.8 Pareto position

Ordering the eleven labels by total time and accumulating:

| Cumulative processes | Cumulative share of working time |
|---|---|
| Top 1 | 37.8% |
| Top 2 | 53.2% |
| Top 3 | 64.9% |
| Top 4 | 73.0% |
| **Top 5** | **80.4%** |
| Top 6 | 85.7% |
| Top 7 | 90.1% |
| Top 8 | 94.3% |
| Top 9 | 97.4% |
| Top 10 | 99.2% |
| Top 11 | 100.0% |

The corpus obeys the 80/20 rule almost exactly: **5 of 11 processes (45%) hold 80.4% of the working time**, and those five are precisely the five portal transaction routes. The document-reference cluster, which occupies six labels, carries under 20% combined and consists of reading rather than transacting — genuinely low-automation-yield work. This shape is the strategic argument for the roadmap in Section 3.9: build the transaction pipeline once against the payroll route, then extend it across the remaining four routes, whose selector conventions (`btn-XX-ok`, `XX-note`) are visibly parallel. The marginal engineering cost of route two is a fraction of route one.

## 2.9 Prioritised automation candidates

**Priority 1 — 給与備考・控除整備 via `/#/payroll-items`.** Selected for Phase 1. 37.8% of working time, 240 records, 307 clipboard operations, stable `#btn-pi-ok` / `#pi-note` selectors, all four operators, 14 of 15 sessions. Build now.

**Priority 2 — 入社照合・手当確認 via `/#/onboarding`.** Recommended as the first Phase 2 extension despite ranking fourth on time, because it has the second-lowest CV among the transaction routes (0.52) and 5.71 clipboard events per visit. It is the cheapest incremental win once the pipeline exists: same commit-button convention, same note-field pattern, highly regular duration.

**Priority 3 — 社保・年金補正対応 via `/#/social-insurance`.** 11.8% of time at CV 0.64, but tightly coupled to the `budget_analysis` Excel workbook (491 events on this route) and to the finance portal. Automate after a canonical spreadsheet contract exists.

**Priority 4 — 住民税通知確認 via `/#/resident-tax`.** Regular (CV 0.61) but low volume in-sample and heavily weighted toward the finance portal (718 + 292 + 204 window-title events) rather than HR. Revisit once Phase 2 authentication covers the second portal.

**Priority 5 — 育児・産休申請確認 via `/#/leave-applications`.** Second by time and third by weighted score, but deprioritised deliberately. 1,602 Word events on this route against 2,620 Edge events means roughly 38% of the effort is reading policy and justification documents, and CV 1.07 confirms case-by-case judgement. The appropriate intervention is decision support — pre-populating the form and surfacing the relevant policy clause — not straight-through processing.

**Not recommended for automation.** The document-reference cluster (業務委託経費規定, 契約解除手続き, 接待経費規定, 新規取引先登録手続き, 入社チェックリスト新卒バッチ) and 予算差異分析 together account for 19.6% of time spread across six labels, with no commit-click signature in the logs at all. There is nothing transactional to automate; the realistic intervention is knowledge management — indexing those Word procedures so they are found faster. 新規取引先登録手続き additionally shows CV 2.03, the least predictable process in the corpus.

---

# 3. Step 3 — Automation Prototype and Technical Rationale

## 3.1 Target selection and scope boundary

**Target.** Batch entry of payroll remark and deduction records into the HR portal at `/#/payroll-items`, replacing the observed Excel→clipboard→browser transcription loop.

**In scope for Phase 1:**

| Capability | Justification from the logs |
|---|---|
| Ingest a canonical spreadsheet (XLSX/CSV) of payroll-item rows | Excel is present on 437 events on this route; `expense_calc` and `budget_analysis` are the dominant workbooks |
| Authenticate to the portal via the SSO form | `sso-mock.html` appears as both source and destination in the route-transition graph |
| Navigate to `/#/payroll-items` per record | 43 recorded visits |
| Populate `employee_name`, `item_name`, `amount` | The three fields reconstructable from clipboard payloads and form-input events |
| Populate the note field `#pi-note` with a templated, auditable string | 239 note clicks against 240 commits |
| Commit via `#btn-pi-ok` | 240 recorded commits |
| Validate each row before submission and divert failures to an exception file | Amount fields are the highest-consequence transcription risk |
| Emit a per-row structured run log with outcome and timing | Required for the reconciliation control in Section 3.7 |

**Explicitly deferred to Phase 2:**

| Deferred item | Why it is deferred |
|---|---|
| The other four portal routes | Prove the pattern once; the selector convention makes replication cheap |
| Finance and inventory portals | Separate authentication domains; 2 of the 3 portals are out of the HR team's change control |
| Reading source data directly from operator mailboxes or Teams | No mail-client signal in Dataset B beyond 73 Teams events; the ingestion contract would be speculative |
| Automated judgement on flagged records | The amber alert-box interactions indicate portal-side business rules we have not yet enumerated |
| Free-text note composition beyond templates | Genuine human content; see residual task 4 |
| OCR over `screenshot_smart` captures | `context.extracted_text` already covers ~4% of events and no automation decision depends on pixels |
| Month-end and year-end variants | Unobserved in a single-afternoon corpus |

**Scope discipline rationale.** A first deployment that writes to one route, in one portal, from one file format, can be reviewed line-by-line by the operations owner and switched off in one action. Every additional surface in Phase 1 multiplies the approval burden without multiplying the recovered hours — 37.8% of the time sits behind the single route we chose.

## 3.2 Architectural justification

**Selected form: a Python batch pipeline — Pandas for ingestion and validation, Playwright (async Chromium) for DOM interaction.** Implemented in `version_2/automation_pipeline.py`.

| Requirement derived from the logs | How the chosen stack satisfies it |
|---|---|
| Source of truth is tabular and spreadsheet-native | Pandas reads XLSX/CSV natively, enforces dtypes, and makes row-level validation declarative |
| The target is a modern SPA with fragment routing (`#/payroll-items`) | Playwright waits on the DOM and on network idle, so it tolerates client-side re-renders that a request-replay approach cannot see |
| Elements carry stable IDs for the critical controls (`#btn-pi-ok`, `#pi-note`) | Playwright selects by ID first and falls back to role/text, giving a two-tier selector strategy |
| Authentication is an interactive SSO form, not a documented API | Driving the real login form reuses the organisation's existing identity path without minting new trust |
| Frontend validation is business logic the organisation relies on | UI-level automation triggers exactly the same client-side rules a human triggers, so the bot cannot write records a human could not |
| Latency is variable across three portals on one browser profile | Playwright's auto-waiting replaces sleep-based timing, which is the primary source of flakiness in scripted UI work |
| Runs must be auditable | A single Python process emits one structured log line per record, with input hash, selectors used, and portal response |

**Rejected: coordinate or image-based GUI macros (PyAutoGUI, SikuliX, Power Automate Desktop).**
The logs make this rejection concrete rather than theoretical. Operators work across 13,300 Edge events with constant tab-count changes — window titles shift between `HR人事給与システム`, `HR人事給与システム and 1 more page`, and `HR人事給与システム and 2 more pages` (3,190 / 1,475 / 834 events respectively). A macro keyed to window title or screen position breaks every time a second tab opens. Add 120 `window_state_change` events and multi-monitor context, and the maintenance burden dominates the savings.

**Rejected: direct HTTP/API scripting (`requests`, `httpx`).**
Dataset B contains 204 `browser_navigation` events and zero evidence of a documented service contract. Reconstructing the endpoints from observed traffic would require inferring CSRF handling and SSO token exchange from behaviour, producing a client that is undocumented, unversioned, and able to bypass every frontend validation the HR team depends on. The speed advantage is irrelevant at 240 records per afternoon; an unattended run measured in minutes is already faster than the business needs. This decision is explicitly revisitable: if the portal team publishes an API, the Playwright layer is the only component that would be replaced, because ingestion, validation, logging, and reconciliation are deliberately kept independent of it.

**Rejected: an LLM-driven browser agent.**
Payroll deductions are a regulated, numeric, high-consequence domain where the correct behaviour is fully specified by a spreadsheet row and a form schema. A non-deterministic planner introduces variance with no corresponding benefit, cannot be diffed or code-reviewed, is far harder to certify for an audit, and costs per record forever. The one place where language understanding genuinely earns its keep is Japanese free-text note composition for exception cases — which is precisely the residual we leave with a human in Section 3.5, and the one narrowly-scoped LLM assist we would consider in Phase 2, behind human approval.

**Rejected: a bespoke internal web application for data ingestion.**
This replaces one manual entry surface with another, requires hosting, authentication, and a support model of its own, and does not remove a single one of the 307 clipboard operations. It solves the wrong half of the problem.

**Rejected: a commercial RPA platform.**
Licence cost, a proprietary artefact format that cannot be code-reviewed or diffed in the repository, and vendor lock-in on a workload that is 300 lines of maintainable Python. Revisit only if the organisation standardises on RPA for reasons beyond this process.

## 3.3 Prototype design

The prototype demonstrates the full control path against the exact selectors observed in the logs, and degrades to a simulation loop when the portal is unreachable, so that the pipeline mechanics can be exercised without a live system.

**Execution trace from `version_2/outputs/pipeline_out.txt`:**

```
Loading data from spreadsheet pipeline...
Loaded 3 rows. Commencing web injection...
[Warning] SSO Mock unavailable. Proceeding with simulation loop.
[SIMULATED] Registered EMP-001 -> 社宅費: 50000 JPY
[SIMULATED] Registered EMP-002 -> 財形貯蓄: 20000 JPY
[SIMULATED] Registered EMP-003 -> 社宅費: 55000 JPY

=== Pipeline Report ===
Total processed: 3
Success: 3
Errors: 0
=======================
```

**Component boundaries:**

| Component | Responsibility | Depends on |
|---|---|---|
| Ingestion | Read the workbook, normalise column names, coerce types, hash each row for traceability | Pandas |
| Validation | Enforce required fields, numeric bounds on `amount`, employee-ID format, duplicate detection within the batch | Pure Python; no portal contact |
| Session | Establish an authenticated browser context once per run and reuse it across records | Playwright |
| Record writer | Navigate, open the entry form, fill four fields, commit, assert the post-commit state | Playwright |
| Outcome recorder | Append a structured result per row: status, elapsed ms, selector path, portal message | Standard library |
| Reporting | Emit the run summary and the exception file for human follow-up | Pandas |

The boundary that matters is between **Validation** and **Record writer**: no row reaches the browser without passing validation, so the portal never receives a value that the pipeline itself considers suspect. This is what makes the 0.1% modelled residual defect rate defensible — remaining defects originate in source data that is internally consistent but wrong, not in the transfer.

## 3.4 Selector map derived from the logs

Every selector below is grounded in an observed interaction count, which is the difference between a script written against a live system and one written against evidence.

| Purpose | Selector | Observed evidence | Stability |
|---|---|---|---|
| Commit record | `#btn-pi-ok` | 240 clicks on the payroll route | High — ID-bearing |
| Note field | `#pi-note` | 239 clicks | High — ID-bearing |
| Open entry form | `#btn-pi-register` | **Not observed in Dataset B** | Unverified — see R-02 |
| Employee field | `input[name='employee_name']` | Inferred from `browser_form_input` (608 corpus-wide) | Medium |
| Item field | `input[name='item_name']` | Inferred from clipboard-to-form pairing | Medium |
| Amount field | `input[name='amount']` | Inferred; highest-consequence field | Medium |
| In-page warning | `.alert-box.amber` | 2 clicks on payroll, 8 on leave | Low — class-only |
| Layout containers | `.side`, `.panel-head`, `.panel-body`, `.main`, `.nav-link` | 3 / 1 / 1 / 4 / 1 clicks | Low — never use for automation |

The Medium-stability rows are the honest ones: `text_input_complete` fired only 77 times in the whole corpus, so field-level content is not directly recoverable and these three selectors are inferences to be confirmed in staging before the first live run (R-04).

## 3.5 Residual manual work after deployment

Automation moves work; it does not evaporate it. The table below decomposes what a human still does per batch, converted to a per-record equivalent so it can be subtracted from the measured 13.5 s baseline. A batch is 1,000 records.

| # | Residual task | What the human actually does | Per batch | Per record | Can it be removed later? |
|---|---|---|---|---|---|
| 1 | Source preparation | Export or assemble the payroll-item rows into the canonical template; confirm the pay period and cost-centre columns | 15 min | 0.90 s | Yes — Phase 2 direct system export |
| 2 | Pre-run validation review | Open the validation report, resolve schema violations, out-of-band amounts, unknown employee IDs before the run | 8 min | 0.48 s | Partially — shrinks as source quality improves |
| 3 | Exception queue resolution | Work the rows the bot refused or the portal rejected: employee not found, deduction above policy limit, duplicate item. Modelled at a 4.0% exception rate × 40 s each | 26.7 min | 1.60 s | Partially — falls as business rules are encoded |
| 4 | Free-text note authoring | Replace the templated note with genuine Japanese commentary where a case requires it. Modelled at 1.5% of records × 25 s | 6.3 min | 0.38 s | Assisted in Phase 2, never fully removed |
| 5 | Post-run reconciliation & sign-off | Compare the run log against the portal's record count, confirm totals, sign off the batch | 10 min | 0.60 s | No — this is the control that makes automation safe |
| | **Total residual** | | **66.0 min** | **3.96 s** | |

**Net time reduction:**

| Quantity | Value |
|---|---|
| Measured manual handling per record | 13.53 s |
| Residual human handling per record | 3.96 s |
| Human time recovered per record | 9.57 s |
| **Net reduction in human handling** | **70.7%** |
| Unattended machine time per record | ~2.5 s |
| Wall-clock for a 1,000-record batch, unattended | ~42 min, schedulable outside working hours |
| Clipboard operations eliminated per 1,000 records | ~1,280 (extrapolated from 307 per 240 records) |

Two properties of this result deserve emphasis. First, **the residual is dominated by controls, not by transcription** — tasks 2, 3, and 5 are review activities that exist because we chose a supervised rollout, and they are exactly the activities that a human should be doing. Second, the residual is *mostly fixed per batch rather than per record* — tasks 1, 2, and 5 are batch-level, so the effective reduction improves as batch size grows: at 2,000 records per batch the residual falls to roughly 3.0 s/record and the net reduction rises past 77%.

## 3.6 Risks and mitigations

Every risk below is anchored to a specific observation in the corpus. Likelihood and impact are assessed for Phase 1 as scoped.

| ID | Category | Risk | Log evidence | Likelihood | Impact | Mitigation |
|---|---|---|---|---|---|---|
| R-01 | Technical | Layout elements are addressable only by CSS class, so any restyling silently breaks selection | Clicks recorded on `alert-box amber`, `side`, `panel-head`, `panel-body`, `main`, `nav-link` — none ID-bearing | High | Medium | Restrict automation to ID-bearing selectors; add role/label fallbacks; run a selector health-check against staging before every batch and abort the run on mismatch |
| R-02 | Technical | The entry-form trigger `#btn-pi-register` assumed by the prototype never appears in Dataset B's click inventory; the real entry path may differ | Top payroll clicks are `btn-pi-ok` (240) and `pi-note` (239) only | High | High | Confirm the entry path in staging before the first live run; treat the selector map (Section 3.4) as a versioned configuration file, not as inline constants |
| R-03 | Technical | Native dialogs and alerts are invisible in this corpus, yet in-page warnings demonstrably occur — an unhandled interruption will stall an unattended run | Zero `dialog_opened`/`dialog_closed`/`browser_alert` in Dataset B versus 28/28/129 in Dataset A, while `alert-box amber` was clicked 10 times | High | High | Register a Playwright `page.on("dialog")` handler that logs and dismisses; treat `.alert-box.amber` as an explicit branch that halts the record and routes it to the exception queue; set a per-record watchdog timeout |
| R-04 | Technical | Field-level input content is not reliably recoverable from the logs, so the three input selectors are inferences | `text_input_complete` fired 77 times against 4,678 keystrokes (1.6%); the schema documents it as defective | Medium | High | Confirm the form schema against staging DOM; never derive field mappings from `text_input_complete`; reconstruct expected values from `clipboard_change` and `keystroke` for the dual-run comparison |
| R-05 | Technical | Browser-extension telemetry drops out mid-session, so L3-only verification is unreliable | 42 `extension_connected` and 42 `extension_disconnected` across 15 sessions (~2.8 cycles per session); 89 events under the window title `Turn off extensions in developer mode` | Medium | Medium | Verify success from the portal's own post-commit state and a post-run export reconciliation, never from extension telemetry alone |
| R-06 | Technical | Navigation failures occur in normal operation and would be recorded as false successes by a naive script | `/error/404.htm` appears as a transition target from `/payroll-items`, `/resident-tax`, and `/onboarding`; 38 `browser_error` events in Dataset B | Medium | Medium | Assert the resolved route after every navigation; retry with exponential backoff up to three attempts; escalate the row to the exception queue rather than skipping it |
| R-07 | Operational | The note field carries human meaning on essentially every record; a blanket template would degrade information quality | 239 `pi-note` clicks against 240 commits | High | Medium | Template only where the source row supplies structured justification; flag rows whose source note field is non-empty and free-form for human authoring (residual task 4) |
| R-08 | Operational | Source spreadsheets are not standardised, so ingestion may silently mis-map columns | Two distinct workbooks dominate: `expense_calc` (605 events) and `budget_analysis` (573) | High | High | Publish a canonical template with a version header; reject any workbook whose column signature does not match; fail the whole batch rather than a subset on schema mismatch |
| R-09 | Operational | Work interleaves across three portals, so a payroll batch may depend on finance-side state | Window-title volumes: HR 5,499, finance 4,340, inventory 3,314 | Medium | Medium | Fence Phase 1 to the HR portal; make cross-portal dependencies an explicit precondition on the input file rather than something the bot resolves |
| R-10 | Operational | Desktop file-association prompts appear frequently and would block any desktop-level automation | `OpenWith` accounts for 757 corpus events and 689 on the payroll route alone | Medium | Low | Ingest from a watched folder or object store; never drive OS file dialogs; run the browser headless in a controlled profile |
| R-11 | Operational | Handling time varies widely between executions, indicating case variants the prototype has not enumerated | Payroll CV 0.86, durations from 7 s to 279 s | High | Medium | Size the exception queue for the observed tail; instrument variant frequency during the shadow period and encode the recurring variants before scaling batch size |
| R-12 | Analytical | Volume and time estimates inherit segmentation error | Boundary F1 0.674 against a 0.75 target; ARI 0.447; segmentation ratio 0.770 (under-segmentation) | High | Medium | Treat execution counts as lower bounds; validate annual volume against a portal-side export before committing to an SLA; prefer raw click counts (629 commits) over segment counts as the volume basis |
| R-13 | Analytical | The corpus is a single afternoon from four operators, with no month-end or year-end coverage | All 15 sessions fall on 2026-07-01 between 16:44 and 19:34 UTC, totalling 168 minutes | High | Medium | Re-run the mining pipeline over a month-end capture before Phase 2 scoping; keep the ROI scenario table rather than a point estimate until then |
| R-14 | Rollout | An unsupervised bot writing payroll deductions is an unacceptable day-one risk | Amount fields are free numeric input; a mis-keyed order of magnitude is invisible at the DOM level | Medium | Critical | Staged rollout (Section 3.7): shadow, dual-run with reconciliation, then supervised live with a maker-checker gate and a documented kill switch |
| R-15 | Rollout | Credential handling for an unattended account | The logs show an interactive SSO form (`sso-mock.html`) with no service-account path | High | High | Provision a dedicated bot identity with write scope limited to payroll items; store credentials in a secrets manager; never in source, environment files, or the run log; rotate on a fixed schedule |
| R-16 | Rollout | Operator trust erodes if the bot's behaviour is opaque | 18.0 process switches per session show operators currently hold the full context themselves | Medium | Medium | Publish the per-row run log to the team, keep the exception queue in a shared location, and review the first four weeks of runs jointly with the operations owner |

## 3.7 Rollout plan

| Stage | Duration | Bot write access | Human control | Exit criterion |
|---|---|---|---|---|
| Shadow | 2 weeks | None — dry run against staging | Operators work normally; the bot produces a would-have-written file | ≥ 99% field-level agreement with the operator's actual entries |
| Dual-run | 2 weeks | Staging only | Every batch reconciled row-by-row against the manual result | Zero unexplained divergences across two consecutive weeks |
| Supervised live | 4 weeks | Production, batch-scoped | Maker-checker sign-off per batch; kill switch documented and tested | Straight-through rate ≥ 95%, exception rate ≤ 5% |
| Steady state | Ongoing | Production, scheduled | Post-run reconciliation only (residual task 5) | Monthly KPI review |

## 3.8 Operating KPIs

| KPI | Baseline from the logs | Phase 1 target |
|---|---|---|
| Human handling time per record | 13.5 s | ≤ 4.0 s |
| Straight-through rate | n/a (0% automated) | ≥ 95% |
| Transcription defect rate | 1.2% modelled | ≤ 0.1% |
| Clipboard operations per 1,000 records | ~1,280 | 0 |
| Batch wall-clock, 1,000 records | ~3.75 operator-hours | ≤ 45 min unattended |
| Selector-breakage incidents | n/a | ≤ 1 per quarter, detected by pre-run health check rather than by a failed batch |
| Exception queue age | n/a | 95% resolved within one business day |

## 3.9 Phase 2 roadmap

1. **Route extension.** Apply the same pipeline to `/#/onboarding`, then `/#/social-insurance` and `/#/resident-tax`. The shared `btn-XX-ok` / `XX-note` convention means the per-route increment is a configuration entry plus a validation schema, not a new codebase. Reaching all five transaction routes addresses the 80.4% of working time identified in Section 2.8.
2. **Direct source ingestion.** Replace the canonical-template hand-off (residual task 1) with a scheduled export from the upstream system, removing 0.90 s/record and the class of errors that R-08 mitigates.
3. **Business-rule encoding.** Convert the recurring exception reasons observed during the supervised period into pre-submission validations, shrinking residual task 3.
4. **Note-authoring assist.** A narrowly-scoped Japanese drafting aid for exception notes, always behind human approval — the single place where a language model earns its place in this architecture.
5. **Decision support for leave applications.** Rather than automating the judgement in 育児・産休申請確認, pre-populate the form and surface the governing policy clause from the Word corpus, attacking the 38% document-reading component directly.
6. **Continuous process mining.** Re-run `segmenter_v2.py` monthly against fresh captures to track whether the automated process actually leaves the operators' time distribution, and to detect drift in the remaining manual work.

## 3.10 Effort estimate

| Workstream | Effort | Notes |
|---|---|---|
| Selector confirmation and staging access | 0.5 session | Resolves R-02 and R-04 |
| Ingestion, validation, canonical template | 1 session | Pandas layer, independent of the browser |
| Playwright record writer with dialog, alert, and retry handling | 1.5 sessions | Resolves R-03 and R-06 |
| Run logging, exception queue, reconciliation report | 1 session | The control layer the rollout depends on |
| Secrets, scheduling, service account | 0.5 session | Resolves R-15 |
| Shadow and dual-run support | 1 session | Spread across the 4-week validation window |
| **Phase 1 total** | **~5.5 engineering sessions** | Excludes the client-side calendar time of the staged rollout |

Calendar time is dominated by the eight-week staged rollout, not by engineering. The build itself can be complete before the shadow period begins.

---

# 4. Appendices

## Appendix A — Reproduction

```bash
# 1. Sweep segmentation parameters against Dataset A ground truth,
#    then apply the best configuration to Dataset B.
python version_2/tune_hyperparameters.py

# 2. Three-stage validation: schema integrity, quantitative benchmark,
#    statistical sanity checks.
python version_2/validate.py

# 3. Exercise the automation pipeline (falls back to a simulation loop
#    when the portal is unreachable).
python version_2/automation_pipeline.py
```

Outputs are written to `version_2/segments.jsonl` and `version_2/outputs/`.

## Appendix B — Per-session breakdown

| Session | Operator | Segments | Recorded span | Classified time | Payroll time |
|---|---|---|---|---|---|
| ses_20260701-164424 | CHAITANYA0BCF | 19 | 11.1 min | 9.5 min | 3.8 min |
| ses_20260701-171614 | CHAITANYA0BCF | 39 | 13.7 min | 10.9 min | 2.8 min |
| ses_20260701-173246 | SIDDHIGUPTAB00B | 31 | 12.5 min | 9.5 min | 1.5 min |
| ses_20260701-173642 | NEELA9BAF | 9 | 10.1 min | 9.8 min | 6.0 min |
| ses_20260701-175258 | LAPTOP-76QMG9DE | 23 | 12.3 min | 10.6 min | 6.2 min |
| ses_20260701-175747 | SIDDHIGUPTAB00B | 13 | 10.8 min | 9.9 min | 5.5 min |
| ses_20260701-180923 | NEELA9BAF | 33 | 12.4 min | 9.6 min | 2.2 min |
| ses_20260701-181413 | LAPTOP-76QMG9DE | 22 | 12.8 min | 10.6 min | 3.0 min |
| ses_20260701-181913 | SIDDHIGUPTAB00B | 21 | 9.8 min | 8.0 min | 1.9 min |
| ses_20260701-182634 | NEELA9BAF | 13 | 10.3 min | 9.5 min | 2.2 min |
| ses_20260701-183232 | LAPTOP-76QMG9DE | 11 | 6.8 min | 6.2 min | 3.9 min |
| ses_20260701-184201 | LAPTOP-76QMG9DE | 69 | 16.2 min | 12.5 min | 0.7 min |
| ses_20260701-190250 | NEELA9BAF | 15 | 9.9 min | 8.5 min | 6.7 min |
| ses_20260701-191537 | LAPTOP-76QMG9DE | 14 | 11.1 min | 10.0 min | 7.7 min |
| ses_20260701-192455 | NEELA9BAF | 7 | 8.2 min | 8.1 min | 0.0 min |
| **Total** | 4 operators | **339** | **168.0 min** | **143.1 min** | **54.1 min** |

Session 184201 is worth noting: 69 segments in 16.2 minutes — 4.3 executions per minute — with only 0.7 minutes of payroll work. It is the corpus's clearest example of fragmented, interrupt-driven work, and a useful counter-example to the batchable pattern we are automating.

## Appendix C — Label frequency distribution by segment count

Reported by `validate.py` Stage 3, shown here for completeness alongside the time-weighted view in Section 2.5. The two orderings differ substantially, which is the point: segment share measures how often an operator touches a process, while time share measures what it costs.

| Label | Share of segments | Share of working time | Ratio |
|---|---|---|---|
| 育児・産休申請確認 | 17.4% | 15.4% | 0.89 |
| 入社照合・手当確認 | 16.2% | 8.1% | 0.50 |
| 給与備考・控除整備 | 13.0% | 37.8% | 2.91 |
| 業務委託経費規定 | 10.6% | 5.4% | 0.51 |
| 住民税通知確認 | 9.1% | 7.4% | 0.81 |
| 契約解除手続き | 8.6% | 4.2% | 0.49 |
| 社保・年金補正対応 | 8.3% | 11.8% | 1.42 |
| 入社チェックリスト新卒バッチ | 7.1% | 4.3% | 0.61 |
| 接待経費規定 | 4.7% | 1.8% | 0.38 |
| 新規取引先登録手続き | 2.9% | 3.2% | 1.10 |
| 予算差異分析 | 2.1% | 0.8% | 0.38 |

A ratio above 1.0 marks a process that costs more than its visit frequency suggests. Only two processes qualify, and the payroll route's 2.91 is nearly double the next. Selecting on visit frequency alone would have inverted the ranking and targeted a process with half the cost per touch.

## Appendix D — Glossary

| Japanese | English | Context |
|---|---|---|
| 給与備考・控除整備 | Payroll remarks & deduction maintenance | Phase 1 automation target |
| 育児・産休申請確認 | Childcare & maternity leave application check | Phase 2 decision support candidate |
| 社保・年金補正対応 | Social insurance & pension correction | Phase 2 route extension |
| 入社照合・手当確認 | Onboarding reconciliation & allowance check | First Phase 2 route extension |
| 住民税通知確認 | Resident tax notification check | Phase 2 route extension |
| 業務委託経費規定 | Contractor expense policy | Reference document |
| 契約解除手続き | Contract termination procedure | Reference document |
| 接待経費規定 | Entertainment expense policy | Reference document |
| 新規取引先登録手続き | New vendor registration procedure | Reference document |
| 入社チェックリスト新卒バッチ | New-graduate onboarding checklist batch | Reference document |
| 予算差異分析 | Budget variance analysis | Spreadsheet activity |
| HR人事給与システム | HR & payroll system | Phase 1 target portal |
| 財務会計システム | Financial accounting system | Out of Phase 1 scope |
| 受発注在庫管理システム | Order & inventory management system | Out of Phase 1 scope |
| 社宅費 | Company housing fee | Deduction item observed in the prototype |
| 財形貯蓄 | Asset-formation savings | Deduction item observed in the prototype |

## Appendix E — Assumption register

Every number in this proposal is either measured from the logs or assumed. The assumptions are listed here so they can be challenged individually.

| # | Assumption | Value used | Sensitivity | How to retire it |
|---|---|---|---|---|
| A-1 | Annual payroll-item record volume | 12k / 30k / 60k scenarios | Linear on all savings | Portal-side export of one full year |
| A-2 | Fully loaded hourly cost | ¥3,800/h | Linear on all currency figures | Finance provides the actual rate |
| A-3 | Manual transcription defect rate | 1.2% | Linear on the rework term | Sample audit of 500 historical records |
| A-4 | Rework cost per defect | 25 min | Linear on the rework term | Time three real correction cases |
| A-5 | Post-automation defect rate | 0.1% | Minor | Measure during the dual-run stage |
| A-6 | Exception rate | 4.0% | Linear on residual task 3 | Measure during the shadow stage |
| A-7 | Free-text note rate | 1.5% | Minor | Measure during the shadow stage |
| A-8 | Batch size | 1,000 records | Inverse on batch-level residual tasks | Set by the operating schedule |
| A-9 | Unattended machine time per record | 2.5 s | Affects scheduling, not savings | Measure in staging |
| A-10 | Records per payroll visit | 5.58 (measured, 240 ÷ 43) | Affects per-execution figures only | Already measured; re-confirm at month-end |

Measured quantities — 13.53 s per record, 307 clipboard events, 240 commits, 37.8% time share, 339 segments, 11 labels, 0.86 CV, and the benchmark scores — carry no assumption and can be recomputed from the repository at any time.
