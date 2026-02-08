"""
Application Use Cases - Recognition
Handles the animal recognition workflow.
"""
from dataclasses import dataclass
from typing import Optional, List
import logging
from asgiref.sync import sync_to_async

from src.domain.entities import Animal, Discovery, RecognitionResult, UserSession
from src.domain.value_objects import ImageFrame
from src.domain.services import AnimalRecognitionService
from src.domain.ports import (
    AnimalRepositoryPort,
    DiscoveryRepositoryPort,
    SessionRepositoryPort,
    AnimalRecognitionPort,
    ImageStoragePort,
    NotificationPort,
)
from src.domain.exceptions import (
    SessionNotFoundException,
    InvalidImageException,
    ModelNotReadyException,
)

logger = logging.getLogger(__name__)


@dataclass
class RecognitionResponse:
    """Response DTO for recognition use case"""
    success: bool
    animal: Optional[dict] = None
    recognition: Optional[dict] = None
    discovery: Optional[dict] = None
    is_new_discovery: bool = False
    error: Optional[str] = None


class ProcessFrameUseCase:
    """
    Use Case: Process Camera Frame
    Processes a single frame from the camera and returns recognition results.
    """
    
    def __init__(
        self,
        recognition_port: AnimalRecognitionPort,
        animal_repository: AnimalRepositoryPort,
        discovery_repository: DiscoveryRepositoryPort,
        session_repository: SessionRepositoryPort,
        image_storage: ImageStoragePort,
        notification_port: NotificationPort,
        confidence_threshold: float = 0.7
    ):
        self._recognition_service = AnimalRecognitionService(
            recognition_port=recognition_port,
            animal_repository=animal_repository,
            discovery_repository=discovery_repository,
            image_storage=image_storage,
            confidence_threshold=confidence_threshold,
        )
        self._session_repo = session_repository
        self._notification = notification_port
        self._recognition_port = recognition_port
    
    async def execute(
        self, 
        session_id: str, 
        frame_data: str
    ) -> RecognitionResponse:
        """
        Execute the frame processing use case.
        
        Args:
            session_id: The active session ID
            frame_data: Base64 encoded image data
        
        Returns:
            RecognitionResponse with results
        """
        try:
            # Validate model is ready
            if not self._recognition_port.is_ready():
                raise ModelNotReadyException("Recognition model is not ready")
            
            # Get session (DB access - run in thread)
            session = await sync_to_async(self._session_repo.get_by_id, thread_sensitive=False)(session_id)
            if not session:
                raise SessionNotFoundException(session_id)
            
            # Parse image frame
            try:
                frame = ImageFrame.from_base64(frame_data)
            except Exception as e:
                raise InvalidImageException(f"Invalid image data: {str(e)}")
            
            # ====== STEP 1: Preprocess image ======
            processed_image = await sync_to_async(
                self._recognition_port.preprocess_image, 
                thread_sensitive=False
            )(frame)
            
            # ====== STEP 2: Get ALL detections (for bounding box visualization) ======
            all_detections = await sync_to_async(
                self._recognition_port.recognize, 
                thread_sensitive=False
            )(processed_image)
            
            # Convert detections to dict format for WebSocket
            detections_data = []
            if all_detections:
                for det in all_detections:
                    detection_dict = {
                        'class': det.animal_name,
                        'confidence': det.confidence,
                    }
                    # Add bounding box if available
                    if det.bounding_box:
                        detection_dict.update(det.bounding_box)
                    detections_data.append(detection_dict)
            
            # Send detections to client (for bounding box visualization)
            await self._notification.send_detections(session_id, detections_data)
            
            # ====== STEP 3: Process frame (filter by confidence threshold) ======
            result = await sync_to_async(self._recognition_service.process_frame, thread_sensitive=False)(frame, session)
            
            if not result:
                return RecognitionResponse(success=True)
            
            recognition_result, animal, discovery = result
            
            # Build response
            response = RecognitionResponse(
                success=True,
                animal=animal.to_dict(),
                recognition=recognition_result.to_dict(),
                discovery=discovery.to_dict() if discovery else None,
                is_new_discovery=discovery is not None,
            )
            
            # Send notifications
            await self._notification.send_recognition_result(
                session_id, recognition_result, animal
            )
            
            if discovery:
                await self._notification.send_discovery_update(
                    session_id, discovery
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing frame: {str(e)}")
            return RecognitionResponse(
                success=False,
                error=str(e)
            )


class StartSessionUseCase:
    """
    Use Case: Start Recognition Session
    Initializes a new recognition session for a user.
    """
    
    def __init__(self, session_repository: SessionRepositoryPort):
        self._session_repo = session_repository
    
    def execute(self, user_id: Optional[str] = None) -> dict:
        """
        Start a new session.
        
        Args:
            user_id: Optional user ID for registered users
        
        Returns:
            Session data
        """
        session = UserSession.create(user_id=user_id)
        saved_session = self._session_repo.create(session)
        
        logger.info(f"Started new session: {saved_session.id}")
        
        return saved_session.to_dict()


class EndSessionUseCase:
    """
    Use Case: End Recognition Session
    Ends a recognition session and returns summary.
    """
    
    def __init__(
        self,
        session_repository: SessionRepositoryPort,
        discovery_repository: DiscoveryRepositoryPort,
        animal_repository: AnimalRepositoryPort,
    ):
        self._session_repo = session_repository
        self._discovery_repo = discovery_repository
        self._animal_repo = animal_repository
    
    def execute(self, session_id: str) -> dict:
        """
        End a session and return summary.
        
        Args:
            session_id: The session ID to end
        
        Returns:
            Session summary with discoveries
        """
        session = self._session_repo.get_by_id(session_id)
        if not session:
            raise SessionNotFoundException(session_id)
        
        # Get all discoveries
        discoveries = self._discovery_repo.get_by_session(session_id)
        
        # Build summary
        discovery_details = []
        for disc in discoveries:
            animal = self._animal_repo.get_by_id(disc.animal_id)
            if animal:
                discovery_details.append({
                    'discovery': disc.to_dict(),
                    'animal': animal.to_dict(),
                })
        
        # End session
        self._session_repo.end_session(session_id)
        
        logger.info(f"Ended session: {session_id} with {len(discoveries)} discoveries")
        
        return {
            'session': session.to_dict(),
            'total_discoveries': len(discoveries),
            'unique_animals': len(set(d.animal_id for d in discoveries)),
            'discoveries': discovery_details,
        }


class GetSessionDiscoveriesUseCase:
    """
    Use Case: Get Session Discoveries
    Retrieves all discoveries for a session.
    """
    
    def __init__(
        self,
        discovery_repository: DiscoveryRepositoryPort,
        animal_repository: AnimalRepositoryPort,
    ):
        self._discovery_repo = discovery_repository
        self._animal_repo = animal_repository
    
    def execute(self, session_id: str) -> List[dict]:
        """
        Get all discoveries for a session.
        
        Args:
            session_id: The session ID
        
        Returns:
            List of discoveries with animal info
        """
        discoveries = self._discovery_repo.get_by_session(session_id)
        
        result = []
        for disc in discoveries:
            animal = self._animal_repo.get_by_id(disc.animal_id)
            if animal:
                result.append({
                    'discovery': disc.to_dict(),
                    'animal': {
                        'id': animal.id,
                        'name': animal.name,
                        'image_url': animal.image_url,
                    },
                })
        
        return result
