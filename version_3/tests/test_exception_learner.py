"""
Unit tests for Exception Pattern Learning System

Tests verify:
1. Zero disruption to happy-path automation runs
2. Correct exception categorization
3. Pattern generation and summary export
4. Integration with automation_pipeline.py without side effects
"""

import json
import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from exception_learner import (
    ExceptionPatternLearner,
    ExceptionRecord,
    ExceptionCategory,
    create_mock_exception_log
)


class TestExceptionPatternLearner(unittest.TestCase):
    """Test suite for ExceptionPatternLearner class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.log_path = self.test_dir / "exception_log.jsonl"
        self.learner = ExceptionPatternLearner(exception_log_path=self.log_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_init_with_custom_path(self):
        """Test initialization with custom path"""
        custom_path = Path("custom/path/log.jsonl")
        learner = ExceptionPatternLearner(exception_log_path=custom_path)
        self.assertEqual(learner.exception_log_path, custom_path)
    
    def test_load_exceptions_empty_file(self):
        """Test loading exceptions when file doesn't exist"""
        exceptions = self.learner.load_exceptions()
        self.assertEqual(len(exceptions), 0)
    
    def test_load_exceptions_valid_file(self):
        """Test loading exceptions from valid file"""
        create_mock_exception_log(self.log_path, num_exceptions=5)
        exceptions = self.learner.load_exceptions()
        self.assertEqual(len(exceptions), 5)
    
    def test_categorize_ui_timeout(self):
        """Test UI timeout categorization"""
        record = ExceptionRecord(
            timestamp="2026-09-18T10:30:45Z",
            error_type="TimeoutError",
            selector="#btn-pi-ok",
            field_name=None,
            field_value=None,
            portal_response=None,
            alert_type=None,
            error_message="Timeout 30000ms exceeded waiting for selector",
            context={}
        )
        category = self.learner.categorize_exception(record)
        self.assertEqual(category, ExceptionCategory.UI_TIMEOUT)
    
    def test_categorize_missing_dom_element(self):
        """Test missing DOM element categorization"""
        record = ExceptionRecord(
            timestamp="2026-09-18T10:30:45Z",
            error_type="NoSuchElementError",
            selector="#btn-pi-register",
            field_name=None,
            field_value=None,
            portal_response=None,
            alert_type=None,
            error_message="Element not found in DOM",
            context={}
        )
        category = self.learner.categorize_exception(record)
        self.assertEqual(category, ExceptionCategory.MISSING_DOM_ELEMENT)
    
    def test_categorize_validation_rule_trigger(self):
        """Test validation rule trigger categorization"""
        record = ExceptionRecord(
            timestamp="2026-09-18T10:30:45Z",
            error_type="ValidationError",
            selector="input[name='amount']",
            field_name="amount",
            field_value="150000",
            portal_response="validation_failed",
            alert_type="amber",
            error_message="Amount format invalid: must be numeric",
            context={}
        )
        category = self.learner.categorize_exception(record)
        self.assertEqual(category, ExceptionCategory.VALIDATION_RULE_TRIGGER)
    
    def test_categorize_authentication_failure(self):
        """Test authentication failure categorization"""
        record = ExceptionRecord(
            timestamp="2026-09-18T10:30:45Z",
            error_type="AuthenticationError",
            selector=None,
            field_name=None,
            field_value=None,
            portal_response="401 Unauthorized",
            alert_type=None,
            error_message="Authentication failed: Invalid credentials",
            context={}
        )
        category = self.learner.categorize_exception(record)
        self.assertEqual(category, ExceptionCategory.AUTHENTICATION_FAILURE)
    
    def test_categorize_network_error(self):
        """Test network error categorization"""
        record = ExceptionRecord(
            timestamp="2026-09-18T10:30:45Z",
            error_type="NetworkError",
            selector=None,
            field_name=None,
            field_value=None,
            portal_response="503 Service Unavailable",
            alert_type=None,
            error_message="Network error: 503 Service Unavailable",
            context={}
        )
        category = self.learner.categorize_exception(record)
        self.assertEqual(category, ExceptionCategory.NETWORK_ERROR)
    
    def test_categorize_data_schema_mismatch(self):
        """Test data schema mismatch categorization"""
        record = ExceptionRecord(
            timestamp="2026-09-18T10:30:45Z",
            error_type="SchemaError",
            selector=None,
            field_name="employee_id",
            field_value=None,
            portal_response=None,
            alert_type=None,
            error_message="Required field 'employee_id' missing from input data",
            context={}
        )
        category = self.learner.categorize_exception(record)
        self.assertEqual(category, ExceptionCategory.DATA_SCHEMA_MISMATCH)
    
    def test_categorize_business_logic_violation(self):
        """Test business logic violation categorization"""
        record = ExceptionRecord(
            timestamp="2026-09-18T10:30:45Z",
            error_type="BusinessLogicError",
            selector=None,
            field_name="amount",
            field_value="75000",
            portal_response="policy_violation",
            alert_type="amber",
            error_message="Deduction amount violates company policy",
            context={}
        )
        category = self.learner.categorize_exception(record)
        self.assertEqual(category, ExceptionCategory.BUSINESS_LOGIC_VIOLATION)
    
    def test_categorize_unknown(self):
        """Test unknown exception categorization"""
        record = ExceptionRecord(
            timestamp="2026-09-18T10:30:45Z",
            error_type="UnknownError",
            selector=None,
            field_name=None,
            field_value=None,
            portal_response=None,
            alert_type=None,
            error_message="Some unknown error occurred",
            context={}
        )
        category = self.learner.categorize_exception(record)
        self.assertEqual(category, ExceptionCategory.UNKNOWN)
    
    def test_categorize_exceptions_multiple(self):
        """Test categorizing multiple exceptions"""
        create_mock_exception_log(self.log_path, num_exceptions=10)
        exceptions = self.learner.load_exceptions()
        categorized = self.learner.categorize_exceptions(exceptions)
        
        # Verify we have multiple categories
        self.assertGreater(len(categorized), 1)
        
        # Verify total count matches
        total_categorized = sum(len(records) for records in categorized.values())
        self.assertEqual(total_categorized, len(exceptions))
    
    def test_generate_patterns(self):
        """Test pattern generation from categorized exceptions"""
        create_mock_exception_log(self.log_path, num_exceptions=10)
        exceptions = self.learner.load_exceptions()
        categorized = self.learner.categorize_exceptions(exceptions)
        patterns = self.learner.generate_patterns(categorized)
        
        # Verify patterns were generated
        self.assertGreater(len(patterns), 0)
        
        # Verify pattern structure
        for pattern in patterns:
            self.assertIsInstance(pattern.category, ExceptionCategory)
            self.assertIsInstance(pattern.description, str)
            self.assertGreater(pattern.frequency, 0)
            self.assertIsInstance(pattern.examples, list)
            self.assertIsInstance(pattern.suggested_fixes, list)
            self.assertIsInstance(pattern.target_risks, list)
    
    def test_patterns_sorted_by_frequency(self):
        """Test that patterns are sorted by frequency (highest first)"""
        create_mock_exception_log(self.log_path, num_exceptions=10)
        self.learner.analyze_exceptions()
        
        frequencies = [pattern.frequency for pattern in self.learner.patterns]
        self.assertEqual(frequencies, sorted(frequencies, reverse=True))
    
    def test_export_summary(self):
        """Test exporting exception summary to JSON"""
        create_mock_exception_log(self.log_path, num_exceptions=5)
        self.learner.analyze_exceptions()
        
        output_path = self.test_dir / "exception_summary.json"
        result_path = self.learner.export_summary(output_path)
        
        # Verify file was created
        self.assertTrue(result_path.exists())
        
        # Verify JSON structure
        with open(result_path, 'r') as f:
            summary = json.load(f)
        
        self.assertIn('generated_at', summary)
        self.assertIn('total_patterns', summary)
        self.assertIn('patterns', summary)
        self.assertIsInstance(summary['patterns'], list)
    
    def test_generate_human_readable_summary(self):
        """Test generating human-readable summary"""
        create_mock_exception_log(self.log_path, num_exceptions=5)
        self.learner.analyze_exceptions()
        
        summary = self.learner.generate_human_readable_summary()
        
        # Verify summary structure
        self.assertIn("# Exception Pattern Analysis Summary", summary)
        self.assertIn("Total patterns identified:", summary)
        self.assertIn("## Risk", summary)
        self.assertIn("Suggested Fixes:", summary)
    
    def test_run_analysis_complete_pipeline(self):
        """Test complete analysis pipeline"""
        create_mock_exception_log(self.log_path, num_exceptions=5)
        
        results = self.learner.run_analysis()
        
        # Verify results structure
        self.assertIn('patterns_found', results)
        self.assertIn('summary_path', results)
        self.assertIn('human_summary_path', results)
        self.assertIn('human_summary', results)
        
        # Verify files were created
        self.assertTrue(Path(results['summary_path']).exists())
        self.assertTrue(Path(results['human_summary_path']).exists())
    
    def test_run_analysis_no_exceptions(self):
        """Test analysis when no exceptions exist"""
        results = self.learner.run_analysis()
        
        # Should handle empty case gracefully
        self.assertEqual(results['patterns_found'], 0)
        self.assertIn("No exception patterns detected", results['human_summary'])


class TestZeroDisruptionToHappyPath(unittest.TestCase):
    """Test that exception learner doesn't disrupt happy-path automation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.log_path = self.test_dir / "exception_log.jsonl"
    
    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_learner_does_not_modify_existing_files(self):
        """Test that learner doesn't modify existing automation files"""
        # Create a mock automation file
        automation_file = self.test_dir / "automation_pipeline.py"
        automation_file.write_text("# Mock automation pipeline")
        original_content = automation_file.read_text()
        
        # Run learner
        learner = ExceptionPatternLearner(exception_log_path=self.log_path)
        learner.run_analysis()
        
        # Verify automation file wasn't modified
        self.assertEqual(automation_file.read_text(), original_content)
    
    def test_learner_does_not_require_exception_log(self):
        """Test that learner works without exception log (no disruption)"""
        learner = ExceptionPatternLearner(exception_log_path=self.log_path)
        
        # Should not raise exception when log doesn't exist
        results = learner.run_analysis()
        self.assertEqual(results['patterns_found'], 0)
    
    def test_learner_passive_observer_only(self):
        """Test that learner is a passive observer only"""
        # Create mock exception log
        create_mock_exception_log(self.log_path, num_exceptions=3)
        original_log_content = self.log_path.read_text()
        
        # Run learner
        learner = ExceptionPatternLearner(exception_log_path=self.log_path)
        learner.run_analysis()
        
        # Verify log file wasn't modified
        self.assertEqual(self.log_path.read_text(), original_log_content)
    
    def test_learner_output_isolated_to_outputs_directory(self):
        """Test that learner only writes to designated outputs directory"""
        learner = ExceptionPatternLearner(exception_log_path=self.log_path)
        
        # Create mock exception log
        create_mock_exception_log(self.log_path, num_exceptions=3)
        
        # Run analysis
        results = learner.run_analysis()
        
        # Verify outputs are in expected locations
        summary_path = Path(results['summary_path'])
        human_summary_path = Path(results['human_summary_path'])
        
        # Both should be in outputs directory
        self.assertIn("outputs", str(summary_path))
        self.assertIn("outputs", str(human_summary_path))


class TestRiskTargeting(unittest.TestCase):
    """Test that patterns correctly target risks R-08 and R-11"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.log_path = self.test_dir / "exception_log.jsonl"
        self.learner = ExceptionPatternLearner(exception_log_path=self.log_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_data_schema_mismatch_targets_r08(self):
        """Test that data schema mismatches target risk R-08"""
        record = ExceptionRecord(
            timestamp="2026-09-18T10:30:45Z",
            error_type="SchemaError",
            selector=None,
            field_name="employee_id",
            field_value=None,
            portal_response=None,
            alert_type=None,
            error_message="Required field 'employee_id' missing",
            context={}
        )
        
        category = self.learner.categorize_exception(record)
        self.assertEqual(category, ExceptionCategory.DATA_SCHEMA_MISMATCH)
        
        # Verify risk mapping
        risks = self.learner.risk_mappings.get(category, [])
        self.assertIn("R-08", risks)
    
    def test_business_logic_violation_targets_r11(self):
        """Test that business logic violations target risk R-11"""
        record = ExceptionRecord(
            timestamp="2026-09-18T10:30:45Z",
            error_type="BusinessLogicError",
            selector=None,
            field_name="amount",
            field_value="150000",
            portal_response="policy_violation",
            alert_type="amber",
            error_message="Amount exceeds policy limit",
            context={}
        )
        
        category = self.learner.categorize_exception(record)
        self.assertEqual(category, ExceptionCategory.BUSINESS_LOGIC_VIOLATION)
        
        # Verify risk mapping
        risks = self.learner.risk_mappings.get(category, [])
        self.assertIn("R-11", risks)
    
    def test_validation_trigger_targets_r11(self):
        """Test that validation triggers target risk R-11"""
        record = ExceptionRecord(
            timestamp="2026-09-18T10:30:45Z",
            error_type="ValidationError",
            selector="input[name='amount']",
            field_name="amount",
            field_value="150000",
            portal_response="validation_failed",
            alert_type="amber",
            error_message="Amount format invalid: must be numeric",
            context={}
        )
        
        category = self.learner.categorize_exception(record)
        self.assertEqual(category, ExceptionCategory.VALIDATION_RULE_TRIGGER)
        
        # Verify risk mapping includes R-11
        risks = self.learner.risk_mappings.get(category, [])
        self.assertIn("R-11", risks)


class TestMockExceptionLogCreation(unittest.TestCase):
    """Test mock exception log creation utility"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.log_path = self.test_dir / "exception_log.jsonl"
    
    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_create_mock_exception_log(self):
        """Test creating mock exception log"""
        create_mock_exception_log(self.log_path, num_exceptions=5)
        
        # Verify file was created
        self.assertTrue(self.log_path.exists())
        
        # Verify content
        with open(self.log_path, 'r') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 5)
        
        # Verify each line is valid JSON
        for line in lines:
            data = json.loads(line)
            self.assertIn('timestamp', data)
            self.assertIn('error_message', data)
    
    def test_create_mock_exception_log_custom_count(self):
        """Test creating mock exception log with custom count"""
        create_mock_exception_log(self.log_path, num_exceptions=15)
        
        with open(self.log_path, 'r') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 15)


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios with automation pipeline"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.log_path = self.test_dir / "exception_log.jsonl"
    
    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_simulate_automation_pipeline_integration(self):
        """Test simulated integration with automation pipeline"""
        # Simulate automation pipeline creating exception log
        create_mock_exception_log(self.log_path, num_exceptions=8)
        
        # Exception learner processes the log
        learner = ExceptionPatternLearner(exception_log_path=self.log_path)
        results = learner.run_analysis()
        
        # Verify successful processing
        self.assertGreater(results['patterns_found'], 0)
        self.assertTrue(Path(results['summary_path']).exists())
        
        # Verify automation pipeline could continue running
        # (i.e. learner didn't block or modify anything)
        self.assertTrue(self.log_path.exists())
    
    def test_concurrent_analysis_safety(self):
        """Test that multiple analysis runs are safe"""
        create_mock_exception_log(self.log_path, num_exceptions=5)
        
        # Run analysis multiple times (simulating concurrent access)
        learner1 = ExceptionPatternLearner(exception_log_path=self.log_path)
        learner2 = ExceptionPatternLearner(exception_log_path=self.log_path)
        
        results1 = learner1.run_analysis()
        results2 = learner2.run_analysis()
        
        # Both should succeed
        self.assertEqual(results1['patterns_found'], results2['patterns_found'])


if __name__ == '__main__':
    unittest.main()