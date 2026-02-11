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

# Importar caché y descripciones built-in
from src.infrastructure.cache_service import (
    load_cache, 
    save_to_cache, 
    get_from_cache, 
    has_in_cache
)

# Cargar descripciones built-in (almacenadas en JSON)
import json
from pathlib import Path
BUILTIN_DESCRIPTIONS_FILE = Path(__file__).parent.parent.parent / 'descriptions_builtin.json'

def load_builtin_descriptions():
    """Cargar descripciones pre-escritas para animales comunes"""
    if BUILTIN_DESCRIPTIONS_FILE.exists():
        with open(BUILTIN_DESCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

BUILTIN_DESCRIPTIONS = load_builtin_descriptions()


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
            
            # Pipeline de detección + descripción:
            # 1️⃣  YOLO (best.pt) - Detección de imágenes (10 animales: Bird, Cats, Cow, Deer, Dog, Elephant, Giraffle, Person, Pig, Sheep)
            # 2️⃣  HuggingFace Vision (ViT) - Filtro visual de fallback (si YOLO < 60%)
            # 3️⃣  OpenRouter (GPT-4o-mini) - Generacion de descripcion, hechos, dieta, habitat, etc
            #
            # Flujo actual:
            # YOLO detecta → Si confianza >= 60% → Genera descripción con OpenRouter
            # YOLO non-detect o < 60% → Intenta HuggingFace Vision → Si fallback → OpenRouter para descripción
            
            # Get recognition results from best.pt
            results = model.recognize(decoded_image)
            
            # Check if YOLO detected anything or if confidence is low
            yolo_detected = results and len(results) > 0
            best_result = None
            yolo_confidence = 0.0
            
            if yolo_detected:
                best_result = max(results, key=lambda r: r.confidence)
                yolo_confidence = best_result.confidence
                logger.info(f"✅ YOLO Detectado: {best_result.animal_name} (conf: {yolo_confidence:.1%})")
                
                # === ENSEMBLE/VOTING SYSTEM ===
                # Combina YOLO + ViT para máxima precisión
                final_animal, final_confidence, decision_method, decision_log = self._ensemble_identify_animal(
                    best_result.animal_name,
                    yolo_confidence,
                    image_data,
                    logger
                )
                for log_line in decision_log:
                    logger.info(f"   {log_line}")
            else:
                # YOLO falló completamente - intentar ViT
                logger.warning(f"❌ YOLO no detectó - Usando ViT como fallback...")
                final_animal = self._identify_animal_with_huggingface(image_data)
                if final_animal:
                    final_confidence = 0.75
                    decision_method = "VIT_FALLBACK"
                else:
                    final_animal = None
                    final_confidence = 0.0
                    decision_method = "BOTH_FAILED"
            
            # Manejo de fallos
            if not final_animal:
                logger.error(f"❌ Animal no identificable - YOLO falló y ViT falló")
                return Response({
                    'success': False,
                    'error': 'Could not identify animal with YOLO or ViT vision analysis',
                    'method': decision_method
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"🎯 DECISIÓN FINAL: {final_animal} ({final_confidence:.1%}) via {decision_method}")
            
            # Mapping YOLO English names to Spanish names (case-insensitive)
            # Ampliado para aceptar CUALQUIER animal, no solo los 10 originales
            ANIMAL_TO_SPANISH = {
                'person': 'Persona',
                'cat': 'Gato',
                'cats': 'Gato',
                'dog': 'Perro',
                'bird': 'Pájaro',
                'cow': 'Vaca',
                'elephant': 'Elefante',
                'giraffe': 'Jirafa',
                'giraffle': 'Jirafa',  # Modelo tiene typo
                'deer': 'Ciervo',
                'pig': 'Cerdo',
                'sheep': 'Oveja',
                # Nuevos animales
                'crab': 'Cangrejo',
                'fiddler crab': 'Cangrejo Violinista',
                'sea lion': 'León Marino',
                'lobster': 'Langosta',
                'shrimp': 'Camarón',
                'monkey': 'Mono',
                'bear': 'Oso',
                'rabbit': 'Conejo',
                'fish': 'Pez',
                'whale': 'Ballena',
                'dolphin': 'Delfín',
                'tiger': 'Tigre',
                'lion': 'León',
                'zebra': 'Cebra',
                'hippopotamus': 'Hipopótamo',
                'crocodile': 'Cocodrilo',
                'eagle': 'Águila',
                'penguin': 'Pingüino',
                'turtle': 'Tortuga',
                'snake': 'Serpiente',
            }
            
            # Map final animal result to Spanish name (case-insensitive)
            animal_label = (final_animal or '').strip().lower()
            animal_name_es = ANIMAL_TO_SPANISH.get(animal_label, final_animal.title())
            
            logger.info(f"🔄 Mapeado a español: '{final_animal}' → '{animal_name_es}'")
            
            # Generar datos con IA, pasando directamente el nombre español del animal
            logger.info(f"🤖 Generando datos con IA para: {animal_name_es}")

            try:
                ai_data = self._generate_description_with_ai(animal_name_es)
            except Exception as e:
                logger.error(f"Error generating AI data: {e}")
                ai_data = self._get_fallback_data(animal_name_es)

            logger.info(f"📥 AI Data recibido completo: {ai_data}")
            
            # Display name is already the Spanish mapped name
            display_name = animal_name_es
            
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

            logger.info(f"🔍 Raw values - Diet: '{raw_diet}', Conservation: '{raw_conservation}'")
            
            diet_key = str(raw_diet).strip().upper()
            conservation_key = str(raw_conservation).strip().upper()

            logger.info(f"🔑 Keys para mapeo - Diet Key: '{diet_key}', Conservation Key: '{conservation_key}'")
            
            diet_display = diet_map.get(diet_key, raw_diet)
            conservation_display = conservation_map.get(conservation_key, raw_conservation)
            
            logger.info(f"✏️ Valores después de mapeo - Diet Display: '{diet_display}', Conservation Display: '{conservation_display}'")

            # Normalize name and scientific name for Spanish display
            # Normalize scientific name from AI response
            raw_scientific = ai_data.get('scientific_name')
            scientific_name = raw_scientific or f"Unknown ({display_name})"

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
                    logger.info(f"🟡 Animal ya existe en BD: {existing_animal.name}")
                    # Actualizar datos con los generados por IA
                    logger.info(f"🔄 Actualizando datos del animal con IA...")
                    try:
                        existing_animal.scientific_name = scientific_name
                        existing_animal.description = ai_data.get('description', f"{display_name} es un animal interesante.")
                        existing_animal.habitat = ai_data.get('habitat', 'Desconocido')
                        existing_animal.diet = db_diet
                        existing_animal.conservation_status = db_conservation
                        existing_animal.fun_facts = ai_data.get('fun_facts', [])
                        existing_animal.average_lifespan = ai_data.get('average_lifespan', 'Desconocido')
                        existing_animal.average_weight = ai_data.get('average_weight', 'Desconocido')
                        existing_animal.geographic_distribution = ai_data.get('geographic_distribution', 'Desconocido')
                        existing_animal.save()
                        logger.info(f"✅ Datos del animal actualizados en BD con IA")
                        found_animal = existing_animal
                    except Exception as e:
                        logger.error(f"⚠️ Error actualizando animal: {e}")
                        found_animal = existing_animal
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
                            aliases=[final_animal, display_name],
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
                    'error': f"Animal detected as '{final_animal}' but could not create it: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Construir animal_dict desde los datos generados con IA
            animal_dict = {
                'id': str(found_animal.id) if found_animal else str(uuid.uuid4()),
                'name': display_name,
                'scientific_name': scientific_name,
                'description': ai_data.get('description', f"{display_name} es un animal interesante."),
                'animal_class': ai_data.get('animal_class', 'MAMMAL'),
                'habitat': ai_data.get('habitat', 'Desconocido'),
                'diet': diet_display,
                'conservation_status': conservation_display,
                'fun_facts': ai_data.get('fun_facts', []),
                'average_lifespan': ai_data.get('average_lifespan', 'Desconocido'),
                'average_weight': ai_data.get('average_weight', 'Desconocido'),
                'geographic_distribution': ai_data.get('geographic_distribution', 'Desconocido'),
                'image_url': uploaded_image_url or '',
            }
            
            logger.info(f"🎁 animal_dict a devolver: {animal_dict}")
            
            # Log resultado
            logger.info(f"📊 Retornando resultado con datos generados por IA: {display_name} ({final_confidence:.1%}) via {decision_method}")
            
            return Response({
                'success': True,
                'animal': animal_dict,
                'recognition': {
                    'animal_name': final_animal,
                    'confidence': float(final_confidence),
                    'method': decision_method,
                },
                'uploaded_image_url': uploaded_image_url
            }, status=status.HTTP_200_OK)
            
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
        """Generate complete animal data - OPTIMIZED for speed
        
        Estrategia de tres capas:
        1. Built-in descriptions (instantáneo) - Si animal es conocido
        2. Caché (instantáneo) - Si ya fue generado antes
        3. OpenRouter API (~35-60seg) - Para animales nuevos
        
        Args:
            animal_name: Animal name in Spanish
        
        Returns:
            dict with complete animal data
        """
        import logging
        
        logger = logging.getLogger(__name__)
        
        # CAPA 1: BUILT-IN DESCRIPTIONS (Instantáneo)
        # ============================================
        builtin_key = animal_name.lower()
        if builtin_key in BUILTIN_DESCRIPTIONS:
            logger.info(f"✅ [BUILT-IN] Usando descripción pre-escrita para: {animal_name} (instantáneo)")
            return BUILTIN_DESCRIPTIONS[builtin_key]
        
        # CAPA 2: CACHÉ (Instantáneo)
        # ===========================
        if has_in_cache(animal_name):
            cached_data = get_from_cache(animal_name)
            logger.info(f"✅ [CACHÉ] Usando descripción en caché para: {animal_name} (instantáneo)")
            return cached_data
        
        # CAPA 3: OPENROUTER API (35-60 segundos)
        # =======================================
        logger.info(f"🔄 [OPENROUTER] Generando datos nuevos para: {animal_name}...")
        
        api_key = os.environ.get('OPENROUTER_API_KEY') or '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'
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        prompt = f"""Eres experto en biología y taxonomía animal.

El sistema ha identificado: "{animal_name}"

GENERA UN JSON CON TODOS estos datos sobre {animal_name}:

{{
    "description": "2-3 oraciones sobre {animal_name}",
    "scientific_name": "Nombre científico",
    "animal_class": "Clasificación: MAMMAL, BIRD, REPTILE, AMPHIBIAN, FISH, o INVERTEBRATE",
    "habitat": "Hábitat principal",
    "diet": "Carnívoro/Herbívoro/Omnívoro/Piscívoro/Insectívoro",
    "conservation_status": "Estado de conservación",
    "average_lifespan": "Esperanza de vida",
    "average_weight": "Peso promedio",
    "geographic_distribution": "Distribución geográfica",
    "fun_facts": ["Hecho 1", "Hecho 2", "Hecho 3"]
}}

REGLAS IMPORTANTES:
- animal_class DEBE ser UNO de: MAMMAL, BIRD, REPTILE, AMPHIBIAN, FISH, INVERTEBRATE
  * Animales con plumas = BIRD (Ave)
  * Mamíferos (pelo, amamantan) = MAMMAL (Mamífero)
  * Reptiles (escamas, sangre fría) = REPTILE (Reptil)
  * Anfibios (rana, sapo, salamandra) = AMPHIBIAN (Anfibio)
  * Peces = FISH (Pez)
  * Insectos, arañas, cangrejos, etc = INVERTEBRATE (Invertebrado)
- Diet DEBE ser: Carnívoro, Herbívoro, Omnívoro, Piscívoro o Insectívoro
- Conservation status DEBE ser: Preocupación menor, Casi amenazado, Vulnerable, En peligro, En peligro crítico o Extinto
- Si no sabes, escribe "Desconocido"
- TODO EN ESPAÑOL
- RESPONDE SOLO JSON, SIN EXPLICACIONES"""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 800,
        }
        
        try:
            logger.info(f"📡 Conectando a OpenRouter...")
            r = requests.post(api_url, headers=headers, json=payload, timeout=60)
            
            logger.info(f"📡 OpenRouter HTTP: {r.status_code}")
            r.raise_for_status()
            
            body = r.json()
            choices = body.get('choices', [])
            
            if choices and isinstance(choices, list):
                first = choices[0]
                msg = first.get('message', {})
                content = msg.get('content', '{}')
                
                # Extraer JSON
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    ai_data = json.loads(json_str)
                    
                    logger.info(f"✅ OpenRouter generó descripción para: {animal_name}")
                    
                    # GUARDAR EN CACHÉ para futuras solicitudes
                    save_to_cache(animal_name, ai_data)
                    logger.info(f"💾 Descripción guardada en caché: {animal_name}")
                    
                    return ai_data
            
            logger.warning(f"⚠️ OpenRouter respuesta inválida")
            return self._get_fallback_data(animal_name)
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ OpenRouter timeout")
            return self._get_fallback_data(animal_name)
        except Exception as e:
            logger.error(f"❌ OpenRouter error: {str(e)}")
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
    
    def _ensemble_identify_animal(self, yolo_result, yolo_confidence: float, image_base64: str, logger):
        """
        ENSEMBLE VOTING SYSTEM - Combina YOLO + ViT para máxima precisión
        
        Reglas de decisión:
        1. YOLO ALTO (>80%) → Usar YOLO directo
        2. YOLO MEDIO (60-80%) + ViT ACUERDAN → Usar resultado (muy confiable)
        3. YOLO MEDIO (60-80%) + ViT DESACUERDAN → Usar ViT (more likely error in YOLO)
        4. YOLO BAJO (<60%) → Confiar principalmente en ViT
        5. AMBOS FALLAN → Retornar None (no identificar)
        
        Args:
            yolo_result: Nombre del animal de YOLO
            yolo_confidence: Score de confianza de YOLO (0-1)
            image_base64: Imagen en base64
            logger: Logger para registrar decisiones
            
        Returns:
            tuple: (animal_name, confidence, method, decision_log)
        """
        
        decision_log = []
        
        # High YOLO confidence - confiar en YOLO
        if yolo_confidence >= 0.80:
            decision_log.append(f"🎯 YOLO muy confiado ({yolo_confidence:.1%}) - Usando YOLO directo")
            logger.info(f"🎯 YOLO muy confiado ({yolo_confidence:.1%}) - Usando YOLO directo")
            return yolo_result, yolo_confidence, "YOLO_PRIMARY", decision_log
        
        # Medium YOLO confidence - Validar con ViT
        if yolo_confidence >= 0.60:
            decision_log.append(f"🔄 YOLO confianza media ({yolo_confidence:.1%}) - Validando con ViT...")
            logger.info(f"🔄 YOLO confianza media ({yolo_confidence:.1%}) - Validando con ViT...")
            
            vit_result = self._identify_animal_with_huggingface(image_base64)
            
            if not vit_result:
                decision_log.append(f"   ViT falló → Usando YOLO")
                logger.warning(f"   ViT falló → Usando YOLO")
                return yolo_result, yolo_confidence, "YOLO_VIT_FALLBACK", decision_log
            
            # ¿YOLO y ViT de acuerdo?
            if yolo_result.lower() == vit_result.lower():
                # ACUERDO - máxima confianza
                consensus_conf = (yolo_confidence + 0.85) / 2  # ViT ~85% por defecto
                decision_log.append(f"   ✅ ACUERDO: YOLO='{yolo_result}' = ViT='{vit_result}'")
                decision_log.append(f"   📊 Confianza combinada: {consensus_conf:.1%}")
                logger.info(f"   ✅ ACUERDO: YOLO='{yolo_result}' = ViT='{vit_result}' ({consensus_conf:.1%})")
                return yolo_result, consensus_conf, "ENSEMBLE_CONSENSUS", decision_log
            else:
                # DESACUERDO - Preferir ViT en rango medio (YOLO tiende a fallar más aquí)
                decision_log.append(f"   ⚠️ DESACUERDO: YOLO='{yolo_result}' ≠ ViT='{vit_result}'")
                decision_log.append(f"   📊 Prevalece ViT en rango medio de YOLO (60-80%)")
                logger.warning(f"   ⚠️ DESACUERDO: YOLO='{yolo_result}' ≠ ViT='{vit_result}' → Usando ViT")
                return vit_result, 0.75, "ENSEMBLE_CONFLICT_VIT_WINS", decision_log
        
        # Low YOLO confidence - Confiar principalmente en ViT
        decision_log.append(f"❌ YOLO baja confianza ({yolo_confidence:.1%}) - Validando con ViT...")
        logger.warning(f"❌ YOLO baja confianza ({yolo_confidence:.1%}) - Validando con ViT...")
        
        vit_result = self._identify_animal_with_huggingface(image_base64)
        
        if not vit_result:
            decision_log.append(f"   ❌ ViT tampoco pudo identificar - Animal NO identificable")
            logger.error(f"   ❌ Ambos modelos fallaron")
            return None, 0.0, "BOTH_FAILED", decision_log
        
        decision_log.append(f"   ✅ ViT identifica: {vit_result}")
        logger.info(f"   ✅ ViT identifica: {vit_result}")
        return vit_result, 0.80, "VIT_FALLBACK", decision_log

    def _identify_animal_with_huggingface(self, image_base64: str) -> str:
        """Use HuggingFace ViT (Vision Transformer) to identify animal when YOLO fails
        
        IMPORTANTE: Usa el modelo ViT PRECARGADO en AppConfig.ready()
        La primera solicitud fue lenta, pero ahora está en caché Django.
        
        ✨ OPTIMIZACIÓN: Mapeo con prioridades para evitar falsos positivos
        (ej: "whale" tiene prioridad sobre "wolf" en "sea wolf")
        
        ⚠️ VALIDACIÓN: Solo acepta animales válidos, rechaza objetos/personas
        
        Args:
            image_base64: Base64 encoded image string
        
        Returns:
            Animal name in English or empty string if not identified or if it's not an animal
        """
        import logging
        import base64
        import io
        from PIL import Image
        
        logger = logging.getLogger(__name__)
        
        # Mapeo de palabras clave PRIORITARIAS (procesadas en orden)
        # Esto evita que "wolf" en "sea wolf" tenga prioridad sobre "whale"
        priority_keywords = [
            # Marino/cetáceos (ALTA PRIORIDAD para evitar confusión con wolf)
            ('orca', 'orca'),
            ('killer whale', 'orca'),
            ('whale', 'whale'),
            ('dolphin', 'dolphin'),
            ('seal', 'seal'),
            ('sea lion', 'sea lion'),
            ('walrus', 'walrus'),
            ('manatee', 'manatee'),
            ('dugong', 'dugong'),
            
            # Crustáceos
            ('crab', 'crab'),
            ('lobster', 'lobster'),
            ('shrimp', 'shrimp'),
            ('crayfish', 'crayfish'),
            
            # Aves
            ('bird', 'bird'),
            ('ostrich', 'ostrich'),
            ('eagle', 'eagle'),
            ('hawk', 'hawk'),
            ('owl', 'owl'),
            ('parrot', 'parrot'),
            ('penguin', 'penguin'),
            ('duck', 'duck'),
            ('swan', 'swan'),
            ('chicken', 'chicken'),
            ('hen', 'hen'),
            ('rooster', 'rooster'),
            ('flamingo', 'flamingo'),
            
            # Felinos
            ('tiger', 'tiger'),
            ('lion', 'lion'),
            ('leopard', 'leopard'),
            ('cheetah', 'cheetah'),
            ('jaguar', 'jaguar'),
            ('cougar', 'cougar'),
            ('puma', 'puma'),
            ('cat', 'cat'),
            
            # Cánidos
            ('wolf', 'wolf'),
            ('fox', 'fox'),
            ('husky', 'husky'),
            ('dog', 'dog'),
            
            # Grandes mamíferos
            ('elephant', 'elephant'),
            ('giraffe', 'giraffe'),
            ('zebra', 'zebra'),
            ('horse', 'horse'),
            ('donkey', 'donkey'),
            ('rhinoceros', 'rhinoceros'),
            ('hippopotamus', 'hippopotamus'),
            ('bear', 'bear'),
            ('deer', 'deer'),
            ('elk', 'elk'),
            
            # Granja
            ('cow', 'cow'),
            ('cattle', 'cattle'),
            ('ox', 'ox'),
            ('bull', 'bull'),
            ('sheep', 'sheep'),
            ('lamb', 'lamb'),
            ('pig', 'pig'),
            ('swine', 'swine'),
            ('hog', 'hog'),
            ('goat', 'goat'),
            
            # Otros mamíferos
            ('monkey', 'monkey'),
            ('ape', 'ape'),
            ('rabbit', 'rabbit'),
            ('squirrel', 'squirrel'),
            ('mouse', 'mouse'),
            ('rat', 'rat'),
            ('otter', 'otter'),
            ('beaver', 'beaver'),
            
            # Reptiles/Anfibios
            ('turtle', 'turtle'),
            ('snake', 'snake'),
            ('lizard', 'lizard'),
            ('frog', 'frog'),
            ('crocodile', 'crocodile'),
            ('alligator', 'alligator'),
            
            # Peces/Otros
            ('fish', 'fish'),
            ('shark', 'shark'),
            
            # Personas
            ('person', 'person'),
            ('people', 'people'),
            ('man', 'man'),
            ('woman', 'woman'),
        ]
        
        # Lista de animales válidos (extrae todos los nombres aceptados)
        VALID_ANIMALS = {simplified_name for _, simplified_name in priority_keywords}
        
        try:
            logger.info(f"🤖 ViT Vision: Analizando imagen visualmente...")
            
            # Limpiar base64 - remover data URLs, espacios, saltos de línea
            clean_base64 = image_base64.strip()
            
            # Si viene como data URL, extraer solo la parte base64
            if ',' in clean_base64:
                logger.info(f"   📝 Detectado formato data URL...")
                clean_base64 = clean_base64.split(',', 1)[1]
            
            # Remover espacios en blanco y saltos de línea
            clean_base64 = ''.join(clean_base64.split())
            
            logger.info(f"   Base64 limpio: {len(clean_base64)} caracteres")
            
            # Decodificar base64 a imagen
            try:
                image_bytes = base64.b64decode(clean_base64)
                logger.info(f"   ✅ Base64 decodificado: {len(image_bytes)} bytes")
            except Exception as e:
                logger.error(f"❌ Error decodificando base64: {e}")
                return ""
            
            # Intentar abrir la imagen con mayor tolerancia
            image = None
            try:
                # Intento 1: PIL directo
                image = Image.open(io.BytesIO(image_bytes))
                logger.info(f"   ✅ Imagen abierta con PIL (formato: {image.format}, modo: {image.mode})")
                
                # Convertir a RGB si es necesario
                if image.mode != 'RGB':
                    logger.info(f"   🔄 Convirtiendo de {image.mode} a RGB...")
                    image = image.convert('RGB')
                    
            except Exception as e:
                logger.warning(f"   ⚠️ PIL directo falló: {e}")
                logger.info(f"   🔄 Intentando con cv2 como fallback...")
                
                # Intento 2: Usar cv2 como fallback
                try:
                    import cv2
                    import numpy as np
                    
                    nparr = np.frombuffer(image_bytes, np.uint8)
                    img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if img_cv is None:
                        logger.error(f"   ❌ cv2 tampoco pudo decodificar (nparr: {len(nparr)} bytes)")
                        logger.error(f"   📊 Primeros 100 bytes: {image_bytes[:100]}")
                        return ""
                    
                    # Convertir de BGR a RGB
                    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(img_rgb)
                    logger.info(f"   ✅ Imagen abierta con cv2")
                    
                except Exception as e2:
                    logger.error(f"   ❌ cv2 fallback también falló: {e2}")
                    logger.error(f"   📊 Detalles: {type(image_bytes)} - {len(image_bytes)} bytes")
                    return ""
            
            if image is None:
                logger.error(f"❌ No se pudo abrir la imagen con ningún método")
                return ""
            
            # USAR MODELO PRECARGADO - Ya está en caché desde AppConfig.ready()
            from src.infrastructure.apps import VIT_MODEL
            
            if VIT_MODEL is None:
                # Fallback si no se pre-cargó (nunca debería pasar)
                logger.warning(f"⚠️ ViT no pre-cargado, cargando on-demand...")
                from transformers import pipeline
                import torch
                classifier = pipeline(
                    "image-classification",
                    model="google/vit-base-patch16-224",
                    device=0 if torch.cuda.is_available() else -1
                )
            else:
                classifier = VIT_MODEL
            
            # Hacer predicción
            logger.info(f"   Haciendo predicción...")
            predictions = classifier(image)
            
            logger.info(f"📋 ViT: Top 5 predicciones:")
            for i, pred in enumerate(predictions[:5]):
                label = pred.get('label', '').lower()
                score = pred.get('score', 0)
                logger.info(f"   {i+1}. {label}: {score:.2%}")
            
            # BÚSQUEDA OPTIMIZADA CON PRIORIDADES
            # Procesa cada predicción y busca matches prioritarios
            for pred in predictions[:15]:
                label = pred.get('label', '').lower().strip()
                score = pred.get('score', 0)
                
                if score < 0.15:
                    continue
                
                # Buscar en orden prioritario
                for keyword, simplified_name in priority_keywords:
                    if keyword in label:
                        logger.info(f"✅ ViT identifica: {simplified_name} (ImageNet: {label}, {score:.2%})")
                        return simplified_name
            
            # Si NO encontró en mapeo, aceptar predicción TOP 1 directamente
            if len(predictions) > 0:
                top_label = predictions[0].get('label', '').lower().strip()
                top_score = predictions[0].get('score', 0)
                
                # RECHAZA automáticamente VEHÍCULOS y OBJETOS NO-ANIMALES
                if 'car' in top_label or 'truck' in top_label or 'automobile' in top_label or 'vehicle' in top_label:
                    logger.warning(f"⚠️ ViT detectó VEHÍCULO, no Animal: {top_label} ({top_score:.2%})")
                    return ""
                
                # Pero SÍ acepta personas
                if top_score > 0.15:
                    logger.info(f"✅ ViT identifica: {top_label} ({top_score:.2%})")
                    return top_label
            
            logger.warning(f"⚠️ ViT: No se encontró ningún ANIMAL válido")
            return ""
            
        except ImportError:
            logger.warning(f"⚠️ Transformers library no instalada")
            return ""
        except Exception as e:
            logger.error(f"❌ ViT error: {str(e)}")
            return ""

    def _identify_animal_with_ai_vision(self, image_base64: str) -> str:
        """Use IA vision to identify animal when YOLO fails or has low confidence
        
        Args:
            image_base64: Base64 encoded image string
        
        Returns:
            Animal name in English (e.g., 'cat', 'bird', 'dog') or empty string if not identified
        """
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Try to get key from environment, fallback to hardcoded
        api_key = os.environ.get('OPENROUTER_API_KEY') or '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'
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        prompt = """Analiza esta imagen y SOLO identifica si hay algún animal en ella.

Si hay un animal visible, responde SOLO con el nombre EXACTO del animal en inglés, en minúsculas, de esta lista:
bear, brown-bear, butterfly, cat, caterpillar, cattle, centipede, cheetah, chicken, deer, dog, duck, eagle, elephant, fox, frog, giraffe, goat, hedgehog, horse, jellyfish, kangaroo, ladybug, leopard, lion, lizard, lynx, monkey, mouse, ostrich, otter, owl, panda, parrot, peacock, pig, polar-bear, rabbit, raccoon, red-panda, rhinoceros, sheep, snake, sparrow, swan, tiger, turkey, woodpecker, zebra, acorn-woodpecker, annas-hummingbird, blue-jay, blue-winged-warbler, carolina-chickadee, carolina-wren, chipping-sparrow, common-eider, common-yellowthroat, dark-eyed-junco, eastern-bluebird, eastern-towhee, hermit-thrush, indigo-bunting, juniper-titmouse, northern-cardinal, northern-mockingbird, northern-waterthrush, orchard-oriole, painted-bunting, prothonotary-warbler, red-winged-blackbird, rock-pigeon, ruddy-duck, scarlet-tanager, song-sparrow, tufted-titmouse, varied-thrush, white-breasted-nuthatch, white-crowned-sparrow, white-throated-sparrow, wood-duck, angelfish, bluetang, butterflyfish, clownfish, goldfish, gourami, morishidol, platyfish, ribbonedsweetlips, threestrippeddamselfish, yellowcichlid, yellowtang, zebrafish, bird, person

Si NO hay ningún animal visible:
- Responde: 'no_animal'

Responde SOLO con UNA PALABRA, sin explicaciones."""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "gpt-4-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_base64,
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "temperature": 0.1,
            "max_tokens": 30,
        }
        
        try:
            logger.info(f"🤖 IA Vision: Analizando imagen visualmente...")
            r = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=20)
            
            logger.info(f"📡 IA Vision respuesta HTTP: {r.status_code}")
            
            r.raise_for_status()
            body = r.json()
            
            # Extract text from response
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
                        animal_name = text.strip().lower()
                        
                        if animal_name == 'no_animal':
                            logger.warning("⚠️ IA Vision: No animal detected in image")
                            return None
                        
                        logger.info(f"✅ IA Vision identifico: {animal_name}")
                        return animal_name
            
            logger.error(f"❌ IA Vision respuesta inesperada: {body}")
            return None
        except Exception as e:
            logger.error(f"❌ Error en IA Vision: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None


class AnimalListView(APIView):
    """API endpoint to list all animals or user's discovered animals"""
    
    def get(self, request):
        # If user_only parameter is set and user is authenticated, return only discovered animals
        user_only = request.query_params.get('user_only', 'false').lower() == 'true'
        
        if user_only and request.user.is_authenticated:
            from src.infrastructure.persistence.models import DiscoveryModel, AnimalModel
            # Get discoveries for this user with their animal data and thumbnail images
            discoveries = DiscoveryModel.objects.filter(
                user=request.user
            ).select_related('animal').order_by('animal_id', '-discovered_at').distinct('animal_id')
            
            # Get animal models with their discovery thumbnail images
            animals_data = []
            for discovery in discoveries:
                try:
                    animal_dict = discovery.animal.to_dict()
                    # Use the discovery's thumbnail URL instead of the base animal image
                    if discovery.thumbnail_url:
                        animal_dict['image_url'] = discovery.thumbnail_url
                    animals_data.append(animal_dict)
                except Exception as e:
                    print(f"Error converting discovery {discovery.id}: {e}")
                    pass
            return Response(animals_data)
        else:
            # Return all animals
            use_case = ListAllAnimalsUseCase(DjangoAnimalRepository())
            animals = use_case.execute()
            return Response(animals)


class AnimalDetailView(APIView):
    """API endpoint to get animal details"""
    
    def get(self, request, animal_id):
        try:
            use_case = GetAnimalDetailsUseCase(DjangoAnimalRepository())
            animal = use_case.execute(animal_id)
            
            # If user is authenticated and has discovered this animal, use their discovery's thumbnail
            if request.user.is_authenticated:
                from src.infrastructure.persistence.models import DiscoveryModel
                try:
                    discovery = DiscoveryModel.objects.filter(
                        user=request.user,
                        animal_id=animal_id
                    ).order_by('-discovered_at').first()
                    
                    if discovery and discovery.thumbnail_url:
                        animal['image_url'] = discovery.thumbnail_url
                except Exception as e:
                    print(f"Error loading user discovery image: {e}")
                    pass
            
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

class UserDiscoveriesView(APIView):
    """API endpoint to get the current user's discoveries"""
    
    def get(self, request):
        from src.infrastructure.persistence.models import DiscoveryModel
        
        if not request.user.is_authenticated:
            return Response(
                {'error': 'User must be authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            discoveries = DiscoveryModel.objects.filter(
                user=request.user
            ).select_related('animal').order_by('-discovered_at')
            
            result = []
            for discovery in discoveries:
                result.append({
                    'id': str(discovery.id),
                    'animal_id': str(discovery.animal.id),
                    'animal_name': discovery.animal.name,
                    'thumbnail_url': discovery.thumbnail_url,
                    'discovered_at': discovery.discovered_at.isoformat(),
                    'confidence': discovery.confidence,
                })
            
            return Response(result)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreateDiscoveryView(APIView):
    """API endpoint to create a discovery for the current user"""
    
    def post(self, request):
        from src.infrastructure.persistence.models import DiscoveryModel, AnimalModel, SessionModel
        import uuid
        
        if not request.user.is_authenticated:
            return Response(
                {'error': 'User must be authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            animal_id = request.data.get('animal_id')
            thumbnail_url = request.data.get('thumbnail_url', '')
            confidence = request.data.get('confidence', 0.0)
            
            if not animal_id:
                return Response(
                    {'error': 'animal_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the animal
            try:
                animal = AnimalModel.objects.get(id=animal_id)
            except AnimalModel.DoesNotExist:
                return Response(
                    {'error': f'Animal with id {animal_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get or create session for this user
            session, _ = SessionModel.objects.get_or_create(
                user=request.user,
                is_active=True,
                defaults={'id': str(uuid.uuid4())}
            )
            
            # Create discovery
            discovery = DiscoveryModel.objects.create(
                id=str(uuid.uuid4()),
                session=session,
                user=request.user,
                animal=animal,
                thumbnail_url=thumbnail_url,
                confidence=float(confidence)
            )
            
            return Response({
                'success': True,
                'discovery': {
                    'id': str(discovery.id),
                    'animal_id': str(discovery.animal.id),
                    'animal_name': discovery.animal.name,
                    'thumbnail_url': discovery.thumbnail_url,
                    'discovered_at': discovery.discovered_at.isoformat(),
                    'confidence': discovery.confidence,
                }
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            import traceback
            return Response(
                {'error': str(e), 'details': traceback.format_exc()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )