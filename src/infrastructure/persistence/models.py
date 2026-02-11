"""
Django ORM Models
These models are infrastructure concerns and map to domain entities.
"""
from django.db import models
from django.contrib.auth import get_user_model


class AnimalModel(models.Model):
    """Database model for Animal entity"""
    
    class AnimalClass(models.TextChoices):
        MAMMAL = 'MAMMAL', 'Mamífero'
        BIRD = 'BIRD', 'Ave'
        REPTILE = 'REPTILE', 'Reptil'
        AMPHIBIAN = 'AMPHIBIAN', 'Anfibio'
        FISH = 'FISH', 'Pez'
        INVERTEBRATE = 'INVERTEBRATE', 'Invertebrado'
    
    class DietType(models.TextChoices):
        CARNIVORE = 'CARNIVORE', 'Carnívoro'
        HERBIVORE = 'HERBIVORE', 'Herbívoro'
        OMNIVORE = 'OMNIVORE', 'Omnívoro'
        INSECTIVORE = 'INSECTIVORE', 'Insectívoro'
        PISCIVORE = 'PISCIVORE', 'Piscívoro'
    
    class ConservationStatus(models.TextChoices):
        EXTINCT = 'EXTINCT', 'Extinto'
        EXTINCT_IN_WILD = 'EXTINCT_IN_WILD', 'Extinto en Estado Silvestre'
        CRITICALLY_ENDANGERED = 'CRITICALLY_ENDANGERED', 'En Peligro Crítico'
        ENDANGERED = 'ENDANGERED', 'En Peligro'
        VULNERABLE = 'VULNERABLE', 'Vulnerable'
        NEAR_THREATENED = 'NEAR_THREATENED', 'Casi Amenazado'
        LEAST_CONCERN = 'LEAST_CONCERN', 'Preocupación Menor'
        DATA_DEFICIENT = 'DATA_DEFICIENT', 'Datos Insuficientes'
        NOT_EVALUATED = 'NOT_EVALUATED', 'No Evaluado'
    
    id = models.CharField(max_length=36, primary_key=True)
    name = models.CharField(max_length=100, unique=True, db_index=True)
    scientific_name = models.CharField(max_length=150)
    description = models.TextField()
    animal_class = models.CharField(
        max_length=20,
        choices=AnimalClass.choices,
        db_index=True
    )
    habitat = models.CharField(max_length=200)
    diet = models.CharField(max_length=20, choices=DietType.choices)
    conservation_status = models.CharField(
        max_length=25,
        choices=ConservationStatus.choices
    )
    fun_facts = models.JSONField(default=list)
    aliases = models.JSONField(default=list, blank=True)
    average_lifespan = models.CharField(max_length=300, blank=True, null=True)
    average_weight = models.CharField(max_length=300, blank=True, null=True)
    average_height = models.CharField(max_length=300, blank=True, null=True)
    geographic_distribution = models.CharField(max_length=500, blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    sound_url = models.URLField(blank=True, null=True)
    last_recognition_confidence = models.FloatField(blank=True, null=True, help_text="Última confianza del modelo YOLO")
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_animals'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'animals'
        verbose_name = 'Animal'
        verbose_name_plural = 'Animales'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.scientific_name})"
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        # Map animal class to display name
        animal_class_map = {choice[0]: choice[1] for choice in self.AnimalClass.choices}
        diet_map = {choice[0]: choice[1] for choice in self.DietType.choices}
        status_map = {choice[0]: choice[1] for choice in self.ConservationStatus.choices}
        
        return {
            'id': str(self.id),
            'name': self.name,
            'scientific_name': self.scientific_name,
            'description': self.description,
            'animal_class': animal_class_map.get(self.animal_class, self.animal_class),
            'habitat': self.habitat,
            'diet': diet_map.get(self.diet, self.diet),
            'conservation_status': status_map.get(self.conservation_status, self.conservation_status),
            'fun_facts': self.fun_facts or [],
            'average_lifespan': self.average_lifespan,
            'average_weight': self.average_weight,
            'average_height': self.average_height,
            'geographic_distribution': self.geographic_distribution,
            'image_url': self.image_url,
            'sound_url': self.sound_url,
            'is_endangered': self.conservation_status in [
                'EXTINCT', 'EXTINCT_IN_WILD', 'CRITICALLY_ENDANGERED', 'ENDANGERED'
            ]
        }


class SessionModel(models.Model):
    """Database model for UserSession entity"""
    
    id = models.CharField(max_length=36, primary_key=True)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='recognition_sessions'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'sessions'
        verbose_name = 'Sesión'
        verbose_name_plural = 'Sesiones'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Session {self.id[:8]}..."


class DiscoveryModel(models.Model):
    """Database model for Discovery entity"""
    
    id = models.CharField(max_length=36, primary_key=True)
    session = models.ForeignKey(
        SessionModel,
        on_delete=models.CASCADE,
        related_name='discoveries'
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='discoveries'
    )
    animal = models.ForeignKey(
        AnimalModel,
        on_delete=models.CASCADE,
        related_name='discoveries'
    )
    thumbnail_url = models.URLField()
    discovered_at = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    confidence = models.FloatField(default=0.0)
    
    class Meta:
        db_table = 'discoveries'
        verbose_name = 'Descubrimiento'
        verbose_name_plural = 'Descubrimientos'
        ordering = ['-discovered_at']
    
    def __str__(self):
        return f"Discovery: {self.animal.name} on {self.discovered_at}"


class ProfileModel(models.Model):
    """Extended profile information for users"""

    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone = models.CharField(max_length=30, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=250, blank=True, null=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'

    def __str__(self):
        return f"Profile for {self.user.username}"
