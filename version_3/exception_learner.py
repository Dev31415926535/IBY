"""
Exception Pattern Learning System (Version 3)
Implementation: Python module for categorizing automation exceptions and suggesting business logic fixes.

Purpose: 
- Hook cleanly into automation_pipeline.py without modifying main execution loop
- Read raw execution error logs and categorize into standard failure modes
- Export exception_summary.json with patterns and suggested fixes
- Auto-generate human-readable summary for risk section (R-08, R-11)

Design Principles:
- Zero disruption to happy-path automation runs
- Passive observation of exception logs
- Extensible pattern matching system
- Clear separation between detection and suggestion generation
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Callable, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class ExceptionCategory(Enum):
    """Standard failure modes for automation exceptions"""
    UI_TIMEOUT = "ui_timeout"
    MISSING_DOM_ELEMENT = "missing_dom_element"
    VALIDATION_RULE_TRIGGER = "validation_rule_trigger"
    AUTHENTICATION_FAILURE = "authentication_failure"
    NETWORK_ERROR = "network_error"
    DATA_SCHEMA_MISMATCH = "data_schema_mismatch"
    BUSINESS_LOGIC_VIOLATION = "business_logic_violation"
    UNKNOWN = "unknown"


@dataclass
class ExceptionRecord:
    """Structured representation of a single exception event"""
    timestamp: str
    error_type: str
    selector: Optional[str]
    field_name: Optional[str]
    field_value: Optional[str]
    portal_response: Optional[str]
    alert_type: Optional[str]
    error_message: str
    context: Dict[str, Any]


@dataclass
class ExceptionPattern:
    """Categorized exception pattern with frequency and suggested fixes"""
    category: ExceptionCategory
    description: str
    frequency: int
    examples: List[Dict[str, Any]]
    suggested_fixes: List[str]
    target_risks: List[str]


class ExceptionPatternLearner:
    """
    Main class for exception pattern learning and fix suggestion.
    
    Hooks into automation_pipeline.py by reading generated exception logs
    without modifying the main execution loop.
    """
    
    def __init__(self, exception_log_path: Optional[Path] = None):
        """
        Initialize the exception learner.
        
        Args:
            exception_log_path: Path to exception log file. If None, uses default path.
        """
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        default_path = script_dir / "outputs" / "exception_log.jsonl"
        self.exception_log_path = exception_log_path or default_path
        self.patterns: List[ExceptionPattern] = []
        
        # Define pattern matching rules
        self.pattern_rules = {
            ExceptionCategory.UI_TIMEOUT: self._is_ui_timeout,
            ExceptionCategory.MISSING_DOM_ELEMENT: self._is_missing_dom_element,
            ExceptionCategory.VALIDATION_RULE_TRIGGER: self._is_validation_rule_trigger,
            ExceptionCategory.AUTHENTICATION_FAILURE: self._is_authentication_failure,
            ExceptionCategory.NETWORK_ERROR: self._is_network_error,
            ExceptionCategory.DATA_SCHEMA_MISMATCH: self._is_data_schema_mismatch,
            ExceptionCategory.BUSINESS_LOGIC_VIOLATION: self._is_business_logic_violation,
        }
        
        # Define fix suggestions per category
        self.fix_suggestions = {
            ExceptionCategory.UI_TIMEOUT: [
                "Increase Playwright timeout for this selector",
                "Add retry logic with exponential backoff",
                "Check if element is conditionally rendered based on business rules",
                "Add explicit wait for specific network state before interaction"
            ],
            ExceptionCategory.MISSING_DOM_ELEMENT: [
                "Verify selector stability in staging environment",
                "Add fallback selector strategies (role, text, test ID)",
                "Check if page layout has changed or if element is dynamically loaded",
                "Add selector health check before main automation run"
            ],
            ExceptionCategory.VALIDATION_RULE_TRIGGER: [
                "Encode this business rule in pre-submission validation",
                "Add field value constraints to input schema",
                "Create exception handling for this specific validation scenario",
                "Document rule in operator training materials"
            ],
            ExceptionCategory.AUTHENTICATION_FAILURE: [
                "Verify service account credentials and permissions",
                "Check SSO token refresh logic",
                "Add authentication health check before batch processing",
                "Implement credential rotation schedule"
            ],
            ExceptionCategory.NETWORK_ERROR: [
                "Add retry logic with exponential backoff",
                "Implement circuit breaker pattern for repeated failures",
                "Verify network connectivity and firewall rules",
                "Add timeout configuration for network operations"
            ],
            ExceptionCategory.DATA_SCHEMA_MISMATCH: [
                "Enforce canonical template with version header",
                "Add schema validation before processing",
                "Reject batches with column signature mismatches",
                "Provide clear error messages for schema violations"
            ],
            ExceptionCategory.BUSINESS_LOGIC_VIOLATION: [
                "Document this business rule in automation specifications",
                "Add pre-flight validation for this condition",
                "Create human review workflow for edge cases",
                "Consider policy override process for exceptions"
            ],
        }
        
        # Map categories to target risks from FINAL_PROPOSAL.md
        self.risk_mappings = {
            ExceptionCategory.DATA_SCHEMA_MISMATCH: ["R-08"],
            ExceptionCategory.BUSINESS_LOGIC_VIOLATION: ["R-11"],
            ExceptionCategory.UI_TIMEOUT: ["R-03", "R-06"],
            ExceptionCategory.MISSING_DOM_ELEMENT: ["R-01", "R-02", "R-04"],
            ExceptionCategory.VALIDATION_RULE_TRIGGER: ["R-07", "R-11"],
            ExceptionCategory.AUTHENTICATION_FAILURE: ["R-15"],
            ExceptionCategory.NETWORK_ERROR: ["R-06"],
        }
    
    def _is_ui_timeout(self, record: ExceptionRecord) -> bool:
        """Check if exception is a UI timeout"""
        timeout_keywords = ["timeout", "timed out", "waiting for element", "exceeded timeout"]
        error_msg_lower = record.error_message.lower()
        return any(keyword in error_msg_lower for keyword in timeout_keywords)
    
    def _is_missing_dom_element(self, record: ExceptionRecord) -> bool:
        """Check if exception is due to missing DOM element"""
        missing_keywords = ["not found", "no element", "selector", "detached", "removed from dom"]
        error_msg_lower = record.error_message.lower()
        return any(keyword in error_msg_lower for keyword in missing_keywords)
    
    def _is_validation_rule_trigger(self, record: ExceptionRecord) -> bool:
        """Check if exception is a validation rule trigger"""
        # Only categorize as validation trigger if it's specifically about validation
        # but not about schema or business logic which have their own categories
        validation_keywords = ["validation", "invalid", "format", "constraint"]
        error_msg_lower = record.error_message.lower()
        has_validation = any(keyword in error_msg_lower for keyword in validation_keywords)
        has_alert = record.alert_type is not None
        
        # Exclude cases that should be categorized elsewhere
        if "required field" in error_msg_lower or "missing" in error_msg_lower:
            return False  # Let data_schema_mismatch catch this
        if "policy" in error_msg_lower or "limit" in error_msg_lower:
            return False  # Let business_logic_violation catch this
        if "authentication" in error_msg_lower or "unauthorized" in error_msg_lower:
            return False  # Let authentication_failure catch this
            
        return has_validation or has_alert
    
    def _is_authentication_failure(self, record: ExceptionRecord) -> bool:
        """Check if exception is authentication-related"""
        auth_keywords = ["authentication", "unauthorized", "forbidden", "login", "sso", "token"]
        error_msg_lower = record.error_message.lower()
        return any(keyword in error_msg_lower for keyword in auth_keywords)
    
    def _is_network_error(self, record: ExceptionRecord) -> bool:
        """Check if exception is network-related"""
        network_keywords = ["network", "connection", "econnrefused", "dns", "timeout", "502", "503", "504"]
        error_msg_lower = record.error_message.lower()
        return any(keyword in error_msg_lower for keyword in network_keywords)
    
    def _is_data_schema_mismatch(self, record: ExceptionRecord) -> bool:
        """Check if exception is due to data schema mismatch"""
        schema_keywords = ["column", "field", "schema", "mismatch", "missing field", "type error"]
        error_msg_lower = record.error_message.lower()
        has_field_issue = record.field_name is not None and "error" in error_msg_lower
        return any(keyword in error_msg_lower for keyword in schema_keywords) or has_field_issue
    
    def _is_business_logic_violation(self, record: ExceptionRecord) -> bool:
        """Check if exception is a business logic violation"""
        business_keywords = ["policy", "limit", "exceeds", "violation", "rule", "business"]
        error_msg_lower = record.error_message.lower()
        has_amount_limit = record.field_name == "amount" and "limit" in error_msg_lower
        return any(keyword in error_msg_lower for keyword in business_keywords) or has_amount_limit
    
    def load_exceptions(self) -> List[ExceptionRecord]:
        """
        Load exception records from log file.
        
        Returns:
            List of ExceptionRecord objects
        """
        exceptions = []
        
        if not self.exception_log_path.exists():
            return exceptions
        
        try:
            with open(self.exception_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        record = ExceptionRecord(
                            timestamp=data.get('timestamp', datetime.utcnow().isoformat()),
                            error_type=data.get('error_type', 'unknown'),
                            selector=data.get('selector'),
                            field_name=data.get('field_name'),
                            field_value=data.get('field_value'),
                            portal_response=data.get('portal_response'),
                            alert_type=data.get('alert_type'),
                            error_message=data.get('error_message', ''),
                            context=data.get('context', {})
                        )
                        exceptions.append(record)
                    except (json.JSONDecodeError, KeyError) as e:
                        # Skip malformed lines but continue processing
                        continue
        except OSError:
            # If file doesn't exist or can't be read, return empty list
            return []
        
        return exceptions
    
    def categorize_exception(self, record: ExceptionRecord) -> ExceptionCategory:
        """
        Categorize a single exception record using pattern matching rules.
        
        Args:
            record: ExceptionRecord to categorize
            
        Returns:
            ExceptionCategory for the record
        """
        for category, rule_func in self.pattern_rules.items():
            if rule_func(record):
                return category
        return ExceptionCategory.UNKNOWN
    
    def categorize_exceptions(self, exceptions: List[ExceptionRecord]) -> Dict[ExceptionCategory, List[ExceptionRecord]]:
        """
        Categorize multiple exception records.
        
        Args:
            exceptions: List of ExceptionRecord objects
            
        Returns:
            Dictionary mapping categories to their exception records
        """
        categorized = {}
        
        for record in exceptions:
            category = self.categorize_exception(record)
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(record)
        
        return categorized
    
    def generate_patterns(self, categorized: Dict[ExceptionCategory, List[ExceptionRecord]]) -> List[ExceptionPattern]:
        """
        Generate exception patterns from categorized exceptions.
        
        Args:
            categorized: Dictionary mapping categories to their exception records
            
        Returns:
            List of ExceptionPattern objects
        """
        patterns = []
        
        for category, records in categorized.items():
            if not records:
                continue
            
            # Generate description based on category and records
            description = self._generate_pattern_description(category, records)
            
            # Get suggested fixes for this category
            suggested_fixes = self.fix_suggestions.get(category, ["Review exception details"])
            
            # Get target risks
            target_risks = self.risk_mappings.get(category, [])
            
            # Create example records (limit to 3 for brevity)
            examples = []
            for record in records[:3]:
                example = {
                    'timestamp': record.timestamp,
                    'error_message': record.error_message,
                    'selector': record.selector,
                    'field_name': record.field_name,
                    'portal_response': record.portal_response
                }
                examples.append(example)
            
            pattern = ExceptionPattern(
                category=category,
                description=description,
                frequency=len(records),
                examples=examples,
                suggested_fixes=suggested_fixes,
                target_risks=target_risks
            )
            
            patterns.append(pattern)
        
        # Sort by frequency (most common first)
        patterns.sort(key=lambda p: p.frequency, reverse=True)
        
        return patterns
    
    def _generate_pattern_description(self, category: ExceptionCategory, records: List[ExceptionRecord]) -> str:
        """Generate a human-readable description for a pattern"""
        if category == ExceptionCategory.UI_TIMEOUT:
            return f"UI timeout errors when waiting for DOM elements ({len(records)} occurrences)"
        elif category == ExceptionCategory.MISSING_DOM_ELEMENT:
            return f"Missing DOM elements or selector failures ({len(records)} occurrences)"
        elif category == ExceptionCategory.VALIDATION_RULE_TRIGGER:
            return f"Validation rule triggers from portal or business logic ({len(records)} occurrences)"
        elif category == ExceptionCategory.AUTHENTICATION_FAILURE:
            return f"Authentication or SSO-related failures ({len(records)} occurrences)"
        elif category == ExceptionCategory.NETWORK_ERROR:
            return f"Network connectivity or HTTP errors ({len(records)} occurrences)"
        elif category == ExceptionCategory.DATA_SCHEMA_MISMATCH:
            return f"Data schema or field mapping mismatches ({len(records)} occurrences)"
        elif category == ExceptionCategory.BUSINESS_LOGIC_VIOLATION:
            return f"Business logic or policy violations ({len(records)} occurrences)"
        else:
            return f"Uncategorized exceptions ({len(records)} occurrences)"
    
    def analyze_exceptions(self) -> List[ExceptionPattern]:
        """
        Main analysis pipeline: load, categorize, and generate patterns.
        
        Returns:
            List of ExceptionPattern objects
        """
        exceptions = self.load_exceptions()
        if not exceptions:
            return []
        
        categorized = self.categorize_exceptions(exceptions)
        patterns = self.generate_patterns(categorized)
        
        self.patterns = patterns
        return patterns
    
    def export_summary(self, output_path: Optional[Path] = None) -> Path:
        """
        Export exception summary to JSON file.
        
        Args:
            output_path: Path for output file. If None, uses default path.
            
        Returns:
            Path to the exported file
        """
        if output_path is None:
            script_dir = Path(__file__).parent
            output_path = script_dir / "outputs" / "exception_summary.json"
        
        # Convert patterns to serializable format
        summary_data = {
            'generated_at': datetime.utcnow().isoformat(),
            'total_patterns': len(self.patterns),
            'patterns': []
        }
        
        for pattern in self.patterns:
            pattern_dict = {
                'category': pattern.category.value,
                'description': pattern.description,
                'frequency': pattern.frequency,
                'examples': pattern.examples,
                'suggested_fixes': pattern.suggested_fixes,
                'target_risks': pattern.target_risks
            }
            summary_data['patterns'].append(pattern_dict)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def generate_human_readable_summary(self) -> str:
        """
        Generate human-readable summary for final report risk section.
        
        Returns:
            Formatted string suitable for pasting into risk documentation
        """
        if not self.patterns:
            return "No exception patterns detected in current logs."
        
        summary_lines = [
            "# Exception Pattern Analysis Summary",
            f"Generated: {datetime.utcnow().isoformat()}",
            f"Total patterns identified: {len(self.patterns)}",
            ""
        ]
        
        # Group by target risks
        risk_grouped = {}
        for pattern in self.patterns:
            for risk in pattern.target_risks:
                if risk not in risk_grouped:
                    risk_grouped[risk] = []
                risk_grouped[risk].append(pattern)
        
        # Generate risk-specific sections
        for risk, patterns in sorted(risk_grouped.items()):
            summary_lines.append(f"## Risk {risk} - Exception Patterns")
            summary_lines.append("")
            
            for pattern in patterns:
                summary_lines.append(f"### {pattern.description}")
                summary_lines.append(f"**Frequency:** {pattern.frequency} occurrences")
                summary_lines.append(f"**Category:** {pattern.category.value}")
                summary_lines.append("")
                summary_lines.append("**Suggested Fixes:**")
                for fix in pattern.suggested_fixes:
                    summary_lines.append(f"- {fix}")
                summary_lines.append("")
        
        # Add overall recommendations
        summary_lines.append("## Overall Recommendations")
        summary_lines.append("")
        summary_lines.append("Based on the exception patterns identified, the following actions are recommended:")
        summary_lines.append("")
        
        if risk_grouped:
            summary_lines.append("1. **Immediate Priority:** Address patterns affecting high-frequency automation paths")
            summary_lines.append("2. **Schema Validation:** Implement strict input validation to prevent data schema mismatches")
            summary_lines.append("3. **Selector Stability:** Add selector health checks before production runs")
            summary_lines.append("4. **Business Rule Encoding:** Document and encode recurring business logic violations")
            summary_lines.append("5. **Monitoring:** Implement continuous exception pattern monitoring")
        
        return "\n".join(summary_lines)
    
    def run_analysis(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Run complete analysis pipeline and export results.
        
        Args:
            output_path: Path for exception summary JSON output
            
        Returns:
            Dictionary with analysis results
        """
        patterns = self.analyze_exceptions()
        summary_path = self.export_summary(output_path)
        human_summary = self.generate_human_readable_summary()
        
        # Save human-readable summary
        human_summary_path = summary_path.parent / "exception_summary_report.md"
        with open(human_summary_path, 'w', encoding='utf-8') as f:
            f.write(human_summary)
        
        return {
            'patterns_found': len(patterns),
            'summary_path': str(summary_path),
            'human_summary_path': str(human_summary_path),
            'human_summary': human_summary
        }


def create_mock_exception_log(log_path: Path, num_exceptions: int = 10) -> None:
    """
    Create a mock exception log for testing purposes.
    
    Args:
        log_path: Path where to create the mock log
        num_exceptions: Number of mock exceptions to generate
    """
    base_mock_exceptions = [
        {
            "timestamp": "2026-09-18T10:30:45Z",
            "error_type": "TimeoutError",
            "selector": "#btn-pi-ok",
            "field_name": None,
            "field_value": None,
            "portal_response": None,
            "alert_type": None,
            "error_message": "Timeout 30000ms exceeded waiting for selector '#btn-pi-ok'",
            "context": {"action": "click", "page": "/payroll-items"}
        },
        {
            "timestamp": "2026-09-18T10:31:12Z",
            "error_type": "NoSuchElementError",
            "selector": "#btn-pi-register",
            "field_name": None,
            "field_value": None,
            "portal_response": None,
            "alert_type": None,
            "error_message": "Element #btn-pi-register not found in DOM",
            "context": {"action": "click", "page": "/payroll-items"}
        },
        {
            "timestamp": "2026-09-18T10:32:45Z",
            "error_type": "ValidationError",
            "selector": "input[name='amount']",
            "field_name": "amount",
            "field_value": "150000",
            "portal_response": "validation_failed",
            "alert_type": "amber",
            "error_message": "Amount format invalid: must be numeric",
            "context": {"action": "form_submit", "page": "/payroll-items"}
        },
        {
            "timestamp": "2026-09-18T10:33:20Z",
            "error_type": "SchemaError",
            "selector": None,
            "field_name": "employee_id",
            "field_value": None,
            "portal_response": None,
            "alert_type": None,
            "error_message": "Required field 'employee_id' missing from input data",
            "context": {"action": "validation", "page": "data_ingestion"}
        },
        {
            "timestamp": "2026-09-18T10:34:10Z",
            "error_type": "NetworkError",
            "selector": None,
            "field_name": None,
            "field_value": None,
            "portal_response": "503 Service Unavailable",
            "alert_type": None,
            "error_message": "Network error: 503 Service Unavailable",
            "context": {"action": "navigation", "page": "/payroll-items"}
        },
        {
            "timestamp": "2026-09-18T10:35:30Z",
            "error_type": "AuthenticationError",
            "selector": "input[name='uid']",
            "field_name": None,
            "field_value": None,
            "portal_response": "401 Unauthorized",
            "alert_type": None,
            "error_message": "Authentication failed: Invalid credentials",
            "context": {"action": "login", "page": "/sso-mock.html"}
        },
        {
            "timestamp": "2026-09-18T10:36:15Z",
            "error_type": "TimeoutError",
            "selector": "#pi-note",
            "field_name": None,
            "field_value": None,
            "portal_response": None,
            "alert_type": None,
            "error_message": "Timeout 20000ms exceeded waiting for element to be visible",
            "context": {"action": "fill", "page": "/payroll-items"}
        },
        {
            "timestamp": "2026-09-18T10:37:00Z",
            "error_type": "BusinessLogicError",
            "selector": None,
            "field_name": "amount",
            "field_value": "75000",
            "portal_response": "policy_violation",
            "alert_type": "amber",
            "error_message": "Deduction amount violates company policy for this employee type",
            "context": {"action": "validation", "page": "/payroll-items"}
        },
        {
            "timestamp": "2026-09-18T10:38:45Z",
            "error_type": "SchemaError",
            "selector": None,
            "field_name": "item_name",
            "field_value": None,
            "portal_response": None,
            "alert_type": None,
            "error_message": "Column 'item_name' not found in input spreadsheet",
            "context": {"action": "data_ingestion", "page": "pipeline"}
        },
        {
            "timestamp": "2026-09-18T10:39:30Z",
            "error_type": "ValidationError",
            "selector": "input[name='employee_name']",
            "field_name": "employee_name",
            "field_value": "INVALID_ID",
            "portal_response": "validation_failed",
            "alert_type": "amber",
            "error_message": "Employee name format invalid: must contain valid characters",
            "context": {"action": "form_submit", "page": "/payroll-items"}
        },
        {
            "timestamp": "2026-09-18T10:40:00Z",
            "error_type": "ValidationError",
            "selector": "input[name='email']",
            "field_name": "email",
            "field_value": "invalid-email",
            "portal_response": "validation_failed",
            "alert_type": "amber",
            "error_message": "Email format invalid: must contain @ symbol",
            "context": {"action": "form_submit", "page": "/payroll-items"}
        },
        {
            "timestamp": "2026-09-18T10:40:30Z",
            "error_type": "BusinessLogicError",
            "selector": None,
            "field_name": "deduction_type",
            "field_value": "forbidden_type",
            "portal_response": "policy_violation",
            "alert_type": "amber",
            "error_message": "Deduction type not allowed for this employee category",
            "context": {"action": "validation", "page": "/payroll-items"}
        }
    ]
    
    # Cycle through the base exceptions if we need more than available
    expanded_exceptions = []
    for i in range(num_exceptions):
        expanded_exceptions.append(base_mock_exceptions[i % len(base_mock_exceptions)])
    
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        for exception in expanded_exceptions:
            f.write(json.dumps(exception) + '\n')


if __name__ == "__main__":
    # Example usage
    learner = ExceptionPatternLearner()
    
    # Create mock exception log for demonstration
    create_mock_exception_log(learner.exception_log_path, num_exceptions=10)
    
    # Run analysis
    results = learner.run_analysis()
    
    print(f"Analysis complete: {results['patterns_found']} patterns found")
    print(f"Summary exported to: {results['summary_path']}")
    print(f"Human-readable report: {results['human_summary_path']}")
    print("\n" + results['human_summary'])