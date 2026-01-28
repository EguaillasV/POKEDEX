"""
Web Views - Django Template Views
Main web interface for the application.
"""
from django.shortcuts import render
from django.views import View


class HomeView(View):
    """Home page with camera recognition interface"""
    
    def get(self, request):
        return render(request, 'web/home.html')


class GalleryView(View):
    """Gallery of discovered animals"""
    
    def get(self, request):
        return render(request, 'web/gallery.html')


class AnimalInfoView(View):
    """Detailed animal information page"""
    
    def get(self, request, animal_id):
        return render(request, 'web/animal_info.html', {
            'animal_id': animal_id,
        })


class AboutView(View):
    """About page"""
    
    def get(self, request):
        return render(request, 'web/about.html')
