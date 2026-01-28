"""
REST API Views
Provides REST endpoints for animal information and session management.
"""
import random
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from src.application.use_cases import (
    GetAnimalDetailsUseCase,
    SearchAnimalsUseCase,
    ListAnimalsByClassUseCase,
    ListEndangeredAnimalsUseCase,
    ListAllAnimalsUseCase,
    StartSessionUseCase,
    EndSessionUseCase,
    GetSessionDiscoveriesUseCase,
)
from src.infrastructure.persistence import (
    DjangoAnimalRepository,
    DjangoSessionRepository,
    DjangoDiscoveryRepository,
)
from src.domain.exceptions import AnimalNotFoundException, SessionNotFoundException


class RecognizeImageView(APIView):
    """API endpoint to recognize an animal from an uploaded image"""
    
    def post(self, request):
        image_data = request.data.get('image')
        if not image_data:
            return Response(
                {'success': False, 'error': 'No image provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all animals for mock recognition
        repository = DjangoAnimalRepository()
        animals = repository.get_all()
        
        if not animals:
            return Response({
                'success': False,
                'error': 'No animals in database'
            })
        
        # Mock recognition - randomly select an animal
        # In production, this would use the ML model
        animal = random.choice(animals)
        confidence = random.uniform(0.75, 0.98)
        
        return Response({
            'success': True,
            'animal': animal.to_dict(),
            'recognition': {
                'animal_name': animal.name,
                'confidence': confidence,
            }
        })


class AnimalListView(APIView):
    """API endpoint to list all animals"""
    
    def get(self, request):
        use_case = ListAllAnimalsUseCase(DjangoAnimalRepository())
        animals = use_case.execute()
        return Response(animals)


class AnimalDetailView(APIView):
    """API endpoint to get animal details"""
    
    def get(self, request, animal_id):
        try:
            use_case = GetAnimalDetailsUseCase(DjangoAnimalRepository())
            animal = use_case.execute(animal_id)
            return Response(animal)
        except AnimalNotFoundException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )


class AnimalSearchView(APIView):
    """API endpoint to search animals"""
    
    def get(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        use_case = SearchAnimalsUseCase(DjangoAnimalRepository())
        animals = use_case.execute(query)
        return Response(animals)


class AnimalsByClassView(APIView):
    """API endpoint to list animals by class"""
    
    def get(self, request, animal_class):
        use_case = ListAnimalsByClassUseCase(DjangoAnimalRepository())
        animals = use_case.execute(animal_class)
        return Response(animals)


class EndangeredAnimalsView(APIView):
    """API endpoint to list endangered animals"""
    
    def get(self, request):
        use_case = ListEndangeredAnimalsUseCase(DjangoAnimalRepository())
        animals = use_case.execute()
        return Response(animals)


class SessionStartView(APIView):
    """API endpoint to start a session"""
    
    def post(self, request):
        user_id = request.data.get('user_id')
        use_case = StartSessionUseCase(DjangoSessionRepository())
        session = use_case.execute(user_id)
        return Response(session, status=status.HTTP_201_CREATED)


class SessionEndView(APIView):
    """API endpoint to end a session"""
    
    def post(self, request, session_id):
        try:
            use_case = EndSessionUseCase(
                DjangoSessionRepository(),
                DjangoDiscoveryRepository(),
                DjangoAnimalRepository(),
            )
            summary = use_case.execute(session_id)
            return Response(summary)
        except SessionNotFoundException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )


class SessionDiscoveriesView(APIView):
    """API endpoint to get session discoveries"""
    
    def get(self, request, session_id):
        use_case = GetSessionDiscoveriesUseCase(
            DjangoDiscoveryRepository(),
            DjangoAnimalRepository(),
        )
        discoveries = use_case.execute(session_id)
        return Response(discoveries)
