"""
Visual regression testing module
"""
import os
import time
from typing import Dict, List, Any
from PIL import Image, ImageChops
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.system.config import TestConfig


class VisualRegressionTester:
    """Visual regression testing using screenshot comparison."""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.screenshot_dir = config.screenshot_dir
        self.baseline_dir = os.path.join(self.screenshot_dir, "baseline")
        self.current_dir = os.path.join(self.screenshot_dir, "current")
        self.diff_dir = os.path.join(self.screenshot_dir, "diff")
        
        # Create directories if they don't exist
        for directory in [self.baseline_dir, self.current_dir, self.diff_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def capture_screenshot(self, driver: webdriver, page_name: str, viewport_size: tuple = (1920, 1080)) -> str:
        """Capture screenshot of current page."""
        driver.set_window_size(*viewport_size)
        time.sleep(1)  # Wait for page to settle
        
        screenshot_path = os.path.join(self.current_dir, f"{page_name}_{viewport_size[0]}x{viewport_size[1]}.png")
        driver.save_screenshot(screenshot_path)
        return screenshot_path
    
    def compare_screenshots(self, baseline_path: str, current_path: str, diff_path: str) -> Dict[str, Any]:
        """Compare two screenshots and generate diff image."""
        try:
            # Open images
            baseline = Image.open(baseline_path)
            current = Image.open(current_path)
            
            # Ensure images are the same size
            if baseline.size != current.size:
                current = current.resize(baseline.size)
            
            # Calculate difference
            diff = ImageChops.difference(baseline, current)
            
            # Calculate percentage difference
            histogram = diff.histogram()
            total_pixels = baseline.size[0] * baseline.size[1]
            changed_pixels = sum(histogram[256:])  # Non-zero differences
            difference_percentage = (changed_pixels / total_pixels) * 100
            
            # Save diff image if there are differences
            if difference_percentage > 0:
                diff.save(diff_path)
            
            return {
                "difference_percentage": difference_percentage,
                "has_differences": difference_percentage > 0.1,  # 0.1% threshold
                "total_pixels": total_pixels,
                "changed_pixels": changed_pixels,
                "diff_image_path": diff_path if difference_percentage > 0 else None
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "has_differences": True,  # Assume differences on error
                "difference_percentage": 100.0
            }
    
    def test_page_visual_regression(self, driver: webdriver, page_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test visual regression for a single page."""
        page_name = page_config["name"]
        page_url = page_config["url"]
        viewports = page_config.get("viewports", [(1920, 1080), (1366, 768), (375, 667)])
        
        results = {
            "page_name": page_name,
            "page_url": page_url,
            "viewport_results": [],
            "overall_status": "PASS"
        }
        
        try:
            # Navigate to page
            driver.get(page_url)
            
            # Wait for page to load
            WebDriverWait(driver, self.config.page_load_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Test each viewport size
            for viewport in viewports:
                viewport_name = f"{viewport[0]}x{viewport[1]}"
                
                # Capture current screenshot
                current_screenshot = self.capture_screenshot(driver, f"{page_name}_{viewport_name}", viewport)
                
                # Check if baseline exists
                baseline_screenshot = os.path.join(self.baseline_dir, f"{page_name}_{viewport_name}.png")
                
                if not os.path.exists(baseline_screenshot):
                    # No baseline - copy current as baseline
                    import shutil
                    shutil.copy2(current_screenshot, baseline_screenshot)
                    
                    viewport_result = {
                        "viewport": viewport_name,
                        "status": "BASELINE_CREATED",
                        "message": "Baseline screenshot created"
                    }
                else:
                    # Compare with baseline
                    diff_screenshot = os.path.join(self.diff_dir, f"{page_name}_{viewport_name}_diff.png")
                    comparison = self.compare_screenshots(baseline_screenshot, current_screenshot, diff_screenshot)
                    
                    viewport_result = {
                        "viewport": viewport_name,
                        "status": "PASS" if not comparison.get("has_differences", True) else "FAIL",
                        "difference_percentage": comparison.get("difference_percentage", 0),
                        "changed_pixels": comparison.get("changed_pixels", 0),
                        "diff_image": comparison.get("diff_image_path"),
                        "baseline_image": baseline_screenshot,
                        "current_image": current_screenshot
                    }
                    
                    if viewport_result["status"] == "FAIL":
                        results["overall_status"] = "FAIL"
                
                results["viewport_results"].append(viewport_result)
                
        except Exception as e:
            results["overall_status"] = "ERROR"
            results["error"] = str(e)
        
        return results
    
    def run_visual_regression_tests(self, driver: webdriver) -> Dict[str, Any]:
        """Run visual regression tests for all configured pages."""
        print("\n📸 Running Visual Regression Tests...")
        
        # Pages to test
        pages_to_test = [
            {
                "name": "homepage",
                "url": self.config.base_url,
                "viewports": [(1920, 1080), (1366, 768), (375, 667)]
            },
            {
                "name": "login",
                "url": f"{self.config.base_url}/login",
                "viewports": [(1920, 1080), (375, 667)]
            },
            {
                "name": "dashboard",
                "url": f"{self.config.base_url}/dashboard",
                "viewports": [(1920, 1080), (1366, 768)]
            }
        ]
        
        results = {
            "timestamp": time.time(),
            "total_pages": len(pages_to_test),
            "pages_passed": 0,
            "pages_failed": 0,
            "page_results": []
        }
        
        for page_config in pages_to_test:
            print(f"   📷 Testing {page_config['name']} page...")
            
            page_result = self.test_page_visual_regression(driver, page_config)
            results["page_results"].append(page_result)
            
            if page_result["overall_status"] == "PASS":
                results["pages_passed"] += 1
                print(f"      ✅ {page_config['name']}: PASS")
            elif page_result["overall_status"] == "BASELINE_CREATED":
                results["pages_passed"] += 1
                print(f"      📝 {page_config['name']}: BASELINE CREATED")
            else:
                results["pages_failed"] += 1
                print(f"      ❌ {page_config['name']}: FAIL")
                
                # Show viewport failures
                for viewport_result in page_result.get("viewport_results", []):
                    if viewport_result["status"] == "FAIL":
                        print(f"         {viewport_result['viewport']}: {viewport_result['difference_percentage']:.2f}% different")
        
        results["success_rate"] = f"{(results['pages_passed'] / results['total_pages']) * 100:.1f}%"
        
        print(f"   📊 Visual Tests: {results['pages_passed']}/{results['total_pages']} passed")
        
        return results
    
    def update_baselines(self):
        """Update baseline screenshots with current screenshots."""
        import shutil
        
        print("🔄 Updating baseline screenshots...")
        
        # Copy all current screenshots to baseline
        for filename in os.listdir(self.current_dir):
            if filename.endswith('.png'):
                current_path = os.path.join(self.current_dir, filename)
                baseline_path = os.path.join(self.baseline_dir, filename)
                shutil.copy2(current_path, baseline_path)
                print(f"   ✅ Updated baseline: {filename}")
        
        print("   📝 Baseline screenshots updated successfully")