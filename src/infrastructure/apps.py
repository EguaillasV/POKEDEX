from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

# Global ViT model - precargado una sola vez
VIT_MODEL = None

class InfrastructureConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.infrastructure'
    verbose_name = 'Infrastructure Layer'
    
    def ready(self):
        """
        Pre-cargar modelo ViT cuando Django inicia
        Esto ocurre UNA sola vez, no en cada solicitud
        Ahorra 45+ segundos en la primera llamada a ViT
        """
        global VIT_MODEL
        
        import os
        # Solo pre-cargar si no estamos en manage.py check o migrate
        if 'runserver' in os.sys.argv or 'daphne' in os.sys.argv:
            try:
                logger.info("🔄 [STARTUP] Pre-cargando modelo ViT-base-patch16-224...")
                
                from transformers import pipeline
                import torch
                
                VIT_MODEL = pipeline(
                    "image-classification",
                    model="google/vit-base-patch16-224",
                    device=0 if torch.cuda.is_available() else -1
                )
                
                logger.info("✅ [STARTUP] ViT cargado exitosamente y en caché")
                
            except Exception as e:
                logger.error(f"❌ [STARTUP] Error pre-cargando ViT: {e}")
                VIT_MODEL = None
