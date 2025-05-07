import cv2
import numpy as np
from pathlib import Path

class DefectDetectionService:
    def __init__(self):
        self.image_size = (224, 224)
        self.threshold_area = 100
        self.threshold_intensity = 50

    def analyze_image(self, image_path):
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                raise ValueError("Could not read image")

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            defects = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.threshold_area:
                    defects.append(area)
            
            total_defect_area = sum(defects)
            image_area = img.shape[0] * img.shape[1]
            defect_ratio = total_defect_area / image_area
            
            is_defective = defect_ratio > 0.01
            confidence = min(defect_ratio * 100, 100)
            
            recommendations = self.generate_recommendations(is_defective, confidence, len(defects))
            
            return {
                'is_defective': is_defective,
                'confidence': confidence,
                'prediction': confidence / 100,
                'recommendations': recommendations,
                'defect_count': len(defects)
            }
            
        except Exception as e:
            return {
                'error': str(e)
            }

    def generate_recommendations(self, is_defective, confidence, defect_count):
        if is_defective:
            if confidence > 70:
                return f"Severe defects detected ({defect_count} areas). Immediate inspection recommended."
            elif confidence > 40:
                return f"Moderate defects detected ({defect_count} areas). Schedule maintenance soon."
            else:
                return f"Minor defects detected ({defect_count} areas). Monitor condition."
        return "No significant defects detected. Regular maintenance recommended." 