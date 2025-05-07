from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path
from django.core.files import File

class DefectDetectionYOLO:
    def __init__(self):
        try:
            # Charger le modèle YOLOv8
            self.model = YOLO('yolov8n.pt')
            self.confidence_threshold = 0.25
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            self.model = None

    def analyze_image(self, image_path):
        try:
            if self.model is None:
                raise ValueError("YOLO model not properly initialized")

            # Faire la prédiction
            results = self.model(image_path)
            result = results[0]

            # Traiter les détections
            detections = []
            for box in result.boxes:
                confidence = float(box.conf[0])
                if confidence > self.confidence_threshold:
                    class_id = int(box.cls[0])
                    class_name = result.names[class_id]
                    bbox = box.xyxy[0].tolist()

                    detections.append({
                        'class': class_name,
                        'confidence': float(confidence),
                        'bbox': bbox
                    })

            # Sauvegarder l'image annotée
            annotated_path = str(Path(image_path).with_suffix('.annotated.jpg'))
            result.save(filename=annotated_path)

            # Calculer les métriques globales
            avg_confidence = np.mean([d['confidence'] for d in detections]) if detections else 0
            is_defective = len(detections) > 0

            return {
                'is_defective': is_defective,
                'confidence': float(avg_confidence * 100),
                'detections': detections,
                'recommendations': self.generate_recommendations(detections),
                'annotated_image': annotated_path
            }

        except Exception as e:
            return {'error': str(e)}

    def generate_recommendations(self, detections):
        if not detections:
            return "No defects detected. Object appears to be in normal condition."
        
        num_defects = len(detections)
        avg_confidence = np.mean([d['confidence'] for d in detections])
        
        classes_found = set(d['class'] for d in detections)
        class_summary = ", ".join(classes_found)

        if avg_confidence > 0.8:
            return f"CRITICAL: Detected {num_defects} potential issues ({class_summary}) with high confidence."
        elif avg_confidence > 0.5:
            return f"WARNING: Found {num_defects} possible defects ({class_summary})."
        else:
            return f"INFO: Identified {num_defects} areas of interest ({class_summary})." 