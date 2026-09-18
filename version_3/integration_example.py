"""
Integration Example: Exception Pattern Learning System with Automation Pipeline

This demonstrates how to hook the exception learner into automation_pipeline.py
without modifying the main execution loop.
"""

import json
from pathlib import Path
from datetime import datetime
import sys

# Import the exception learner
sys.path.insert(0, str(Path(__file__).parent))
from exception_learner import ExceptionPatternLearner, ExceptionRecord


class AutomationPipelineWithExceptionLogging:
    """
    Wrapper around automation_pipeline.py that adds exception logging
    without modifying the original execution logic.
    """
    
    def __init__(self, exception_log_path: Path = None):
        script_dir = Path(__file__).parent
        default_path = script_dir / "outputs" / "exception_log.jsonl"
        self.exception_log_path = exception_log_path or default_path
        self.exception_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_exception(self, error_type: str, error_message: str, selector: str = None, 
                     field_name: str = None, field_value: str = None, 
                     portal_response: str = None, alert_type: str = None, 
                     context: dict = None):
        """
        Log an exception to the exception log file.
        
        This method can be called from anywhere in the automation pipeline
        without disrupting the main execution flow.
        """
        exception_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "selector": selector,
            "field_name": field_name,
            "field_value": field_value,
            "portal_response": portal_response,
            "alert_type": alert_type,
            "error_message": error_message,
            "context": context or {}
        }
        
        with open(self.exception_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(exception_record) + '\n')
    
    def pipeline_with_logging(self):
        """
        Original automation pipeline logic with exception logging added.
        This demonstrates how to add logging without changing the core logic.
        """
        # 1. Simulate loading data
        print("Loading data from spreadsheet pipeline...")
        data = [
            {"employee_id": "EMP-001", "name": "Employee 1", "item": "Housing", "amount": 50000},
            {"employee_id": "EMP-002", "name": "Employee 2", "item": "Savings", "amount": 20000},
            {"employee_id": "EMP-003", "name": "Employee 3", "item": "Housing", "amount": 55000}
        ]
        print(f"Loaded {len(data)} rows. Commencing web injection...")

        # 2. Simulate Browser Automation with exception logging
        # (In real implementation, this would be the actual Playwright code)
        success_count = 0
        error_count = 0

        # 3. Batch processing loop
        for index, row in enumerate(data):
            emp_id = row['employee_id']
            item = row['item']
            amt = str(row['amount'])
            
            try:
                # Simulate some operations that might fail
                if index == 1:
                    # Simulate a timeout error
                    raise TimeoutError("Timeout 30000ms exceeded waiting for selector '#btn-pi-ok'")
                elif index == 2:
                    # Simulate a validation error
                    raise ValueError("Amount exceeds policy limit of 100000")
                
                # Simulate successful processing
                success_count += 1
                print(f"[SUCCESS] {emp_id} -> {item}: {amt} JPY")
            except Exception as e:
                # Log the exception with full context
                self.log_exception(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    selector="#btn-pi-ok" if index == 1 else None,
                    field_name="amount" if index == 2 else None,
                    field_value=amt if index == 2 else None,
                    portal_response="validation_failed" if index == 2 else None,
                    alert_type="amber" if index == 2 else None,
                    context={"action": "form_submit", "page": "/payroll-items", "row_index": index}
                )
                error_count += 1
                print(f"[ERROR] {emp_id} -> {item}: {str(e)}")
            
        print("\n=== Pipeline Report ===")
        print(f"Total processed: {len(data)}")
        print(f"Success: {success_count}")
        print(f"Errors: {error_count}")
        print("=======================")


def main():
    """
    Main function demonstrating the integration:
    1. Run automation pipeline with exception logging
    2. Run exception pattern learner on the logged exceptions
    3. Generate summary report
    """
    print("=== Integration Example: Automation Pipeline + Exception Learning ===\n")
    
    # Step 1: Run automation pipeline with exception logging
    print("Step 1: Running automation pipeline with exception logging...")
    pipeline = AutomationPipelineWithExceptionLogging()
    pipeline.pipeline_with_logging()
    
    # Step 2: Run exception pattern learner
    print("\nStep 2: Running exception pattern learner...")
    learner = ExceptionPatternLearner(exception_log_path=pipeline.exception_log_path)
    results = learner.run_analysis()
    
    # Step 3: Display results
    print(f"\nStep 3: Analysis complete: {results['patterns_found']} patterns found")
    print(f"Summary exported to: {results['summary_path']}")
    print(f"Human-readable report: {results['human_summary_path']}")
    
    # Display a snippet of the human-readable summary
    print("\n=== Exception Summary Report (First 20 lines) ===")
    summary_lines = results['human_summary'].split('\n')
    for line in summary_lines[:20]:
        print(line)
    print("...")
    print(f"\nFull report available at: {results['human_summary_path']}")


if __name__ == "__main__":
    main()