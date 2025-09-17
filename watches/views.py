from django.shortcuts import render
from django.core.paginator import Paginator

def build_home_context():
    featured_watches = [
        {
            'id': 1,
            'name': 'Submariner Date',
            'brand': 'Rolex',
            "type": "Deportivo",
            'price': 12500,
            'image': '/static/img/rolex-submariner.jpg',
            'rating': 4.9,
            'features': ['Resistente al agua 300m', 'Movimiento automático', 'Cristal de zafiro']
        },
        {
            'id': 2,
            'name': 'Speedmaster Professional',
            'brand': 'Omega',
            "type": "Casual",
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
            'image': '/static/img/placeholder.jpg',
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
        },
        {
            'id': 1,
            'name': 'Submariner Date',
            'brand': 'Rolex',
            "type": "Deportivo",
            "gender": "Hombre",
            'price': 12500,
            'image': '/static/img/rolex-submariner.jpg',
            'rating': 4.9,
            'features': ['Resistente al agua 300m', 'Movimiento automático', 'Cristal de zafiro']
        },
    ]

    return {'featured_watches': featured_watches, 'catalog_watches': catalog_watches}

def home(request):
    return render(request, 'home.html', build_home_context())

def catalog(request):
    ctx = build_home_context()
    items = ctx['catalog_watches'][:]  # copia

    # ---- Filtros ----
    t = (request.GET.get('type') or '').lower()
    price = (request.GET.get('price') or '').lower()
    gender = (request.GET.get('gender') or '').lower()

    def match_type(x):
        if not t or t == 'all': return True
        value = (x.get('type') or '').lower()
        return value == t

    def match_price(x):
        if not price or price == 'all': return True
        p = float(x.get('price') or 0)
        if price == 'up_to_5000': return p <= 5000
        if price == '5000_10000': return 5000 <= p <= 10000
        if price == 'over_10000': return p > 10000
        return True

    def match_gender(x):
        if not gender or gender == 'all': return True
        return (x.get('gender') or '').lower() == gender

    items = [x for x in items if match_type(x) and match_price(x) and match_gender(x)]

    # ---- Ordenamiento ----
    sort = (request.GET.get('sort') or 'featured').lower()
    if sort == 'price_asc':
        items.sort(key=lambda x: float(x.get('price') or 0))
    elif sort == 'price_desc':
        items.sort(key=lambda x: float(x.get('price') or 0), reverse=True)
    elif sort == 'rating_desc':
        items.sort(key=lambda x: float(x.get('rating') or 0), reverse=True)
    elif sort == 'name_asc':
        items.sort(key=lambda x: (x.get('name') or '').lower())
    # 'featured' = sin cambios

    # ---- Paginación ----
    page_number = request.GET.get('page') or 1
    paginator = Paginator(items, 12)  # 12 por página
    page_obj = paginator.get_page(page_number)

    return render(request, 'catalog.html', {
        'page_obj': page_obj,
        'catalog_watches': page_obj.object_list,
        'querystring': request.GET.urlencode(),
        'current': {
            'type': t or 'all',
            'price': price or 'all',
            'gender': gender or 'all',
            'sort': sort or 'featured',
        }
    })
