# Project Documentation

## Architectural Decisions
- **Modularity of Analysis Scripts**: We separated the analysis into independent scripts (`inventory.py`, `route_actions.py`, `parse_gt.py`, `segmenter.py`). This allowed for targeted extraction of insights (e.g., separating raw event tracking from ground truth validation) and kept scripts easy to maintain.
- **Rule-based Segmentation**: For the segmentation baseline, we adopted a rule-based algorithm identifying contiguous sequences of work bounded by specific routes and window titles. While simple, it proved highly effective for detecting well-defined tasks like `/payroll-items` or `/leave-applications` without requiring a complex ML model.
- **Python Playwright for Prototype**: We elected to use `playwright` for the automation prototype instead of `requests` or `selenium` because Playwright natively supports modern asynchronous browser interactions and perfectly mirrors the UI interactions tracked in the dataset (like `btn-pi-register`).

## Pivot Points
- **Initial Assumption vs. Reality**: We initially assumed that the process names in Dataset B would exactly match Dataset A. We quickly discovered that while the web routes (e.g., `/payroll-items`) remained the same, the window titles and contextual applications were slightly different (e.g., using `Microsoft Edge` instead of `Chrome`). The `segmenter.py` script was updated to capture both Dataset A and B patterns.
- **Data Availability**: The raw logs exhibited many `None` values for expected fields (e.g., `payload` and `context`). We had to pivot our parsing logic in `route_actions.py` to robustly handle missing dictionary properties, preventing crashes and allowing successful extraction.

## Failed Experiments
- **Relying Solely on Text Inputs**: We initially considered relying on `text_input_complete` to define the start and end of a process. However, the data revealed that `text_input_complete` events were highly unreliable. We abandoned this and pivoted to using specific element clicks (like `btn-pi-ok`) and URL route changes.
- **Pandas Dependency in Prototype**: The prototype originally used `pandas` to manage data inputs, which introduced unnecessary bulk and a dependency failure. We ultimately simplified the prototype to use standard dictionaries and eventually integrated `matplotlib` to demonstrate ROI dynamically instead of relying purely on heavy data frames.
