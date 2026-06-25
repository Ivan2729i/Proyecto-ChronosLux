from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from watches.models import Producto
from .models import Proveedor, Compra, DetalleCompra
from django.contrib import messages


def obtener_proveedor_o_403(user):
    proveedor = Proveedor.objects.filter(user=user).first()
    pertenece_grupo = user.groups.filter(name='Proveedores').exists()

    if not proveedor and not pertenece_grupo:
        raise PermissionDenied

    if not proveedor:
        raise PermissionDenied("El usuario pertenece al grupo Proveedores, pero no tiene perfil de proveedor.")

    return proveedor


@login_required
def portal_proveedor(request):
    proveedor = obtener_proveedor_o_403(request.user)

    compras = Compra.objects.filter(proveedor=proveedor).order_by('-fecha_compra')

    context = {
        'proveedor': proveedor,
        'compras': compras,
    }

    return render(request, 'proveedores/portal.html', context)


@login_required
def crear_compra(request):
    proveedor = obtener_proveedor_o_403(request.user)

    if request.method == 'POST':
        proveedor = request.user.proveedor

        # --- INICIO: VALIDACIÓN DE ORDEN VACÍA ---
        orden_tiene_productos = False
        for key, value in request.POST.items():
            if key.startswith('cantidad_'):
                try:
                    if int(value) > 0:
                        orden_tiene_productos = True
                        break
                except (ValueError, TypeError):
                    continue

        if not orden_tiene_productos:
            messages.error(request,
                           'No puedes enviar una orden de compra vacía. Por favor, especifica la cantidad de al menos un producto.')
            return redirect('crear_compra')
        # --- FIN: VALIDACIÓN ---

        nueva_compra = Compra.objects.create(proveedor=proveedor)
        total_compra = 0

        for key, value in request.POST.items():
            if key.startswith('cantidad_'):
                producto_id = key.split('_')[1]
                try:
                    cantidad = int(value)
                    if cantidad > 0:
                        costo_str = request.POST.get(f'costo_{producto_id}', '0')
                        costo = float(costo_str)

                        producto = Producto.objects.get(pk=producto_id)

                        DetalleCompra.objects.create(
                            compra=nueva_compra,
                            producto=producto,
                            cantidad=cantidad,
                            costo_unitario=costo
                        )

                        producto.stock += cantidad
                        producto.save()

                        total_compra += cantidad * costo
                except (ValueError, TypeError, Producto.DoesNotExist):
                    continue

        nueva_compra.total_compra = total_compra
        nueva_compra.save()

        messages.success(request, 'Orden de suministro enviada con éxito.')
        return redirect('portal_proveedor')

    productos = Producto.objects.all().order_by('marca', 'nombre')
    context = {
        'productos': productos
    }
    return render(request, 'proveedores/crear_compra.html', context)


@login_required
def historial_compras(request):
    proveedor = obtener_proveedor_o_403(request.user)

    compras = Compra.objects.filter(proveedor=request.user.proveedor).order_by('-fecha_compra')

    context = {
        'compras': compras
    }
    return render(request, 'proveedores/historial_compras.html', context)

