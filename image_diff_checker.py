#!/usr/bin/env python3
"""
Image difference checker to detect if camera feed is frozen
"""
import cv2
import numpy as np
import sys

def calculate_image_difference(image1_path, image2_path):
    """
    Calculate difference between two images using multiple methods
    Returns a dictionary with different difference metrics
    """
    try:
        # Read images
        img1 = cv2.imread(image1_path)
        img2 = cv2.imread(image2_path)
        
        if img1 is None or img2 is None:
            return {"error": "Could not load one or both images"}
        
        # Resize images to same size if different
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        
        # Extract just the camera feed region (right side of the image)
        # Based on the screenshots, the camera feed is in the right third of the image
        height, width = img1.shape[:2]
        camera_x_start = int(width * 0.67)  # Start from 67% across the image
        
        camera1 = img1[:, camera_x_start:]
        camera2 = img2[:, camera_x_start:]
        
        # Convert to grayscale for comparison
        gray1 = cv2.cvtColor(camera1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(camera2, cv2.COLOR_BGR2GRAY)
        
        # Method 1: Mean Squared Error (MSE)
        mse = np.mean((gray1 - gray2) ** 2)
        
        # Method 2: Structural Similarity Index (SSIM)
        # Simple correlation coefficient as SSIM approximation
        mean1, mean2 = np.mean(gray1), np.mean(gray2)
        std1, std2 = np.std(gray1), np.std(gray2)
        correlation = np.mean((gray1 - mean1) * (gray2 - mean2)) / (std1 * std2) if std1 * std2 > 0 else 0
        
        # Method 3: Histogram comparison
        hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
        hist_correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        # Method 4: Number of different pixels (above threshold)
        diff_pixels = np.sum(np.abs(gray1.astype(int) - gray2.astype(int)) > 30)
        total_pixels = gray1.shape[0] * gray1.shape[1]
        diff_percentage = (diff_pixels / total_pixels) * 100
        
        # Check if images are black/empty
        mean_brightness1 = np.mean(gray1)
        mean_brightness2 = np.mean(gray2)
        is_black1 = mean_brightness1 < 20  # Very dark
        is_black2 = mean_brightness2 < 20
        
        return {
            "mse": float(mse),
            "correlation": float(correlation),
            "hist_correlation": float(hist_correlation), 
            "diff_pixels_percent": float(diff_percentage),
            "total_pixels": int(total_pixels),
            "different_pixels": int(diff_pixels),
            "mean_brightness1": float(mean_brightness1),
            "mean_brightness2": float(mean_brightness2),
            "is_black1": bool(is_black1),
            "is_black2": bool(is_black2)
        }
        
    except Exception as e:
        return {"error": str(e)}

def is_camera_frozen(before_image, after_image, threshold_mse=100, threshold_diff_percent=5):
    """
    Determine if camera is frozen based on image comparison
    Returns True if frozen, False if not frozen
    """
    diff_metrics = calculate_image_difference(before_image, after_image)
    
    if "error" in diff_metrics:
        print(f"Error comparing images: {diff_metrics['error']}")
        return None
    
    # Camera is considered frozen if:
    # 1. MSE is very low (images are very similar)
    # 2. Very few pixels are different
    # 3. High histogram correlation
    
    mse = diff_metrics["mse"]
    diff_percent = diff_metrics["diff_pixels_percent"]
    hist_corr = diff_metrics["hist_correlation"]
    
    is_frozen = (mse < threshold_mse and 
                diff_percent < threshold_diff_percent and 
                hist_corr > 0.95)
    
    print(f"Image Comparison Results:")
    print(f"  MSE: {mse:.2f} (threshold: {threshold_mse})")
    print(f"  Different pixels: {diff_percent:.2f}% (threshold: {threshold_diff_percent}%)")
    print(f"  Histogram correlation: {hist_corr:.4f} (threshold: 0.95)")
    print(f"  Correlation: {diff_metrics['correlation']:.4f}")
    print(f"  Camera brightness 1: {diff_metrics['mean_brightness1']:.1f} (black if < 20)")
    print(f"  Camera brightness 2: {diff_metrics['mean_brightness2']:.1f} (black if < 20)")
    print(f"  Image 1 is black: {diff_metrics['is_black1']}")
    print(f"  Image 2 is black: {diff_metrics['is_black2']}")
    print(f"  Camera frozen: {is_frozen}")
    
    return is_frozen

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python image_diff_checker.py <image1> <image2>")
        sys.exit(1)
    
    result = is_camera_frozen(sys.argv[1], sys.argv[2])
    if result is not None:
        sys.exit(0 if not result else 1)  # Exit 0 if not frozen, 1 if frozen