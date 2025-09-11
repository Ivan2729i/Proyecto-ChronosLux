from django.shortcuts import render
from .models import Watch

def home(request):
    featured_watches = [
        {
            'id': 1,
            'name': 'Submariner Date',
            'brand': 'Rolex',
            'price': 12500,
            'image': '/placeholder.svg?height=400&width=400',
            'rating': 5.0,
            'features': ['Resistente al agua 300m', 'Movimiento automático', 'Cristal de zafiro']
        },
        {
            'id': 2,
            'name': 'Speedmaster Professional',
            'brand': 'Omega',
            'price': 6800,
            'image': '/placeholder.svg?height=400&width=400',
            'rating': 4.9,
            'features': ['Cronógrafo manual', 'Certificado por la NASA', 'Resistente a campos magnéticos']
        },
        {
            'id': 3,
            'name': 'Royal Oak',
            'brand': 'Audemars Piguet',
            'price': 28000,
            'image': '/placeholder.svg?height=400&width=400',
            'rating': 5.0,
            'features': ['Caja octagonal icónica', 'Movimiento ultra-delgado', 'Acabado artesanal']
        }
    ]
    
    catalog_watches = [
        {
            'id': 4,
            'name': 'Datejust 36',
            'brand': 'Rolex',
            'price': 8900,
            'image': '/placeholder.svg?height=300&width=300',
            'rating': 4.8,
            'features': ['Acero y oro', 'Fecha instantánea', 'Movimiento perpetuo']
        },
        {
            'id': 5,
            'name': 'Seamaster Planet Ocean',
            'brand': 'Omega',
            'price': 5200,
            'image': '/placeholder.svg?height=300&width=300',
            'rating': 4.7,
            'features': ['Resistente al agua 600m', 'Bisel unidireccional', 'Co-Axial Master Chronometer']
        },
        {
            'id': 6,
            'name': 'Millenary',
            'brand': 'Audemars Piguet',
            'price': 22000,
            'image': '/placeholder.svg?height=300&width=300',
            'rating': 4.9,
            'features': ['Caja ovalada', 'Movimiento visible', 'Edición limitada']
        },
        {
            'id': 7,
            'name': 'GMT-Master II',
            'brand': 'Rolex',
            'price': 15200,
            'image': '/placeholder.svg?height=300&width=300',
            'rating': 5.0,
            'features': ['Doble zona horaria', 'Bisel Pepsi', 'Movimiento GMT']
        },
        {
            'id': 8,
            'name': 'De Ville Prestige',
            'brand': 'Omega',
            'price': 3800,
            'image': '/placeholder.svg?height=300&width=300',
            'rating': 4.6,
            'features': ['Diseño clásico', 'Movimiento Co-Axial', 'Caja delgada']
        }
    ]
    
    context = {
        'featured_watches': featured_watches,
        'catalog_watches': catalog_watches
    }
    return render(request, 'home.html', context)
