"""
Domain Value Objects
Immutable objects that represent concepts in our domain.
"""
from dataclasses import dataclass
from typing import Optional, Tuple
import base64


@dataclass(frozen=True)
class ImageFrame:
    """
    Value Object: Image Frame
    Represents a single frame from the camera.
    """
    data: bytes
    width: int
    height: int
    channels: int = 3
    format: str = "jpeg"
    
    @classmethod
    def from_base64(cls, base64_string: str, width: int = 640, height: int = 480) -> 'ImageFrame':
        """Create ImageFrame from base64 encoded string"""
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        data = base64.b64decode(base64_string)
        return cls(data=data, width=width, height=height)
    
    def to_base64(self) -> str:
        """Convert to base64 string"""
        return base64.b64encode(self.data).decode('utf-8')
    
    def get_data_url(self) -> str:
        """Get data URL for HTML embedding"""
        return f"data:image/{self.format};base64,{self.to_base64()}"


@dataclass(frozen=True)
class BoundingBox:
    """
    Value Object: Bounding Box
    Represents a rectangular region in an image.
    """
    x: int
    y: int
    width: int
    height: int
    
    @property
    def center(self) -> Tuple[int, int]:
        """Get the center point of the bounding box"""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def area(self) -> int:
        """Get the area of the bounding box"""
        return self.width * self.height
    
    def to_dict(self) -> dict:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
        }
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is inside the bounding box"""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)


@dataclass(frozen=True)
class Confidence:
    """
    Value Object: Confidence Score
    Represents a confidence score for a prediction.
    """
    value: float
    
    def __post_init__(self):
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")
    
    @property
    def percentage(self) -> float:
        """Get confidence as percentage"""
        return self.value * 100
    
    @property
    def percentage_string(self) -> str:
        """Get formatted percentage string"""
        return f"{self.percentage:.1f}%"
    
    def meets_threshold(self, threshold: float = 0.7) -> bool:
        """Check if confidence meets the threshold"""
        return self.value >= threshold
    
    @property
    def level(self) -> str:
        """Get human-readable confidence level"""
        if self.value >= 0.9:
            return "Muy Alto"
        elif self.value >= 0.7:
            return "Alto"
        elif self.value >= 0.5:
            return "Medio"
        elif self.value >= 0.3:
            return "Bajo"
        else:
            return "Muy Bajo"


@dataclass(frozen=True)
class GeoLocation:
    """
    Value Object: Geographic Location
    Represents a geographic coordinate.
    """
    latitude: float
    longitude: float
    name: Optional[str] = None
    
    def __post_init__(self):
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180")
    
    def to_dict(self) -> dict:
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'name': self.name,
        }


# Fix the Optional import
from typing import Optional
