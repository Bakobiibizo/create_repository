"""
Tests for the Environment Manager utility.

This module contains tests for the EnvironmentManager class and related functionality.
"""

import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utilities.environment_manager import EnvironmentManager, EnvironmentType, get_environment_manager
from src.utilities.exceptions import (
    EnvironmentVariableNotFoundError,
    EnvironmentVariableValidationError
)
from src.utilities.singleton import Singleton


class TestEnvironmentManager(unittest.TestCase):
    """Tests for the EnvironmentManager class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Clear the singleton instance before each test
        Singleton.clear_instance(EnvironmentManager)
        
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create a test .env file
        self.env_file = self.test_dir / ".env"
        with open(self.env_file, "w") as f:
            f.write("TEST_VAR=test_value\n")
            f.write("TEST_INT=42\n")
            f.write("TEST_FLOAT=3.14\n")
            f.write("TEST_BOOL=true\n")
            f.write("TEST_LIST=item1,item2,item3\n")
            f.write("TEST_DICT={\"key\": \"value\"}\n")
        
        # Create a test environment-specific .env file
        self.env_dev_file = self.test_dir / ".env.development"
        with open(self.env_dev_file, "w") as f:
            f.write("ENV_SPECIFIC=development\n")
        
        # Patch the path manager to return our test directory
        self.path_manager_patcher = patch("src.utilities.path_manager.get_path_manager")
        self.mock_path_manager = self.path_manager_patcher.start()
        
        mock_path_manager_instance = MagicMock()
        mock_path_manager_instance.resolve_path.side_effect = lambda path: {
            "project_root": self.test_dir,
            "config_dir": self.test_dir,
        }.get(path, Path(path))
        
        self.mock_path_manager.return_value = mock_path_manager_instance
    
    def tearDown(self):
        """Clean up the test environment."""
        self.path_manager_patcher.stop()
        self.temp_dir.cleanup()
    
    def test_singleton(self):
        """Test that EnvironmentManager is a singleton."""
        em1 = EnvironmentManager()
        em2 = EnvironmentManager()
        self.assertIs(em1, em2)
        
        # Test the get_environment_manager function
        em3 = get_environment_manager()
        self.assertIs(em1, em3)
    
    @patch.dict(os.environ, {"ENV": "development"}, clear=True)
    def test_environment_type(self):
        """Test environment type detection."""
        em = EnvironmentManager()
        self.assertEqual(em.get_env_type(), EnvironmentType.DEVELOPMENT)
        self.assertTrue(em.is_development())
        self.assertFalse(em.is_testing())
        self.assertFalse(em.is_production())
        
        # Test with different environment types
        with patch.dict(os.environ, {"ENV": "testing"}, clear=True):
            Singleton.clear_instance(EnvironmentManager)
            em = EnvironmentManager()
            self.assertEqual(em.get_env_type(), EnvironmentType.TESTING)
            self.assertFalse(em.is_development())
            self.assertTrue(em.is_testing())
            self.assertFalse(em.is_production())
        
        with patch.dict(os.environ, {"ENV": "production"}, clear=True):
            Singleton.clear_instance(EnvironmentManager)
            em = EnvironmentManager()
            self.assertEqual(em.get_env_type(), EnvironmentType.PRODUCTION)
            self.assertFalse(em.is_development())
            self.assertFalse(em.is_testing())
            self.assertTrue(em.is_production())
    
    @patch.dict(os.environ, {}, clear=True)
    def test_register_and_get_var(self):
        """Test registering and getting environment variables."""
        em = EnvironmentManager()
        
        # Register a variable with a default value
        em.register_var("TEST_VAR", default="default_value")
        
        # Get the variable (should return the default)
        value = em.get_var("TEST_VAR")
        self.assertEqual(value, "default_value")
        
        # Set the variable
        em.set_var("TEST_VAR", "new_value")
        
        # Get the variable (should return the new value)
        value = em.get_var("TEST_VAR")
        self.assertEqual(value, "new_value")
        
        # Register a required variable
        with self.assertRaises(EnvironmentVariableValidationError):
            em.register_var("REQUIRED_VAR", required=True)
        
        # Register a variable with a pattern
        em.register_var("PATTERN_VAR", pattern=r"^[a-z]+$")
        
        # Set a valid value
        em.set_var("PATTERN_VAR", "valid")
        
        # Set an invalid value
        with self.assertRaises(EnvironmentVariableValidationError):
            em.set_var("PATTERN_VAR", "INVALID")
        
        # Register a variable with options
        em.register_var("OPTION_VAR", options=["option1", "option2"])
        
        # Set a valid value
        em.set_var("OPTION_VAR", "option1")
        
        # Set an invalid value
        with self.assertRaises(EnvironmentVariableValidationError):
            em.set_var("OPTION_VAR", "invalid")
    
    @patch.dict(os.environ, {"TEST_VAR": "test_value"}, clear=True)
    def test_has_var(self):
        """Test checking if a variable exists."""
        em = EnvironmentManager()
        
        # Check if a variable exists
        self.assertTrue(em.has_var("TEST_VAR"))
        self.assertFalse(em.has_var("NONEXISTENT_VAR"))
    
    @patch.dict(os.environ, {
        "TEST_INT": "42",
        "TEST_FLOAT": "3.14",
        "TEST_BOOL_TRUE": "true",
        "TEST_BOOL_FALSE": "false",
        "TEST_LIST": "item1,item2,item3",
        "TEST_DICT": '{"key": "value"}'
    }, clear=True)
    def test_get_var_as_type(self):
        """Test getting variables as different types."""
        em = EnvironmentManager()
        
        # Test get_var_as_int
        value = em.get_var_as_int("TEST_INT")
        self.assertEqual(value, 42)
        self.assertIsInstance(value, int)
        
        # Test get_var_as_float
        value = em.get_var_as_float("TEST_FLOAT")
        self.assertEqual(value, 3.14)
        self.assertIsInstance(value, float)
        
        # Test get_var_as_bool
        value = em.get_var_as_bool("TEST_BOOL_TRUE")
        self.assertEqual(value, True)
        self.assertIsInstance(value, bool)
        
        value = em.get_var_as_bool("TEST_BOOL_FALSE")
        self.assertEqual(value, False)
        self.assertIsInstance(value, bool)
        
        # Test get_var_as_list
        value = em.get_var_as_list("TEST_LIST")
        self.assertEqual(value, ["item1", "item2", "item3"])
        self.assertIsInstance(value, list)
        
        # Test get_var_as_dict
        value = em.get_var_as_dict("TEST_DICT")
        self.assertEqual(value, {"key": "value"})
        self.assertIsInstance(value, dict)
        
        # Test with invalid values
        with patch.dict(os.environ, {"INVALID_INT": "not_an_int"}, clear=False):
            with self.assertRaises(EnvironmentVariableValidationError):
                em.get_var_as_int("INVALID_INT")
        
        with patch.dict(os.environ, {"INVALID_FLOAT": "not_a_float"}, clear=False):
            with self.assertRaises(EnvironmentVariableValidationError):
                em.get_var_as_float("INVALID_FLOAT")
        
        with patch.dict(os.environ, {"INVALID_BOOL": "not_a_bool"}, clear=False):
            with self.assertRaises(EnvironmentVariableValidationError):
                em.get_var_as_bool("INVALID_BOOL")
        
        with patch.dict(os.environ, {"INVALID_DICT": "not_a_dict"}, clear=False):
            with self.assertRaises(EnvironmentVariableValidationError):
                em.get_var_as_dict("INVALID_DICT")
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_var_with_default(self):
        """Test getting variables with default values."""
        em = EnvironmentManager()
        
        # Test get_var with default
        value = em.get_var("NONEXISTENT_VAR", default="default_value")
        self.assertEqual(value, "default_value")
        
        # Test get_var_as_int with default
        value = em.get_var_as_int("NONEXISTENT_VAR", default=42)
        self.assertEqual(value, 42)
        
        # Test get_var_as_float with default
        value = em.get_var_as_float("NONEXISTENT_VAR", default=3.14)
        self.assertEqual(value, 3.14)
        
        # Test get_var_as_bool with default
        value = em.get_var_as_bool("NONEXISTENT_VAR", default=True)
        self.assertEqual(value, True)
        
        # Test get_var_as_list with default
        value = em.get_var_as_list("NONEXISTENT_VAR", default=["default"])
        self.assertEqual(value, ["default"])
        
        # Test get_var_as_dict with default
        value = em.get_var_as_dict("NONEXISTENT_VAR", default={"default": "value"})
        self.assertEqual(value, {"default": "value"})
        
        # Test get_var without default
        with self.assertRaises(EnvironmentVariableNotFoundError):
            em.get_var("NONEXISTENT_VAR")
    
    @patch.dict(os.environ, {}, clear=True)
    def test_loaded_files(self):
        """Test that .env files are loaded."""
        em = EnvironmentManager()
        
        # Check that the .env file was loaded
        loaded_files = em.get_loaded_files()
        self.assertIn(str(self.env_file), loaded_files)
        
        # Check that environment-specific .env files are loaded
        with patch.dict(os.environ, {"ENV": "development"}, clear=True):
            Singleton.clear_instance(EnvironmentManager)
            em = EnvironmentManager()
            loaded_files = em.get_loaded_files()
            self.assertIn(str(self.env_file), loaded_files)
            self.assertIn(str(self.env_dev_file), loaded_files)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_registered_vars(self):
        """Test getting registered variables."""
        em = EnvironmentManager()
        
        # Register some variables
        em.register_var("VAR1", default="value1", description="Description 1")
        em.register_var("VAR2", default="value2", description="Description 2")
        
        # Get registered variables
        registered = em.get_registered_vars()
        self.assertIn("VAR1", registered)
        self.assertIn("VAR2", registered)
        self.assertEqual(registered["VAR1"]["default"], "value1")
        self.assertEqual(registered["VAR1"]["description"], "Description 1")
        self.assertEqual(registered["VAR2"]["default"], "value2")
        self.assertEqual(registered["VAR2"]["description"], "Description 2")


if __name__ == "__main__":
    unittest.main()
