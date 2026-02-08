"""
WebSocket Consumer for Animal Recognition
Handles real-time camera frame processing.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from src.domain.entities import RecognitionResult, Animal, Discovery
from src.domain.ports import NotificationPort
from src.application.use_cases import (
    ProcessFrameUseCase,
    StartSessionUseCase,
    EndSessionUseCase,
    GetSessionDiscoveriesUseCase,
)
from src.infrastructure.persistence import (
    DjangoAnimalRepository,
    DjangoSessionRepository,
    DjangoDiscoveryRepository,
)
from src.infrastructure.ml import TensorFlowAnimalRecognition, YOLOAnimalRecognition
from src.infrastructure.storage import get_image_storage

logger = logging.getLogger(__name__)


class WebSocketNotificationAdapter(NotificationPort):
    """Adapter to send notifications via WebSocket"""
    
    def __init__(self, consumer: 'AnimalRecognitionConsumer'):
        self._consumer = consumer
    
    async def send_recognition_result(
        self,
        session_id: str,
        result: RecognitionResult,
        animal: Animal
    ) -> None:
        await self._consumer.send_json({
            'type': 'recognition',
            'data': {
                'recognition': result.to_dict(),
                'animal': animal.to_dict(),
            }
        })
    
    async def send_discovery_update(
        self,
        session_id: str,
        discovery: Discovery
    ) -> None:
        await self._consumer.send_json({
            'type': 'discovery',
            'data': discovery.to_dict(),
        })
    
    async def send_error(self, session_id: str, error: str) -> None:
        await self._consumer.send_json({
            'type': 'error',
            'data': {'message': error},
        })
    
    async def send_detections(self, session_id: str, detections: list) -> None:
        await self._consumer.send_detections(detections)


class AnimalRecognitionConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time animal recognition.
    Handles camera frames and sends back recognition results.
    """
    
    # Class variable para lazy loading del modelo
    _recognition_service = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.notification_adapter = None
        
        # Initialize repositories
        self.animal_repo = DjangoAnimalRepository()
        self.session_repo = DjangoSessionRepository()
        self.discovery_repo = DjangoDiscoveryRepository()
        
        # Recognition service se carga en connect()
        self.recognition_service = None
        self.image_storage = get_image_storage()
    
    async def connect(self):
        """Handle WebSocket connection"""
        try:
            await self.accept()
            
            # Initialize notification adapter
            self.notification_adapter = WebSocketNotificationAdapter(self)
            
            # Lazy load recognition service on first connection
            if self.recognition_service is None:
                logger.info("🔄 Cargando servicio de reconocimiento (primera conexión)...")
                self.recognition_service = await sync_to_async(
                    self._load_recognition_service
                )()
            
            # Start a new session
            start_session = StartSessionUseCase(self.session_repo)
            session_data = await sync_to_async(start_session.execute)()
            self.session_id = session_data['id']
            
            logger.info(f"✅ WebSocket connected. Session: {self.session_id}")
            
            # Send session info to client
            await self.send_json({
                'type': 'session_started',
                'data': session_data,
            })
        except Exception as e:
            logger.error(f"❌ Error en connect: {str(e)}")
            await self.close()
    
    def _load_recognition_service(self):
        """Carga el servicio de reconocimiento (llamado en sync_to_async)"""
        logger.info("🚀 Inicializando YOLOAnimalRecognition...")
        return YOLOAnimalRecognition(
            confidence_threshold=0.5  # 50% confianza mínima
        )
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if self.session_id:
            # End session
            end_session = EndSessionUseCase(
                self.session_repo,
                self.discovery_repo,
                self.animal_repo,
            )
            try:
                summary = await sync_to_async(end_session.execute)(self.session_id)
                logger.info(f"Session ended: {self.session_id} - {summary['total_discoveries']} discoveries")
            except Exception as e:
                logger.error(f"Error ending session: {str(e)}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'frame':
                await self.handle_frame(data.get('data'))
            elif message_type == 'get_discoveries':
                await self.handle_get_discoveries()
            elif message_type == 'ping':
                await self.send_json({'type': 'pong'})
            else:
                logger.warning(f"Unknown message type: {message_type}")
            
                if message_type == 'frame':
                    logger.debug(f"📨 Frame recibido (tamaño: {len(data.get('data', ''))} bytes)")
                    await self.handle_frame(data.get('data'))
                
        except json.JSONDecodeError:
            await self.send_json({
                'type': 'error',
                'data': {'message': 'Invalid JSON'}
            })
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send_json({
                'type': 'error',
                'data': {'message': str(e)}
            })
    
    async def handle_frame(self, frame_data: str):
        """Process a camera frame"""
        if not frame_data:
            return
        
        # Create use case
        process_frame = ProcessFrameUseCase(
            recognition_port=self.recognition_service,
            animal_repository=self.animal_repo,
            discovery_repository=self.discovery_repo,
            session_repository=self.session_repo,
            image_storage=self.image_storage,
            notification_port=self.notification_adapter,
        )
        
        # Process frame
        response = await process_frame.execute(self.session_id, frame_data)
        
        if not response.success:
            await self.send_json({
                'type': 'error',
                'data': {'message': response.error}
            })
    
    async def handle_get_discoveries(self):
        """Get all discoveries for current session"""
        get_discoveries = GetSessionDiscoveriesUseCase(
            self.discovery_repo,
            self.animal_repo,
        )
        
        discoveries = await sync_to_async(get_discoveries.execute)(self.session_id)
        
        await self.send_json({
            'type': 'discoveries',
            'data': discoveries,
        })
    
    async def send_json(self, data: dict):
        """Send JSON data to client"""
        await self.send(text_data=json.dumps(data))
    
    async def send_detections(self, detections: list) -> None:
        """Send detection boxes to client (for bounding box visualization)"""
        await self.send_json({
            'type': 'detections',
            'data': {
                'detections': detections
            }
        })
