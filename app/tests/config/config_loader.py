"""
Configuration loader for test system.

This module provides functionality to load and manage test configuration
from YAML files with environment-specific overrides.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
import logging


@dataclass
class TestConfig:
    """Test configuration container."""
    
    # Test suite configuration
    parallel: bool = True
    max_workers: int = 4
    coverage_threshold: float = 80.0
    performance_threshold_ms: float = 1000.0
    verbose: bool = False
    fail_fast: bool = False
    output_dir: str = "test_results"
    report_format: str = "html"
    categories: list = field(default_factory=list)
    exclude_categories: list = field(default_factory=list)
    
    # Timeouts
    timeouts: Dict[str, int] = field(default_factory=dict)
    
    # Database configuration
    database_urls: Dict[str, str] = field(default_factory=dict)
    database_connection: Dict[str, Any] = field(default_factory=dict)
    
    # Performance configuration
    performance_thresholds: Dict[str, float] = field(default_factory=dict)
    load_test_config: Dict[str, Any] = field(default_factory=dict)
    stress_test_config: Dict[str, Any] = field(default_factory=dict)
    
    # Security configuration
    security_config: Dict[str, Any] = field(default_factory=dict)
    
    # Coverage configuration
    coverage_thresholds: Dict[str, float] = field(default_factory=dict)
    coverage_report: Dict[str, Any] = field(default_factory=dict)
    coverage_exclude: list = field(default_factory=list)
    
    # Logging configuration
    logging_level: str = "INFO"
    logging_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_files: Dict[str, str] = field(default_factory=dict)
    log_rotation: Dict[str, Any] = field(default_factory=dict)
    
    # CI/CD configuration
    ci_cd_config: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> list:
        """Validate the configuration and return list of errors."""
        errors = []
        
        # Validate basic types
        if not isinstance(self.max_workers, int) or self.max_workers < 1:
            errors.append("max_workers must be an integer >= 1")
        
        if not isinstance(self.coverage_threshold, (int, float)) or not 0 <= self.coverage_threshold <= 100:
            errors.append("coverage_threshold must be a number between 0 and 100")
        
        if not isinstance(self.performance_threshold_ms, (int, float)) or self.performance_threshold_ms <= 0:
            errors.append("performance_threshold_ms must be a positive number")
        
        if self.report_format not in ["html", "json", "xml"]:
            errors.append("report_format must be one of: html, json, xml")
        
        # Validate timeouts
        for category, timeout in self.timeouts.items():
            if not isinstance(timeout, int) or timeout <= 0:
                errors.append(f"Timeout for {category} must be a positive integer")
        
        # Validate database URLs
        for category, url in self.database_urls.items():
            if not isinstance(url, str) or not url.strip():
                errors.append(f"Database URL for {category} must be a non-empty string")
        
        return errors


class TestConfigLoader:
    """Loads and manages test configuration from YAML files."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_dir: Directory containing configuration files. 
                       Defaults to app/tests/config
        """
        if config_dir is None:
            config_dir = Path(__file__).parent
        
        self.config_dir = Path(config_dir)
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, 
                   config_file: str = "test_config.yaml",
                   environment: Optional[str] = None,
                   overrides: Optional[Dict[str, Any]] = None) -> TestConfig:
        """
        Load configuration from YAML file with optional environment overrides.
        
        Args:
            config_file: Name of the configuration file
            environment: Environment name (development, staging, production)
            overrides: Additional configuration overrides
            
        Returns:
            Loaded TestConfig object
            
        Raises:
            FileNotFoundError: If configuration file not found
            yaml.YAMLError: If YAML parsing fails
            ValueError: If configuration validation fails
        """
        config_path = self.config_dir / config_file
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Load base configuration
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Apply environment-specific overrides
        if environment and 'environments' in config_data:
            env_config = config_data['environments'].get(environment, {})
            config_data = self._merge_configs(config_data, env_config)
        
        # Apply manual overrides
        if overrides:
            config_data = self._merge_configs(config_data, overrides)
        
        # Convert to TestConfig object
        config = self._dict_to_config(config_data)
        
        # Validate configuration
        errors = config.validate()
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
        
        self.logger.info(f"Loaded configuration from {config_path}")
        if environment:
            self.logger.info(f"Applied environment overrides for: {environment}")
        
        return config
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _dict_to_config(self, config_data: Dict[str, Any]) -> TestConfig:
        """Convert dictionary to TestConfig object."""
        config = TestConfig()
        
        # Test suite configuration
        if 'test_suite' in config_data:
            suite_config = config_data['test_suite']
            config.parallel = suite_config.get('parallel', config.parallel)
            config.max_workers = suite_config.get('max_workers', config.max_workers)
            config.coverage_threshold = suite_config.get('coverage_threshold', config.coverage_threshold)
            config.performance_threshold_ms = suite_config.get('performance_threshold_ms', config.performance_threshold_ms)
            config.verbose = suite_config.get('verbose', config.verbose)
            config.fail_fast = suite_config.get('fail_fast', config.fail_fast)
            config.output_dir = suite_config.get('output_dir', config.output_dir)
            config.report_format = suite_config.get('report_format', config.report_format)
            config.categories = suite_config.get('default_categories', config.categories)
            config.exclude_categories = suite_config.get('default_exclude_categories', config.exclude_categories)
        
        # Timeouts
        if 'timeouts' in config_data:
            config.timeouts = config_data['timeouts']
        
        # Database configuration
        if 'database' in config_data:
            db_config = config_data['database']
            config.database_urls = db_config.get('urls', config.database_urls)
            config.database_connection = db_config.get('connection', config.database_connection)
        
        # Performance configuration
        if 'performance' in config_data:
            perf_config = config_data['performance']
            config.performance_thresholds = perf_config.get('thresholds', config.performance_thresholds)
            config.load_test_config = perf_config.get('load_test', config.load_test_config)
            config.stress_test_config = perf_config.get('stress_test', config.stress_test_config)
        
        # Security configuration
        if 'security' in config_data:
            config.security_config = config_data['security']
        
        # Coverage configuration
        if 'coverage' in config_data:
            cov_config = config_data['coverage']
            config.coverage_thresholds = cov_config.get('thresholds', config.coverage_thresholds)
            config.coverage_report = cov_config.get('report', config.coverage_report)
            config.coverage_exclude = cov_config.get('exclude', config.coverage_exclude)
        
        # Logging configuration
        if 'logging' in config_data:
            log_config = config_data['logging']
            config.logging_level = log_config.get('level', config.logging_level)
            config.logging_format = log_config.get('format', config.logging_format)
            config.log_files = log_config.get('files', config.log_files)
            config.log_rotation = log_config.get('rotation', config.log_rotation)
        
        # CI/CD configuration
        if 'ci_cd' in config_data:
            config.ci_cd_config = config_data['ci_cd']
        
        return config
    
    def save_config(self, config: TestConfig, config_file: str = "test_config_generated.yaml"):
        """
        Save configuration to YAML file.
        
        Args:
            config: TestConfig object to save
            config_file: Name of the output file
        """
        config_path = self.config_dir / config_file
        
        # Convert TestConfig to dictionary
        config_dict = {
            'test_suite': {
                'parallel': config.parallel,
                'max_workers': config.max_workers,
                'coverage_threshold': config.coverage_threshold,
                'performance_threshold_ms': config.performance_threshold_ms,
                'verbose': config.verbose,
                'fail_fast': config.fail_fast,
                'output_dir': config.output_dir,
                'report_format': config.report_format,
                'default_categories': config.categories,
                'default_exclude_categories': config.exclude_categories
            },
            'timeouts': config.timeouts,
            'database': {
                'urls': config.database_urls,
                'connection': config.database_connection
            },
            'performance': {
                'thresholds': config.performance_thresholds,
                'load_test': config.load_test_config,
                'stress_test': config.stress_test_config
            },
            'security': config.security_config,
            'coverage': {
                'thresholds': config.coverage_thresholds,
                'report': config.coverage_report,
                'exclude': config.coverage_exclude
            },
            'logging': {
                'level': config.logging_level,
                'format': config.logging_format,
                'files': config.log_files,
                'rotation': config.log_rotation
            },
            'ci_cd': config.ci_cd_config
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        
        self.logger.info(f"Saved configuration to {config_path}")


def load_test_config(environment: Optional[str] = None, 
                    overrides: Optional[Dict[str, Any]] = None) -> TestConfig:
    """
    Convenience function to load test configuration.
    
    Args:
        environment: Environment name
        overrides: Configuration overrides
        
    Returns:
        Loaded TestConfig object
    """
    loader = TestConfigLoader()
    return loader.load_config(environment=environment, overrides=overrides)
