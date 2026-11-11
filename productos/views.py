from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .models import Producto, Categoria, Pedido, DetallePedido
from .forms import RegistroForm


def obtener_carrito(request):
    return request.session.get("carrito", {})


def guardar_carrito(request, carrito):
    request.session["carrito"] = carrito
    request.session.modified = True


def calcular_detalle_carrito(carrito):
    items = []
    total = 0
    cantidad_total = 0

    for id_texto, cantidad in carrito.items():
        producto = Producto.objects.filter(id=int(id_texto)).first()
        if producto:
            cant = int(cantidad)
            subtotal = producto.precio * cant
            items.append({
                "producto": producto,
                "cantidad": cant,
                "subtotal": subtotal,
            })
            total = total + subtotal
            cantidad_total = cantidad_total + cant

    return items, total, cantidad_total


def landing(request):
    categorias = Categoria.objects.annotate(n=Count("productos")).all()
    destacados = Producto.objects.select_related("categoria").order_by("-stock")[:4]
    _, _, cart_count = calcular_detalle_carrito(obtener_carrito(request))

    contexto = {
        "categorias": categorias,
        "destacados": destacados,
        "total_productos": Producto.objects.count(),
        "cart_count": cart_count,
    }
    return render(request, "landing.html", contexto)


def tienda(request):
    q = request.GET.get("q", "").strip()
    cat_id = request.GET.get("categoria", "")
    cat_activa = int(cat_id) if cat_id.isdigit() else 0

    productos = Producto.objects.select_related("categoria").all()
    if cat_activa > 0:
        productos = productos.filter(categoria_id=cat_activa)
    if q != "":
        productos = productos.filter(nombre__icontains=q)

    categorias = Categoria.objects.all()
    _, _, cart_count = calcular_detalle_carrito(obtener_carrito(request))

    contexto = {
        "productos": productos,
        "categorias": categorias,
        "cat_activa": cat_activa,
        "q": q,
        "cart_count": cart_count,
    }
    return render(request, "tienda.html", contexto)


def detalle(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    _, _, cart_count = calcular_detalle_carrito(obtener_carrito(request))

    contexto = {
        "producto": producto,
        "cart_count": cart_count,
    }
    return render(request, "detalle.html", contexto)


def vista_registro(request):
    if request.user.is_authenticated:
        return redirect("tienda")

    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(request, f"Bienvenido/a, {usuario.username}. Tu cuenta fue creada.")
            return redirect("tienda")
    else:
        form = RegistroForm()

    return render(request, "registro.html", {"form": form})


def vista_login(request):
    if request.user.is_authenticated:
        return redirect("tienda")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)
            messages.success(request, f"Hola, {usuario.username}.")
            siguiente = request.GET.get("next") or request.POST.get("next")
            if siguiente:
                return redirect(siguiente)
            return redirect("tienda")
    else:
        form = AuthenticationForm(request)

    return render(request, "login.html", {"form": form})


def vista_logout(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect("tienda")


def carrito_ver(request):
    items, total, cantidad_total = calcular_detalle_carrito(obtener_carrito(request))
    contexto = {
        "items": items,
        "total": total,
        "cart_count": cantidad_total,
    }
    return render(request, "carrito.html", contexto)


def carrito_agregar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    carrito = obtener_carrito(request)
    cantidad_actual = int(carrito.get(str(pk), 0))

    if producto.stock <= 0:
        messages.error(request, f"{producto.nombre} está sin stock.")
    elif cantidad_actual + 1 > producto.stock:
        messages.error(request, f"Solo quedan {producto.stock} unidades de {producto.nombre}.")
    else:
        carrito[str(pk)] = cantidad_actual + 1
        guardar_carrito(request, carrito)
        messages.success(request, f"{producto.nombre} fue agregado al carrito.")

    return redirect("carrito")


def carrito_quitar(request, pk):
    carrito = obtener_carrito(request)
    if str(pk) in carrito:
        del carrito[str(pk)]
        guardar_carrito(request, carrito)
        messages.info(request, "Producto quitado del carrito.")
    return redirect("carrito")


def carrito_actualizar(request, pk):
    if request.method == "POST":
        producto = get_object_or_404(Producto, pk=pk)
        carrito = obtener_carrito(request)
        try:
            nueva_cantidad = int(request.POST.get("cantidad", 1))
        except ValueError:
            nueva_cantidad = 1

        if nueva_cantidad <= 0:
            if str(pk) in carrito:
                del carrito[str(pk)]
            messages.info(request, f"{producto.nombre} fue eliminado del carrito.")
        elif nueva_cantidad > producto.stock:
            messages.error(request, f"Solo hay {producto.stock} unidades disponibles de {producto.nombre}.")
        else:
            carrito[str(pk)] = nueva_cantidad
            messages.success(request, "Cantidad actualizada.")

        guardar_carrito(request, carrito)
    return redirect("carrito")


@login_required
def checkout(request):
    if request.method != "POST":
        return redirect("carrito")

    carrito = obtener_carrito(request)
    items, total, _ = calcular_detalle_carrito(carrito)

    if not items:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("carrito")

    # Verificar que todos los productos tengan stock suficiente
    for item in items:
        prod = item["producto"]
        if item["cantidad"] > prod.stock:
            messages.error(request, f"Stock insuficiente para {prod.nombre}.")
            return redirect("carrito")

    # Crear el pedido y descontar stock
    pedido = Pedido.objects.create(usuario=request.user, total=total)
    for item in items:
        prod = item["producto"]
        cant = item["cantidad"]
        DetallePedido.objects.create(
            pedido=pedido,
            producto=prod,
            nombre_producto=prod.nombre,
            cantidad=cant,
            precio_unitario=prod.precio,
        )
        prod.stock = prod.stock - cant
        prod.save()

    guardar_carrito(request, {})
    messages.success(request, f"Compra realizada con éxito. Pedido #{pedido.id} por ${total}.")
    return redirect("mis_pedidos")


@login_required
def mis_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).prefetch_related("detalles")
    _, _, cart_count = calcular_detalle_carrito(obtener_carrito(request))
    return render(request, "mis_pedidos.html", {"pedidos": pedidos, "cart_count": cart_count})
