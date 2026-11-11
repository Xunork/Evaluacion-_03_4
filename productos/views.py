from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, Sum
from .models import Producto, Categoria, Pedido, DetallePedido, ConsultaCliente
from .forms import RegistroForm, ProductoForm, CategoriaForm, ConsultaClienteForm


def es_admin(user):
    return user.is_authenticated and user.is_staff


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


def obtener_ultimos_visitados(request):
    ids_visitados = request.session.get("ultimos_visitados", [])
    productos_visitados = []
    for prod_id in ids_visitados:
        prod = Producto.objects.filter(id=prod_id).first()
        if prod:
            productos_visitados.append(prod)
    return productos_visitados


def tienda(request):
    # Contador de visitas al catálogo guardado en sesión
    visitas = request.session.get("visitas_catalogo", 0) + 1
    request.session["visitas_catalogo"] = visitas

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
    ultimos_visitados = obtener_ultimos_visitados(request)

    contexto = {
        "productos": productos,
        "categorias": categorias,
        "cat_activa": cat_activa,
        "q": q,
        "cart_count": cart_count,
        "visitas_catalogo": visitas,
        "ultimos_visitados": ultimos_visitados,
    }
    return render(request, "tienda.html", contexto)


def detalle(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    # Guardar en sesión los últimos 3 productos visitados
    visitados = request.session.get("ultimos_visitados", [])
    if pk in visitados:
        visitados.remove(pk)
    visitados.insert(0, pk)
    visitados = visitados[:3]
    request.session["ultimos_visitados"] = visitados
    request.session.modified = True

    _, _, cart_count = calcular_detalle_carrito(obtener_carrito(request))
    ultimos_visitados = obtener_ultimos_visitados(request)

    contexto = {
        "producto": producto,
        "cart_count": cart_count,
        "ultimos_visitados": ultimos_visitados,
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
        return redirect("panel_admin" if request.user.is_staff else "tienda")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)
            messages.success(request, f"Hola, {usuario.username}.")
            siguiente = request.GET.get("next") or request.POST.get("next")
            if siguiente:
                return redirect(siguiente)
            if usuario.is_staff:
                return redirect("panel_admin")
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

    for item in items:
        prod = item["producto"]
        if item["cantidad"] > prod.stock:
            messages.error(request, f"Stock insuficiente para {prod.nombre}.")
            return redirect("carrito")

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


# ==========================================================
# ETAPA 1: CRUD DEL CATÁLOGO DESDE LA WEB CON FORMULARIOS
# ==========================================================

@user_passes_test(es_admin)
def panel_admin(request):
    productos = Producto.objects.select_related("categoria").all()
    _, _, cart_count = calcular_detalle_carrito(obtener_carrito(request))
    contexto = {
        "productos": productos,
        "cart_count": cart_count,
    }
    return render(request, "admin_panel.html", contexto)


@user_passes_test(es_admin)
def producto_crear(request):
    if request.method == "POST":
        form = ProductoForm(request.POST)
        if form.is_valid():
            nuevo_producto = form.save(commit=False)
            if not nuevo_producto.imagen:
                nuevo_producto.imagen = "/static/img/productos/default.svg"
            nuevo_producto.save()
            messages.success(request, f"Producto '{nuevo_producto.nombre}' creado correctamente.")
            return redirect("tienda")
    else:
        form = ProductoForm()

    _, _, cart_count = calcular_detalle_carrito(obtener_carrito(request))
    contexto = {
        "form": form,
        "titulo": "Crear nuevo producto",
        "cart_count": cart_count,
    }
    return render(request, "producto_form.html", contexto)


@user_passes_test(es_admin)
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == "POST":
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            prod_editado = form.save(commit=False)
            if not prod_editado.imagen:
                prod_editado.imagen = "/static/img/productos/default.svg"
            prod_editado.save()
            messages.success(request, f"Producto '{prod_editado.nombre}' actualizado correctamente.")
            return redirect("tienda")
    else:
        form = ProductoForm(instance=producto)

    _, _, cart_count = calcular_detalle_carrito(obtener_carrito(request))
    contexto = {
        "form": form,
        "titulo": f"Editar producto: {producto.nombre}",
        "producto": producto,
        "cart_count": cart_count,
    }
    return render(request, "producto_form.html", contexto)


@user_passes_test(es_admin)
def producto_eliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == "POST":
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f"Producto '{nombre}' eliminado correctamente.")
        return redirect("tienda")

    _, _, cart_count = calcular_detalle_carrito(obtener_carrito(request))
    contexto = {
        "producto": producto,
        "cart_count": cart_count,
    }
    return render(request, "producto_confirmar.html", contexto)


@user_passes_test(es_admin)
def categorias_admin(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría creada correctamente.")
            return redirect("categorias_admin")
    else:
        form = CategoriaForm()

    categorias = Categoria.objects.annotate(total_prod=Count("productos")).all()
    _, _, cart_count = calcular_detalle_carrito(obtener_carrito(request))
    contexto = {
        "categorias": categorias,
        "form": form,
        "cart_count": cart_count,
    }
    return render(request, "categorias.html", contexto)


# ==========================================================
# ETAPA 2: REPORTES CON CONSULTAS DEL ORM
# ==========================================================

def reporte_resumen(request):
    # Reporte 1: Agrupación por categoría usando annotate()
    resumen_categorias = Categoria.objects.annotate(
        cantidad_productos=Count("productos"),
        precio_promedio=Avg("productos__precio"),
        stock_total=Sum("productos__stock"),
    ).order_by("nombre")

    # Redondeamos el promedio en la vista para no hacer cálculos en el template
    for cat in resumen_categorias:
        if cat.precio_promedio is not None:
            cat.precio_promedio_entero = int(round(cat.precio_promedio))
        else:
            cat.precio_promedio_entero = 0
        if cat.stock_total is None:
            cat.stock_total = 0

    # Totales generales del catálogo usando aggregate()
    totales = Producto.objects.aggregate(
        total_productos=Count("id"),
        promedio_general=Avg("precio"),
        suma_stock_general=Sum("stock"),
    )

    promedio_general_entero = 0
    if totales["promedio_general"] is not None:
        promedio_general_entero = int(round(totales["promedio_general"]))

    _, _, cart_count = calcular_detalle_carrito(obtener_carrito(request))
    contexto = {
        "resumen_categorias": resumen_categorias,
        "total_productos": totales["total_productos"] or 0,
        "promedio_general": promedio_general_entero,
        "suma_stock_general": totales["suma_stock_general"] or 0,
        "cart_count": cart_count,
    }
    return render(request, "reporte_resumen.html", contexto)


def reporte_critico(request):
    # Reporte 2: Listado filtrado bajo umbral de stock crítico usando filter() y order_by()
    umbral = 10
    productos_criticos = (
        Producto.objects.select_related("categoria")
        .filter(stock__lte=umbral)
        .order_by("stock", "nombre")
    )
    total_criticos = productos_criticos.count()

    _, _, cart_count = calcular_detalle_carrito(obtener_carrito(request))
    contexto = {
        "productos_criticos": productos_criticos,
        "umbral": umbral,
        "total_criticos": total_criticos,
        "cart_count": cart_count,
    }
    return render(request, "reporte_critico.html", contexto)


# ==========================================================
# ETAPA 3: FORMULARIO DE CLIENTES (MODELFORM) Y SESIONES
# ==========================================================

def consultas_clientes(request):
    producto_id = request.GET.get("producto", "")

    if request.method == "POST":
        form = ConsultaClienteForm(request.POST)
        if form.is_valid():
            consulta = form.save()
            messages.success(
                request,
                f"¡Gracias {consulta.nombre}! Tu consulta fue guardada en la base de datos correctamente."
            )
            return redirect("consultas")
    else:
        datos_iniciales = {}
        if producto_id.isdigit():
            datos_iniciales["producto_interes"] = int(producto_id)
        form = ConsultaClienteForm(initial=datos_iniciales)

    consultas = ConsultaCliente.objects.select_related("producto_interes").all()[:10]
    _, _, cart_count = calcular_detalle_carrito(obtener_carrito(request))
    ultimos_visitados = obtener_ultimos_visitados(request)

    contexto = {
        "form": form,
        "consultas": consultas,
        "cart_count": cart_count,
        "ultimos_visitados": ultimos_visitados,
    }
    return render(request, "consultas.html", contexto)


