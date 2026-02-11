"""
ML Service - Animal Recognition Adapter
Implements the AnimalRecognitionPort using YOLO (YOLOv8).
Handles real-time animal detection from camera frames.
"""
import os
import logging
from typing import List, Optional
import numpy as np
from pathlib import Path

from src.domain.entities import RecognitionResult
from src.domain.value_objects import ImageFrame
from src.domain.ports import AnimalRecognitionPort
from src.domain.exceptions import RecognitionException, ModelNotReadyException

logger = logging.getLogger(__name__)


# Mapeo de clases YOLO a nombres en español
# Clases del modelo best.pt (Modelo personalizado con 10 animales)
YOLO_CLASS_MAPPING = {
    0: "Bird",       # Pájaro
    1: "Cats",       # Gato
    2: "Cow",        # Vaca
    3: "Deer",       # Ciervo
    4: "Dog",        # Perro
    5: "Elephant",   # Elefante
    6: "Giraffle",   # Jirafa (nota: modelo tiene typo "Giraffle")
    7: "Person",     # Persona
    8: "Pig",        # Cerdo
    9: "Sheep",      # Oveja
}


class YOLOAnimalRecognition(AnimalRecognitionPort):
    """
    YOLO (YOLOv8) implementation of AnimalRecognitionPort.
    Uses best.pt pre-trained model for real-time animal detection.
    
    El modelo se carga UNA SOLA VEZ en memoria (al iniciar el servidor).
    Cada frame es procesado en ~20-50ms según GPU disponible.
    """
    
    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.5):
        self._model = None
        self._model_path = model_path
        self._confidence_threshold = confidence_threshold
        self._is_ready = False
        
        logger.info("🚀 Inicializando YOLOAnimalRecognition...")
        self._load_model()
    
    def _load_model(self) -> None:
        """
        Carga el modelo YOLO best.pt.
        Se ejecuta UNA SOLA VEZ al iniciar el servidor.
        """
        try:
            from ultralytics import YOLO
            
            # Ruta del modelo - por defecto en la raíz del proyecto
            if not self._model_path:
                # Buscar best.pt en la raíz del proyecto Django
                base_path = Path(__file__).resolve().parent.parent.parent.parent  # POKEDEX/
                self._model_path = os.path.join(base_path, "best.pt")
            
            # Verificar que el archivo existe
            if not os.path.exists(self._model_path):
                raise FileNotFoundError(
                    f"El modelo best.pt no se encontró en: {self._model_path}\n"
                    f"Descargalo desde: https://github.com/your-repo/releases/download/v1/best.pt"
                )
            
            # Cargar el modelo YOLO
            logger.info(f"📦 Cargando YOLO desde: {self._model_path}")
            self._model = YOLO(self._model_path)
            
            # Verificar que se cargó correctamente
            if self._model is None:
                raise Exception("Failed to initialize YOLO model")
            
            self._is_ready = True
            logger.info(f"✅ YOLO cargado exitosamente")
            logger.info(f"   Confianza mínima: {self._confidence_threshold * 100:.0f}%")
            
        except ImportError as e:
            logger.error(
                f"❌ Error: ultralytics no está instalada\n"
                f"   Instala con: pip install ultralytics"
            )
            self._is_ready = False
            raise
        except FileNotFoundError as e:
            logger.error(f"❌ {str(e)}")
            self._is_ready = False
            raise
        except Exception as e:
            logger.error(f"❌ Error cargando YOLO: {str(e)}")
            self._is_ready = False
            raise
    
    def preprocess_image(self, frame: ImageFrame) -> np.ndarray:
        """
        Preprocesa un frame de imagen para reconocimiento.
        Convierte ImageFrame → numpy array OpenCV.
        """
        try:
            import cv2
            import base64
            
            # Decodificar base64 si viene en ese formato
            if isinstance(frame.data, str):
                # Es base64
                if ',' in frame.data:
                    frame_data = frame.data.split(',')[1]
                else:
                    frame_data = frame.data
                
                # Decodificar a bytes
                img_bytes = base64.b64decode(frame_data)
                nparr = np.frombuffer(img_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                # Ya es bytes
                nparr = np.frombuffer(frame.data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise RecognitionException("Failed to decode image")
            
            return image
            
        except Exception as e:
            raise RecognitionException(f"Image preprocessing failed: {str(e)}")
    
    def recognize(self, image: np.ndarray) -> List[RecognitionResult]:
        """
        Detecta animales en la imagen usando YOLO.
        
        Args:
            image: numpy array con formato OpenCV (BGR, HxWx3)
        
        Returns:
            Lista de RecognitionResult con los animales detectados
        """
        if not self._is_ready or self._model is None:
            raise ModelNotReadyException("Modelo YOLO no está listo")
        
        try:
            # Ejecutar YOLO - Simple y directo
            results = self._model(image)

            if not results or results[0].boxes is None:
                return []

            recognition_results = []

            # Procesar cada detección
            for box in results[0].boxes:
                conf = float(box.conf[0]) if box.conf is not None else 0
                cls_idx = int(box.cls[0]) if box.cls is not None else -1
                
                if conf >= self._confidence_threshold:
                    animal_name = YOLO_CLASS_MAPPING.get(cls_idx, f"Unknown_{cls_idx}")
                    
                    # Extraer bounding box
                    bounding_box = None
                    try:
                        if hasattr(box, 'xyxy'):
                            coords = box.xyxy[0].tolist() if hasattr(box.xyxy, '__len__') else box.xyxy.tolist()
                            if coords:
                                x1, y1, x2, y2 = map(int, coords[:4])
                                bounding_box = {'x': x1, 'y': y1, 'width': x2-x1, 'height': y2-y1}
                    except Exception:
                        pass
                    
                    recognition_results.append(RecognitionResult(
                        animal_id="",
                        animal_name=animal_name,
                        confidence=conf,
                        bounding_box=bounding_box,
                    ))
                    
                    logger.debug(f"🐾 Detectado: {animal_name} (conf: {conf:.1%})")
            
            return recognition_results
            
        except Exception as e:
            logger.error(f"❌ Error en reconocimiento YOLO: {str(e)}")
            raise RecognitionException(f"Reconocimiento fallido: {str(e)}")
    
    def get_supported_animals(self) -> List[str]:
        """Retorna lista de animales soportados por el modelo"""
        return list(YOLO_CLASS_MAPPING.values())
    
    def is_ready(self) -> bool:
        """Verifica si el modelo está cargado y listo"""
        return self._is_ready and self._model is not None


class TensorFlowAnimalRecognition(AnimalRecognitionPort):
    """
    DEPRECATED: Usar YOLOAnimalRecognition en su lugar.
    Mantener para compatibilidad hacia atrás.
    """
    
    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.7):
        logger.warning(
            "⚠️ TensorFlowAnimalRecognition está deprecated. "
            "Usar YOLOAnimalRecognition en su lugar."
        )
        self._model = None
        self._model_path = model_path
        self._confidence_threshold = confidence_threshold
        self._is_ready = False
        self._labels = list(YOLO_CLASS_MAPPING.values())
        
        # Try to load model on initialization
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the TensorFlow model"""
        try:
            # In production, this would load a real model
            # For now, we'll use a mock implementation
            if self._model_path and os.path.exists(self._model_path):
                import tensorflow as tf
                self._model = tf.keras.models.load_model(self._model_path)
                self._is_ready = True
                logger.info(f"Model loaded from {self._model_path}")
            else:
                # Mock mode for development
                logger.warning("Running in mock mode - no real model loaded")
                self._is_ready = True
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            self._is_ready = False
    
    def preprocess_image(self, frame: ImageFrame) -> np.ndarray:
        """Preprocess an image frame for recognition"""
        try:
            import cv2
            
            # Decode image from bytes
            nparr = np.frombuffer(frame.data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise RecognitionException("Failed to decode image")
            
            # Resize to model input size (224x224 for most models)
            image = cv2.resize(image, (224, 224))
            
            # Convert BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Normalize pixel values
            image = image.astype(np.float32) / 255.0
            
            # Add batch dimension
            image = np.expand_dims(image, axis=0)
            
            return image
            
        except Exception as e:
            raise RecognitionException(f"Image preprocessing failed: {str(e)}")
    
    def recognize(self, image: np.ndarray) -> List[RecognitionResult]:
        """Recognize animals in a preprocessed image"""
        if not self._is_ready:
            raise ModelNotReadyException("Model is not ready")
        
        try:
            if self._model is not None:
                # Real model prediction
                predictions = self._model.predict(image, verbose=0)
                return self._process_predictions(predictions[0])
            else:
                # Mock prediction for development
                return self._mock_prediction()
                
        except Exception as e:
            raise RecognitionException(f"Recognition failed: {str(e)}")
    
    def _process_predictions(self, predictions: np.ndarray) -> List[RecognitionResult]:
        """Process model predictions into RecognitionResult objects"""
        results = []
        
        # Get indices sorted by confidence (descending)
        sorted_indices = np.argsort(predictions)[::-1]
        
        for idx in sorted_indices[:5]:  # Top 5 predictions
            confidence = float(predictions[idx])
            if confidence >= self._confidence_threshold:
                results.append(RecognitionResult(
                    animal_id="",  # Will be filled by the service
                    animal_name=self._labels[idx],
                    confidence=confidence,
                ))
        
        return results
    
    def _mock_prediction(self) -> List[RecognitionResult]:
        """Generate mock predictions for development"""
        import random
        
        # Randomly select an animal with random confidence
        if random.random() > 0.3:  # 70% chance of detection
            animal = random.choice(self._labels)
            confidence = random.uniform(0.7, 0.98)
            
            return [RecognitionResult(
                animal_id="",
                animal_name=animal,
                confidence=confidence,
            )]
        
        return []
    
    def get_supported_animals(self) -> List[str]:
        """Get list of supported animal names"""
        return self._labels.copy()
    
    def is_ready(self) -> bool:
        """Check if the recognition service is ready"""
        return self._is_ready


class OpenCVPreprocessor:
    """
    OpenCV-based image preprocessing utilities.
    """
    
    @staticmethod
    def decode_base64_image(base64_string: str) -> np.ndarray:
        """Decode a base64 image string to numpy array"""
        import cv2
        import base64
        
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        img_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(img_data, np.uint8)
        
        # Decode image
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        return image
    
    @staticmethod
    def create_thumbnail(image: np.ndarray, size: tuple = (100, 100)) -> bytes:
        """Create a thumbnail from an image"""
        import cv2
        
        # Resize maintaining aspect ratio
        h, w = image.shape[:2]
        aspect = w / h
        
        if aspect > 1:
            new_w = size[0]
            new_h = int(size[0] / aspect)
        else:
            new_h = size[1]
            new_w = int(size[1] * aspect)
        
        thumbnail = cv2.resize(image, (new_w, new_h))
        
        # Encode to JPEG
        _, buffer = cv2.imencode('.jpg', thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        return buffer.tobytes()
    
    @staticmethod
    def draw_bounding_box(
        image: np.ndarray,
        box: dict,
        label: str,
        confidence: float
    ) -> np.ndarray:
        """Draw a bounding box with label on an image"""
        import cv2
        
        x, y, w, h = box['x'], box['y'], box['width'], box['height']
        
        # Draw rectangle
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Draw label background
        label_text = f"{label}: {confidence:.1%}"
        (text_w, text_h), _ = cv2.getTextSize(
            label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1
        )
        cv2.rectangle(
            image,
            (x, y - text_h - 10),
            (x + text_w + 10, y),
            (0, 255, 0),
            -1
        )
        
        # Draw label text
        cv2.putText(
            image,
            label_text,
            (x + 5, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            1
        )
        
        return image
