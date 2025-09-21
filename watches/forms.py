import os
import uuid
from django import forms
from .models import Producto, Categoria, ImgProducto
import re
from decimal import Decimal


class ProductoForm(forms.ModelForm):
    # --- 1. Definimos los campos de Categoría por separado ---

    # Creamos un campo de opciones para el género
    genero = forms.ChoiceField(
        choices=[('', '---------'), ('Masculino', 'Masculino'), ('Femenino', 'Femenino'), ('Unisex', 'Unisex')],
        label="Género",
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'})
    )

    # Creamos un campo de texto para el material
    material = forms.CharField(
        label="Material",
        widget=forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'})
    )

    # Creamos un campo de opciones para el tipo de reloj
    tipo = forms.ChoiceField(
        choices=[('', '---------')] + Categoria._meta.get_field('tipo').choices,
        label="Tipo de Reloj",
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'})
    )

    imagen = forms.ImageField(
        label="Foto del Reloj",
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'})
    )

    class Meta:
        model = Producto
        fields = [
            'nombre',
            'precio',
            'stock',
            'marca',
            'es_exclusivo',
            'descripcion1',
            'descripcion2',
            'descripcion3',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
            'precio': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
            'stock': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
            'marca': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
            'es_exclusivo': forms.Select(
                choices=[(False, 'No'), (True, 'Sí')],
                attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}
            ),
            'descripcion1': forms.Textarea(
                attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md', 'rows': 3}),
            'descripcion2': forms.Textarea(
                attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md', 'rows': 3}),
            'descripcion3': forms.Textarea(
                attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md', 'rows': 3}),
        }

        # --- VALIDACIONES PERSONALIZADAS ---

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not re.match(r'^[a-zA-Z0-9\sáéíóúÁÉÍÓÚñÑ-]+$', nombre):
            raise forms.ValidationError("El nombre solo puede contener letras y espacios.")
        return nombre

    def clean_material(self):
        material = self.cleaned_data.get('material')
        if not re.match(r'^[a-zA-Z\sáéíóúÁÉÍÓÚñÑ]+$', material):
            raise forms.ValidationError("El material solo puede contener letras y espacios.")
        return material

    def clean_descripcion1(self):
        descripcion = self.cleaned_data.get('descripcion1')
        if descripcion and not re.match(r'^[a-zA-Z0-9\sáéíóúÁÉÍÓÚñÑ.,]+$', descripcion):
            raise forms.ValidationError("La descripción contiene caracteres no válidos.")
        return descripcion

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 1:
            raise forms.ValidationError("El stock no puede ser cero o un número negativo. El mínimo es 1.")
        return stock

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is not None:
            try:
                precio = Decimal(str(precio))
            except:
                raise forms.ValidationError("Por favor, introduce un número válido.")

            # Ahora aplicamos la validación del mínimo
            if precio < 100:
                raise forms.ValidationError("El precio no puede ser negativo, cero o menor a 100.")
        return precio
    #  --- FIN DE VALIDACIÓN ---

