"""
Data provider service for origin validation.

This module provides external data access for the origin validation system,
including configuration loading and caching.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache


class OriginDataProvider:
    """Provides external data for origin validation."""
    
    def __init__(self, config_path: Path):
        self.config_path = Path(config_path)
        self._regions_cache: Optional[Dict[str, Any]] = None
        self._certifications_cache: Optional[Dict[str, Any]] = None
        
        # Validate config path exists
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration path does not exist: {config_path}")
    
    @property
    def regions(self) -> Dict[str, Any]:
        """Get regional configuration with caching."""
        if self._regions_cache is None:
            self._regions_cache = self._load_json_config("regions.json")
        return self._regions_cache
    
    @property
    def certifications(self) -> Dict[str, Any]:
        """Get certification configuration with caching."""
        if self._certifications_cache is None:
            self._certifications_cache = self._load_json_config("certifications.json")
        return self._certifications_cache
    
    def get_regional_requirements(self, region: str, category: str) -> Dict[str, Any]:
        """
        Get certification requirements for region and category.
        
        Args:
            region: Palm oil region name
            category: Product category
            
        Returns:
            Regional requirements dictionary
        """
        return (self.certifications
                .get("regional_requirements", {})
                .get(region, {})
                .get(category, {}))
    
    def get_certification_body_info(self, certification: str) -> Dict[str, Any]:
        """
        Get information about a certification body.
        
        Args:
            certification: Certification body name
            
        Returns:
            Certification body information
        """
        return (self.certifications
                .get("certification_bodies", {})
                .get(certification, {}))
    
    def get_product_category_requirements(self, category: str) -> Dict[str, Any]:
        """
        Get requirements for a product category.
        
        Args:
            category: Product category
            
        Returns:
            Category requirements dictionary
        """
        return (self.certifications
                .get("product_categories", {})
                .get(category, {}))
    
    def get_high_value_certifications(self) -> list[str]:
        """Get list of high-value certification names."""
        high_value = []
        cert_bodies = self.certifications.get("certification_bodies", {})
        
        for cert_name, cert_info in cert_bodies.items():
            if cert_info.get("is_high_value", False):
                high_value.append(cert_name)
        
        return high_value
    
    def get_region_names(self) -> list[str]:
        """Get list of all configured region names."""
        return list(self.regions.keys())
    
    def get_certification_names(self) -> list[str]:
        """Get list of all configured certification names."""
        return list(self.certifications.get("certification_bodies", {}).keys())
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate configuration files for completeness and consistency.
        
        Returns:
            Validation report
        """
        report = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "regions_count": 0,
            "certifications_count": 0
        }
        
        try:
            # Validate regions configuration
            regions = self.regions
            report["regions_count"] = len(regions)
            
            for region_name, region_config in regions.items():
                required_fields = ["name", "min_latitude", "max_latitude", 
                                 "min_longitude", "max_longitude", "description"]
                for field in required_fields:
                    if field not in region_config:
                        report["errors"].append(f"Region {region_name} missing required field: {field}")
                        report["is_valid"] = False
                
                # Validate coordinate ranges
                if "min_latitude" in region_config and "max_latitude" in region_config:
                    if region_config["min_latitude"] >= region_config["max_latitude"]:
                        report["errors"].append(f"Region {region_name} has invalid latitude range")
                        report["is_valid"] = False
                
                if "min_longitude" in region_config and "max_longitude" in region_config:
                    if region_config["min_longitude"] >= region_config["max_longitude"]:
                        report["errors"].append(f"Region {region_name} has invalid longitude range")
                        report["is_valid"] = False
            
            # Validate certifications configuration
            certifications = self.certifications
            cert_bodies = certifications.get("certification_bodies", {})
            report["certifications_count"] = len(cert_bodies)
            
            for cert_name, cert_config in cert_bodies.items():
                required_fields = ["name", "description", "is_high_value"]
                for field in required_fields:
                    if field not in cert_config:
                        report["errors"].append(f"Certification {cert_name} missing required field: {field}")
                        report["is_valid"] = False
            
            # Check regional requirements consistency
            regional_reqs = certifications.get("regional_requirements", {})
            for region_name in regional_reqs.keys():
                if region_name not in regions:
                    report["warnings"].append(f"Regional requirement for unknown region: {region_name}")
            
        except Exception as e:
            report["errors"].append(f"Configuration validation error: {str(e)}")
            report["is_valid"] = False
        
        return report
    
    def reload_configuration(self) -> None:
        """Reload configuration from files, clearing cache."""
        self._regions_cache = None
        self._certifications_cache = None
    
    def _load_json_config(self, filename: str) -> Dict[str, Any]:
        """
        Load JSON configuration file.
        
        Args:
            filename: Name of the JSON file to load
            
        Returns:
            Parsed JSON data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
        """
        file_path = self.config_path / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in {filename}: {e.msg}",
                e.doc,
                e.pos
            )
    
    @lru_cache(maxsize=128)
    def get_cached_regional_requirements(self, region: str, category: str) -> Dict[str, Any]:
        """Cached version of get_regional_requirements for performance."""
        return self.get_regional_requirements(region, category)
    
    @lru_cache(maxsize=128)
    def get_cached_certification_info(self, certification: str) -> Dict[str, Any]:
        """Cached version of get_certification_body_info for performance."""
        return self.get_certification_body_info(certification)
    
    def clear_cache(self) -> None:
        """Clear all caches."""
        self._regions_cache = None
        self._certifications_cache = None
        self.get_cached_regional_requirements.cache_clear()
        self.get_cached_certification_info.cache_clear()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cache usage."""
        return {
            "regions_cached": self._regions_cache is not None,
            "certifications_cached": self._certifications_cache is not None,
            "regional_requirements_cache": self.get_cached_regional_requirements.cache_info()._asdict(),
            "certification_info_cache": self.get_cached_certification_info.cache_info()._asdict()
        }
