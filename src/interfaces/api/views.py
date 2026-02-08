"""
REST API Views
Provides REST endpoints for animal information and session management.
"""
import random
import subprocess
import threading
import os
import requests
import json
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


# Global YOLO model instance (cached to avoid reloading)
_yolo_model_instance = None

def get_yolo_model():
    """Get or create YOLO model instance (singleton pattern)"""
    global _yolo_model_instance
    if _yolo_model_instance is None:
        from src.infrastructure.ml.recognition import YOLOAnimalRecognition
        _yolo_model_instance = YOLOAnimalRecognition()
    return _yolo_model_instance

# Global variable to track detection process
detection_process = None


class StartDetectionView(APIView):
    """Inicia el script Deteccion.py en un thread separado"""
    
    def post(self, request):
        global detection_process
        
        try:
            # Obtener ruta al script Deteccion.py
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            deteccion_script = os.path.join(project_root, 'Deteccion.py')
            
            if not os.path.exists(deteccion_script):
                return Response({
                    'success': False,
                    'error': f'Script no encontrado en: {deteccion_script}'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Si ya hay un proceso, terminarlo
            if detection_process and detection_process.poll() is None:
                detection_process.terminate()
            
            # Ejecutar Deteccion.py en un thread separado
            def run_detection():
                global detection_process
                # Usar venv python
                venv_python = os.path.join(project_root, 'venv', 'Scripts', 'python.exe')
                if not os.path.exists(venv_python):
                    venv_python = 'python'  # Fallback
                
                detection_process = subprocess.Popen(
                    [venv_python, deteccion_script],
                    cwd=project_root
                )
                detection_process.wait()
            
            thread = threading.Thread(target=run_detection, daemon=True)
            thread.start()
            
            return Response({
                'success': True,
                'message': 'Detección iniciada (Deteccion.py)'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecognizeImageView(APIView):
    """API endpoint to recognize an animal from an uploaded image using best.pt YOLO model"""
    
    def post(self, request):
        image_data = request.data.get('image')
        if not image_data:
            return Response(
                {'success': False, 'error': 'No image provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Import ML utilities
            from src.infrastructure.ml.recognition import YOLOAnimalRecognition
            from src.domain.value_objects import ImageFrame
            from src.infrastructure.storage import get_image_storage
            import logging
            import uuid

            logger = logging.getLogger(__name__)

            # Get cached YOLO model (loads only once)
            model = get_yolo_model()

            # Convert incoming base64 -> ImageFrame and let the model preprocess it
            try:
                frame = ImageFrame.from_base64(image_data)
                decoded_image = model.preprocess_image(frame)
            except Exception as e:
                logger.error(f"Error decoding/preprocessing image: {e}")
                return Response({
                    'success': False,
                    'error': 'Error decoding or preprocessing image'
                }, status=status.HTTP_400_BAD_REQUEST)

            uploaded_image_url = None
            try:
                image_storage = get_image_storage()
                thumbnail_filename = f"upload_{uuid.uuid4().hex}.jpg"
                uploaded_image_url = image_storage.save_thumbnail(frame, thumbnail_filename)
            except Exception as e:
                logger.warning(f"No se pudo guardar la miniatura: {e}")
            
            logger.info("🔍 Procesando imagen con YOLO...")
            
            # Get recognition results from best.pt
            results = model.recognize(decoded_image)
            
            if not results or len(results) == 0:
                logger.warning("⚠️ No animals detected in image")
                return Response({
                    'success': False,
                    'error': 'No animals detected in image'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get best result (highest confidence)
            best_result = max(results, key=lambda r: r.confidence)
            logger.info(f"✅ Detectado: {best_result.animal_name} (conf: {best_result.confidence:.1%})")
            
            # Repository to find animal in database
            repository = DjangoAnimalRepository()

            # Mapping from model label -> probable DB names (ordered candidates)
            MODEL_TO_DB = {
                'bird': ['Bird', 'Ave', 'Pájaro'],
                'cats': ['Gato', 'Cats', 'Cat'],
                'cow': ['Vaca', 'Cow'],
                'deer': ['Venado', 'Deer'],
                'dog': ['Perro', 'Dog'],
                'elephant': ['Elefante', 'Elefante Africano', 'Elephant'],
                'giraffe': ['Jirafa', 'Giraffa', 'Giraffe'],
                'person': ['Persona', 'Person'],
                'pig': ['Cerdo', 'Pig'],
                'sheep': ['Oveja', 'Sheep'],
            }

            # Build ordered candidate names to search in DB
            candidates = []
            model_label = (best_result.animal_name or '').strip()
            key = model_label.lower()
            if key in MODEL_TO_DB:
                candidates.extend(MODEL_TO_DB[key])
            # Always try the original model label as well
            candidates.append(model_label)

            # Deduplicate preserving order (case-insensitive)
            seen = set()
            uniq_candidates = []
            for c in candidates:
                if not c:
                    continue
                lc = c.lower()
                if lc in seen:
                    continue
                seen.add(lc)
                uniq_candidates.append(c)

            found_animal = None

            # Strategy 1: Try exact match on name and aliases (case-insensitive)
            # This is the safest approach and avoids false positives from substring matches in scientific_name
            animals = repository.get_all()
            for c in uniq_candidates:
                # Try exact match on name
                for animal in animals:
                    if animal.name.lower() == c.lower():
                        found_animal = animal
                        logger.info(f"🎯 Animal encontrado por nombre exacto: {animal.name} (candidato: {c})")
                        break
                if found_animal:
                    break
                
                # Try exact match on aliases
                for animal in animals:
                    aliases = getattr(animal, 'aliases', None) or []
                    for alias in aliases:
                        if alias and alias.lower() == c.lower():
                            found_animal = animal
                            logger.info(f"🎯 Animal encontrado por alias exacto: {animal.name} (alias: {alias})")
                            break
                    if found_animal:
                        break
                if found_animal:
                    break

            # Strategy 2 (fallback): Partial substring match on name and aliases ONLY
            # Avoid scientific_name to prevent false positives like "cat" matching "truncatus"
            if not found_animal:
                logger.info(f"🔎 Buscando coincidencia parcial en nombre y aliases para: {best_result.animal_name}")
                for animal in animals:
                    # Check name partial matches
                    if model_label.lower() in animal.name.lower() or animal.name.lower() in model_label.lower():
                        found_animal = animal
                        logger.info(f"🎯 Coincidencia parcial en nombre: {animal.name}")
                        break
                    # Check aliases (if present)
                    aliases = getattr(animal, 'aliases', None) or []
                    for alias in aliases:
                        if alias and (model_label.lower() in alias.lower() or alias.lower() in model_label.lower()):
                            found_animal = animal
                            logger.info(f"🎯 Coincidencia parcial en alias: {animal.name} (alias: {alias})")
                            break
                    if found_animal:
                        break

            # If still not found, generate animal data with AI but DO NOT save to DB
            if not found_animal:
                logger.warning(f"❌ Animal '{best_result.animal_name}' no encontrado en BD tras búsqueda")
                logger.info(f"🤖 Generando datos automáticos con IA para: {best_result.animal_name} (NO se guardarán en BD)")

                try:
                    ai_data = self._generate_description_with_ai(best_result.animal_name)
                except Exception as e:
                    logger.error(f"Error generating AI data: {e}")
                    ai_data = self._get_fallback_data(best_result.animal_name)

                # Normalize diet and conservation for display
                diet_map = {
                    'CARNIVORE': 'Carnívoro',
                    'HERBIVORE': 'Herbívoro',
                    'OMNIVORE': 'Omnívoro',
                    'PISCIVORE': 'Piscívoro',
                }
                conservation_map = {
                    'LEAST_CONCERN': 'Preocupación menor',
                    'NEAR_THREATENED': 'Casi amenazado',
                    'VULNERABLE': 'Vulnerable',
                    'ENDANGERED': 'En peligro',
                    'CRITICALLY_ENDANGERED': 'En peligro crítico',
                    'EXTINCT': 'Extinto',
                }

                # Map common name to Spanish when YOLO label is English
                name_map_es = {
                    'Bird': 'Ave',
                    'Cats': 'Gato',
                    'Cow': 'Vaca',
                    'Deer': 'Ciervo',
                    'Dog': 'Perro',
                    'Elephant': 'Elefante',
                    'Giraffe': 'Jirafa',
                    'Person': 'Persona',
                    'Pig': 'Cerdo',
                    'Sheep': 'Oveja',
                }
                # Optional scientific name hints for common YOLO classes
                scientific_hint = {
                    'Deer': 'Cervus elaphus',
                    'Cow': 'Bos taurus',
                    'Pig': 'Sus scrofa domesticus',
                    'Sheep': 'Ovis aries',
                    'Dog': 'Canis lupus familiaris',
                    'Cats': 'Felis catus',
                    'Elephant': 'Loxodonta africana',
                    'Giraffe': 'Giraffa camelopardalis',
                    'Person': 'Homo sapiens',
                    'Bird': 'Aves',
                }

                raw_diet = ai_data.get('diet', 'Omnívoro')
                raw_conservation = ai_data.get('conservation_status', 'Preocupación menor')

                diet_key = str(raw_diet).strip().upper()
                conservation_key = str(raw_conservation).strip().upper()

                diet_display = diet_map.get(diet_key, raw_diet)
                conservation_display = conservation_map.get(conservation_key, raw_conservation)

                # Normalize name and scientific name for Spanish display
                display_name = name_map_es.get(best_result.animal_name, best_result.animal_name)
                raw_scientific = ai_data.get('scientific_name')
                scientific_lower = str(raw_scientific).strip().lower() if raw_scientific else ''
                invalid_scientific = not raw_scientific or scientific_lower in {
                    best_result.animal_name.lower(),
                    display_name.lower(),
                    'cervidae'
                }
                if invalid_scientific and best_result.animal_name in scientific_hint:
                    scientific_name = scientific_hint[best_result.animal_name]
                else:
                    scientific_name = raw_scientific or f"Unknown ({best_result.animal_name})"

                # Build animal_dict and persist in DB
                try:
                    from src.infrastructure.persistence.models import AnimalModel
                    import uuid

                    # Map diet/conservation to DB expected values
                    diet_reverse = {
                        'Carnívoro': 'CARNIVORE',
                        'Herbívoro': 'HERBIVORE',
                        'Omnívoro': 'OMNIVORE',
                        'Piscívoro': 'PISCIVORE',
                    }
                    conservation_reverse = {
                        'Preocupación menor': 'LEAST_CONCERN',
                        'Casi amenazado': 'NEAR_THREATENED',
                        'Vulnerable': 'VULNERABLE',
                        'En peligro': 'ENDANGERED',
                        'En peligro crítico': 'CRITICALLY_ENDANGERED',
                        'Extinto': 'EXTINCT',
                    }

                    db_diet = diet_reverse.get(diet_display, 'OMNIVORE')
                    db_conservation = conservation_reverse.get(conservation_display, 'LEAST_CONCERN')

                    from django.db import IntegrityError

                    created_by = request.user if request.user and request.user.is_authenticated else None

                    existing_animal = AnimalModel.objects.filter(name=display_name).first()
                    if existing_animal:
                        found_animal = existing_animal
                        logger.info(f"🟡 Animal ya existe en BD: {existing_animal.name}")
                    else:
                        try:
                            new_animal = AnimalModel.objects.create(
                                id=str(uuid.uuid4()),
                                name=display_name,
                                scientific_name=scientific_name,
                                description=ai_data.get('description', f"{display_name} es un animal interesante."),
                                animal_class=ai_data.get('animal_class', 'MAMMAL'),
                                habitat=ai_data.get('habitat', 'Desconocido'),
                                diet=db_diet,
                                conservation_status=db_conservation,
                                fun_facts=ai_data.get('fun_facts', []),
                                average_lifespan=ai_data.get('average_lifespan', 'Desconocido'),
                                average_weight=ai_data.get('average_weight', 'Desconocido'),
                                geographic_distribution=ai_data.get('geographic_distribution', 'Desconocido'),
                                aliases=[best_result.animal_name, display_name],
                                image_url=uploaded_image_url,
                                created_by=created_by,
                            )
                            found_animal = new_animal
                            logger.info(f"✨ Nuevo animal agregado a BD con datos IA: {new_animal.name}")
                        except IntegrityError:
                            # If another request created it first, load existing record
                            found_animal = AnimalModel.objects.filter(name=display_name).first()
                            if found_animal:
                                logger.info(f"🟡 Animal creado en paralelo, usando existente: {found_animal.name}")
                            else:
                                raise
                except Exception as e:
                    logger.error(f"Error creando animal en BD: {e}")
                    import traceback as tb
                    logger.error(f"Traceback: {tb.format_exc()}")
                    return Response({
                        'success': False,
                        'error': f"Animal detected as '{best_result.animal_name}' but could not create it: {str(e)}"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Handle both persisted animals (found_animal is object) and AI-generated (found_animal is None)
            if found_animal is not None:
                logger.info(f"📊 Retornando resultado: {found_animal.name} ({best_result.confidence:.1%})")
                
                # Obtener el modelo Django para actualizar
                from src.infrastructure.persistence.models import AnimalModel
                try:
                    animal_model = AnimalModel.objects.get(id=found_animal.id)
                    
                    if (
                        uploaded_image_url
                        and getattr(animal_model, 'image_url', None) in (None, '')
                        and request.user
                        and request.user.is_authenticated
                        and getattr(animal_model, 'created_by_id', None) == request.user.id
                    ):
                        animal_model.image_url = uploaded_image_url
                    
                    # Actualizar confianza del último reconocimiento
                    animal_model.last_recognition_confidence = float(best_result.confidence)
                    animal_model.save(update_fields=['last_recognition_confidence', 'updated_at', 'image_url'])
                except AnimalModel.DoesNotExist:
                    logger.warning(f"⚠️ Animal {found_animal.id} no encontrado en BD para actualizar")
                
                # Serialize response from database
                try:
                    animal_dict = found_animal.to_dict()
                except Exception as e:
                    logger.error(f"Error serializing animal to dict: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    animal_dict = {
                        'id': str(found_animal.id),
                        'name': found_animal.name,
                        'scientific_name': found_animal.scientific_name,
                        'description': found_animal.description,
                        'animal_class': found_animal.animal_class,
                        'habitat': found_animal.habitat,
                        'diet': found_animal.diet,
                        'conservation_status': found_animal.conservation_status,
                        'fun_facts': found_animal.fun_facts or [],
                    }
            else:
                # found_animal is None, use animal_dict already built from AI data
                logger.info(f"📊 Retornando resultado generado por IA: {animal_dict.get('name')} ({best_result.confidence:.1%})")
            
            return Response({
                'success': True,
                'animal': animal_dict,
                'recognition': {
                    'animal_name': best_result.animal_name,
                    'confidence': float(best_result.confidence),
                }
            })
            
        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            tb_lines = traceback.format_exc()
            logger.error(f"❌ Error en reconocimiento: {repr(e)}")
            logger.error(f"Error string: {str(e)}")
            logger.error(f"Traceback completo:\n{tb_lines}")
            traceback.print_exc()
            print(f"DEBUG: Error type={type(e).__name__}, repr={repr(e)}, str={str(e)}")
            return Response({
                'success': False,
                'error': f'Recognition failed: {repr(e)} - {tb_lines[-200:]}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _generate_description_with_ai(self, animal_name: str) -> dict:
        """Generate complete animal data for unknown animal using OpenRouter"""
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Try to get key from environment, fallback to hardcoded
        api_key = os.environ.get('OPENROUTER_API_KEY') or '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'
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        prompt = f"""IMPORTANTE: Solo genera datos del animal "{animal_name}". No confundas con otros animales.

Genera TODOS los datos científicos del animal {animal_name} en formato JSON.

RESPONDE EN JSON CON ESTA ESTRUCTURA (sin markdown, solo JSON puro):
{{
    "description": "Descripción de 2-3 oraciones sobre {animal_name}",
    "scientific_name": "Nombre científico del {animal_name}",
    "habitat": "Hábitat principal donde vive",
    "diet": "Carnívoro o Herbívoro o Omnívoro o Piscívoro",
    "conservation_status": "Preocupación menor, Casi amenazado, Vulnerable, En peligro, En peligro crítico o Extinto",
    "average_lifespan": "Esperanza de vida en años (ej: '15-20 años')",
    "average_weight": "Peso promedio (ej: '500 kg' o '2.5 kg')",
    "geographic_distribution": "Distribución geográfica principal",
    "fun_facts": ["Dato curioso 1", "Dato curioso 2", "Dato curioso 3"]
}}

REGLAS CRÍTICAS:
1. TODOS los datos deben ser ÚNICAMENTE del animal "{animal_name}"
2. El campo 'diet' DEBE SER uno de estos valores exactamente: Carnívoro, Herbívoro, Omnívoro, Piscívoro
3. El campo 'conservation_status' DEBE SER uno de estos: Preocupación menor, Casi amenazado, Vulnerable, En peligro, En peligro crítico, Extinto
4. NO inventes datos. Si no estás seguro de algún campo, usa "Desconocido".
5. En "geographic_distribution" no incluyas continentes o países erróneos. Si no estás seguro, usa "Desconocido".
6. La descripción debe ser de 2-3 oraciones en español
7. Los fun_facts deben ser en español
8. Responde SOLO con el JSON válido, sin explicaciones adicionales
9. El JSON debe ser parseable sin errores"""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            "temperature": 0.7,
            "max_tokens": 800,
        }
        
        try:
            r = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=20)
            r.raise_for_status()
            body = r.json()
            
            # Parse response
            if isinstance(body, dict):
                choices = body.get('choices') or body.get('outputs')
                if choices and isinstance(choices, list):
                    first = choices[0]
                    msg = first.get('message') or first.get('output') or first
                    if isinstance(msg, dict):
                        content = msg.get('content') or msg.get('text') or msg.get('output_text')
                        if isinstance(content, dict):
                            text = content.get('text')
                        else:
                            text = content
                        if not text:
                            text = first.get('text') or first.get('output_text')
                    else:
                        text = str(msg)
                    
                    if text:
                        # Try to parse JSON from response
                        try:
                            # Clean up the response (remove markdown code blocks if present)
                            text = text.strip()
                            if text.startswith('```json'):
                                text = text[7:]
                            if text.startswith('```'):
                                text = text[3:]
                            if text.endswith('```'):
                                text = text[:-3]
                            text = text.strip()
                            
                            data = json.loads(text)
                            logger.info(f"✨ Datos completos generados con IA para {animal_name}")
                            return data
                        except json.JSONDecodeError as e:
                            logger.warning(f"⚠️ Error parseando JSON: {e}, text={text[:100]}")
                            return self._get_fallback_data(animal_name)
            
            return self._get_fallback_data(animal_name)
        except Exception as e:
            logger.warning(f"⚠️ Error generando datos con IA: {e}")
            return self._get_fallback_data(animal_name)
    
    def _get_fallback_data(self, animal_name: str) -> dict:
        """Return fallback data when AI generation fails"""
        return {
            "description": f"{animal_name} es un animal fascinante del reino animal.",
            "scientific_name": f"Unknown ({animal_name})",
            "habitat": "Desconocido",
            "diet": "OMNIVORE",
            "conservation_status": "NOT_EVALUATED",
            "average_lifespan": "Desconocido",
            "average_weight": "Desconocido",
            "geographic_distribution": "Desconocido",
            "fun_facts": [f"{animal_name} es una especie animal interesante"]
        }


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
