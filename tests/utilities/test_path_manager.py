"""
Tests for the Path Manager utility.

This module contains tests for the PathManager class and related functionality.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.utilities.path_manager import PathManager, get_path_manager
from src.utilities.exceptions import PathNotFoundError, PathResolutionError, PathValidationError
from src.utilities.singleton import Singleton


class TestPathManager(unittest.TestCase):
    """Tests for the PathManager class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Clear the singleton instance before each test
        Singleton.clear_instance(PathManager)
        
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create some test directories and files
        self.config_dir = self.test_dir / "config"
        self.data_dir = self.test_dir / "data"
        self.logs_dir = self.test_dir / "logs"
        
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Create a test file
        self.test_file = self.config_dir / "test.txt"
        with open(self.test_file, "w") as f:
            f.write("Test content")
    
    def tearDown(self):
        """Clean up the test environment."""
        self.temp_dir.cleanup()
    
    def test_singleton(self):
        """Test that PathManager is a singleton."""
        pm1 = PathManager()
        pm2 = PathManager()
        self.assertIs(pm1, pm2)
        
        # Test the get_path_manager function
        pm3 = get_path_manager()
        self.assertIs(pm1, pm3)
    
    def test_register_and_resolve_path(self):
        """Test registering and resolving paths."""
        pm = PathManager()
        
        # Register a test path
        pm.register_path("test_dir", str(self.test_dir))
        
        # Resolve the path
        resolved = pm.resolve_path("test_dir")
        self.assertEqual(resolved, self.test_dir)
        
        # Register a path with a variable
        pm.register_path("config_dir", "${test_dir}/config")
        
        # Resolve the path with the variable
        resolved = pm.resolve_path("config_dir")
        self.assertEqual(resolved, self.config_dir)
        
        # Test resolving a non-registered path
        resolved = pm.resolve_path(str(self.data_dir))
        self.assertEqual(resolved, self.data_dir)
    
    def test_path_validation(self):
        """Test path validation."""
        pm = PathManager()
        
        # Register test paths
        pm.register_path("test_dir", str(self.test_dir))
        pm.register_path("test_file", str(self.test_file))
        pm.register_path("nonexistent", str(self.test_dir / "nonexistent"))
        
        # Test validating an existing path
        resolved = pm.resolve_path("test_dir", validate=True)
        self.assertEqual(resolved, self.test_dir)
        
        # Test validating a non-existent path
        with self.assertRaises(PathValidationError):
            pm.resolve_path("nonexistent", validate=True)
    
    def test_resolve_directory(self):
        """Test resolving directories."""
        pm = PathManager()
        
        # Register test paths
        pm.register_path("test_dir", str(self.test_dir))
        pm.register_path("test_file", str(self.test_file))
        pm.register_path("nonexistent", str(self.test_dir / "nonexistent"))
        
        # Test resolving an existing directory
        resolved = pm.resolve_directory("test_dir")
        self.assertEqual(resolved, self.test_dir)
        
        # Test resolving a file as a directory
        with self.assertRaises(PathValidationError):
            pm.resolve_directory("test_file")
        
        # Test resolving a non-existent directory
        with self.assertRaises(PathValidationError):
            pm.resolve_directory("nonexistent")
        
        # Test creating a non-existent directory
        resolved = pm.resolve_directory("nonexistent", create=True)
        self.assertEqual(resolved, self.test_dir / "nonexistent")
        self.assertTrue(resolved.exists())
        self.assertTrue(resolved.is_dir())
    
    def test_resolve_file(self):
        """Test resolving files."""
        pm = PathManager()
        
        # Register test paths
        pm.register_path("test_dir", str(self.test_dir))
        pm.register_path("test_file", str(self.test_file))
        pm.register_path("nonexistent_file", str(self.test_dir / "nonexistent.txt"))
        
        # Test resolving an existing file
        resolved = pm.resolve_file("test_file")
        self.assertEqual(resolved, self.test_file)
        
        # Test resolving a directory as a file
        with self.assertRaises(PathValidationError):
            pm.resolve_file("test_dir")
        
        # Test resolving a non-existent file
        resolved = pm.resolve_file("nonexistent_file")
        self.assertEqual(resolved, self.test_dir / "nonexistent.txt")
        self.assertFalse(resolved.exists())
    
    def test_join_path(self):
        """Test joining paths."""
        pm = PathManager()
        
        # Register a test path
        pm.register_path("test_dir", str(self.test_dir))
        
        # Join a registered path with additional parts
        joined = pm.join_path("test_dir", "subdir", "file.txt")
        self.assertEqual(joined, self.test_dir / "subdir" / "file.txt")
        
        # Join a Path object with additional parts
        joined = pm.join_path(self.test_dir, "subdir", "file.txt")
        self.assertEqual(joined, self.test_dir / "subdir" / "file.txt")
    
    def test_find_file(self):
        """Test finding files."""
        pm = PathManager()
        
        # Create some test files
        test_file1 = self.config_dir / "test1.txt"
        test_file2 = self.data_dir / "test2.txt"
        test_file3 = self.data_dir / "subdir" / "test3.txt"
        
        os.makedirs(self.data_dir / "subdir", exist_ok=True)
        
        with open(test_file1, "w") as f:
            f.write("Test content 1")
        with open(test_file2, "w") as f:
            f.write("Test content 2")
        with open(test_file3, "w") as f:
            f.write("Test content 3")
        
        # Register test paths
        pm.register_path("test_dir", str(self.test_dir))
        pm.register_path("config_dir", str(self.config_dir))
        pm.register_path("data_dir", str(self.data_dir))
        
        # Find a file in the first search path
        found = pm.find_file("test1.txt", ["config_dir", "data_dir"])
        self.assertEqual(found, test_file1)
        
        # Find a file in the second search path
        found = pm.find_file("test2.txt", ["config_dir", "data_dir"])
        self.assertEqual(found, test_file2)
        
        # Find a file recursively
        found = pm.find_file("test3.txt", ["config_dir", "data_dir"], recursive=True)
        self.assertEqual(found, test_file3)
        
        # Try to find a non-existent file
        found = pm.find_file("nonexistent.txt", ["config_dir", "data_dir"])
        self.assertIsNone(found)
    
    def test_find_directory(self):
        """Test finding directories."""
        pm = PathManager()
        
        # Create some test directories
        test_dir1 = self.config_dir / "subdir1"
        test_dir2 = self.data_dir / "subdir2"
        test_dir3 = self.data_dir / "subdir2" / "subdir3"
        
        os.makedirs(test_dir1, exist_ok=True)
        os.makedirs(test_dir2, exist_ok=True)
        os.makedirs(test_dir3, exist_ok=True)
        
        # Register test paths
        pm.register_path("test_dir", str(self.test_dir))
        pm.register_path("config_dir", str(self.config_dir))
        pm.register_path("data_dir", str(self.data_dir))
        
        # Find a directory in the first search path
        found = pm.find_directory("subdir1", ["config_dir", "data_dir"])
        self.assertEqual(found, test_dir1)
        
        # Find a directory in the second search path
        found = pm.find_directory("subdir2", ["config_dir", "data_dir"])
        self.assertEqual(found, test_dir2)
        
        # Find a directory recursively
        found = pm.find_directory("subdir3", ["config_dir", "data_dir"], recursive=True)
        self.assertEqual(found, test_dir3)
        
        # Try to find a non-existent directory
        found = pm.find_directory("nonexistent", ["config_dir", "data_dir"])
        self.assertIsNone(found)
    
    def test_normalize_path(self):
        """Test normalizing paths."""
        pm = PathManager()
        
        # Register a test path
        pm.register_path("test_dir", str(self.test_dir))
        
        # Normalize a registered path
        normalized = pm.normalize_path("test_dir")
        self.assertEqual(normalized, self.test_dir)
        
        # Normalize a string path
        normalized = pm.normalize_path(str(self.test_dir))
        self.assertEqual(normalized, self.test_dir)
        
        # Normalize a Path object
        normalized = pm.normalize_path(self.test_dir)
        self.assertEqual(normalized, self.test_dir)
        
        # Normalize a path with variables
        pm.register_path("var_path", "${test_dir}/subdir")
        normalized = pm.normalize_path("${test_dir}/subdir")
        self.assertEqual(normalized, self.test_dir / "subdir")
    
    @patch.dict(os.environ, {"TEST_ENV_VAR": "/test/env/path"})
    def test_environment_variable_substitution(self):
        """Test environment variable substitution in paths."""
        pm = PathManager()
        
        # Register a path with an environment variable
        pm.register_path("env_path", "${TEST_ENV_VAR}/subdir")
        
        # Resolve the path
        resolved = pm.resolve_path("env_path")
        self.assertEqual(resolved, Path("/test/env/path/subdir"))
        
        # Test with a non-existent environment variable
        pm.register_path("bad_env_path", "${NONEXISTENT_ENV_VAR}/subdir")
        with self.assertRaises(PathResolutionError):
            pm.resolve_path("bad_env_path")


if __name__ == "__main__":
    unittest.main()
