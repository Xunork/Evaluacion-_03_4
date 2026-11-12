from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
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
    carrito = obtener_carrito(request)
    items, total, cantidad_total = calcular_detalle_carrito(carrito)

    if not items:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("carrito")

    for item in items:
        prod = item["producto"]
        if item["cantidad"] > prod.stock:
            messages.error(request, f"Stock insuficiente para {prod.nombre}.")
            return redirect("carrito")

    # Si es GET, mostramos la ventana propia de confirmación de compra
    if request.method == "GET":
        contexto = {
            "items": items,
            "total": total,
            "cart_count": cantidad_total,
        }
        return render(request, "confirmar_compra.html", contexto)

    # Si es POST, confirmamos el pedido y descontamos stock
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
    categorias = Categoria.objects.annotate(total_prod=Count("productos")).all()
    pedidos_recientes = Pedido.objects.select_related("usuario").prefetch_related("detalles").all()[:5]

    totales_ventas = Pedido.objects.aggregate(
        total_pedidos=Count("id"),
        ingresos_totales=Sum("total"),
    )
    totales_stock = Producto.objects.aggregate(
        suma_stock=Sum("stock"),
    )

    _, _, cart_count = calcular_detalle_carrito(obtener_carrito(request))
    contexto = {
        "productos": productos,
        "categorias": categorias,
        "pedidos_recientes": pedidos_recientes,
        "total_pedidos": totales_ventas["total_pedidos"] or 0,
        "ingresos_totales": totales_ventas["ingresos_totales"] or 0,
        "suma_stock": totales_stock["suma_stock"] or 0,
        "cart_count": cart_count,
    }
    return render(request, "admin_panel.html", contexto)


@user_passes_test(es_admin)
def pedidos_admin(request):
    pedidos = Pedido.objects.select_related("usuario").prefetch_related("detalles").all()
    categorias = Categoria.objects.all()
    totales_ventas = Pedido.objects.aggregate(
        total_pedidos=Count("id"),
        ingresos_totales=Sum("total"),
    )
    unidades_vendidas = DetallePedido.objects.aggregate(total_unidades=Sum("cantidad"))

    _, _, cart_count = calcular_detalle_carrito(obtener_carrito(request))
    contexto = {
        "pedidos": pedidos,
        "categorias": categorias,
        "total_pedidos": totales_ventas["total_pedidos"] or 0,
        "ingresos_totales": totales_ventas["ingresos_totales"] or 0,
        "total_unidades": unidades_vendidas["total_unidades"] or 0,
        "cart_count": cart_count,
    }
    return render(request, "admin_pedidos.html", contexto)


@user_passes_test(es_admin)
def producto_crear(request):
    if request.method == "POST":
        form = ProductoForm(request.POST)
        if form.is_valid():
            nuevo_producto = form.save(commit=False)
            if not nuevo_producto.imagen:
                nuevo_producto.imagen = "/static/img/productos/default.jpg"
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
                prod_editado.imagen = "/static/img/productos/default.jpg"
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
        "categorias": Categoria.objects.all(),
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


# ==========================================================
# EXPORTACIÓN DIRECTA A ARCHIVO EXCEL (.XLSX) CON DISEÑO Y TOTALES
# ==========================================================

def generar_respuesta_xls(nombre_archivo, titulo, encabezados, filas, fila_total=None, cols_moneda=None):
    if cols_moneda is None:
        cols_moneda = []

    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte"
    ws.views.sheetView[0].showGridLines = True

    num_cols = len(encabezados)
    ultima_letra = get_column_letter(num_cols)

    # Estilos principales
    fondo_titulo = PatternFill(start_color="141413", end_color="141413", fill_type="solid")
    fondo_subtitulo = PatternFill(start_color="EFECE6", end_color="EFECE6", fill_type="solid")
    fondo_encabezado = PatternFill(start_color="262624", end_color="262624", fill_type="solid")
    fondo_par = PatternFill(start_color="FAF9F5", end_color="FAF9F5", fill_type="solid")
    fondo_impar = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    fondo_total = PatternFill(start_color="EFECE6", end_color="EFECE6", fill_type="solid")

    fuente_titulo = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    fuente_sub = Font(name="Calibri", size=10, italic=True, color="4A4945")
    fuente_encabezado = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    fuente_celda = Font(name="Calibri", size=10, color="141413")
    fuente_total = Font(name="Calibri", size=11, bold=True, color="141413")

    borde_fino = Side(border_style="thin", color="D4D0C8")
    borde_grueso_arriba = Side(border_style="medium", color="141413")
    borde_doble_abajo = Side(border_style="double", color="141413")

    borde_celda = Border(left=borde_fino, right=borde_fino, top=borde_fino, bottom=borde_fino)
    borde_total = Border(
        left=borde_fino,
        right=borde_fino,
        top=borde_grueso_arriba,
        bottom=borde_doble_abajo,
    )

    # Fila 1: Banner de título
    ws.merge_cells(f"A1:{ultima_letra}1")
    celda_t1 = ws["A1"]
    celda_t1.value = f"FERRETERÍA EL MARTILLO — {titulo.upper()}"
    celda_t1.font = fuente_titulo
    celda_t1.fill = fondo_titulo
    celda_t1.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 30

    # Fila 2: Subtítulo informativo
    ws.merge_cells(f"A2:{ultima_letra}2")
    celda_t2 = ws["A2"]
    celda_t2.value = f"Reporte generado desde el sistema de inventario ({len(filas)} registros incluidos)"
    celda_t2.font = fuente_sub
    celda_t2.fill = fondo_subtitulo
    celda_t2.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[2].height = 20

    # Fila 4: Encabezados de la tabla
    fila_header = 4
    ws.row_dimensions[fila_header].height = 24
    for col_idx, texto_col in enumerate(encabezados, start=1):
        c = ws.cell(row=fila_header, column=col_idx, value=texto_col)
        c.font = fuente_encabezado
        c.fill = fondo_encabezado
        c.border = borde_celda
        c.alignment = Alignment(horizontal="center", vertical="center")

    # Filas de datos con cebreado (alternancia de color) y bordes de tabla
    fila_actual = 5
    for indice_fila, datos_fila in enumerate(filas):
        ws.row_dimensions[fila_actual].height = 20
        relleno = fondo_impar if indice_fila % 2 == 0 else fondo_par

        for col_idx, valor in enumerate(datos_fila, start=1):
            c = ws.cell(row=fila_actual, column=col_idx, value=valor)
            c.font = fuente_celda
            c.fill = relleno
            c.border = borde_celda

            if col_idx in cols_moneda and isinstance(valor, (int, float)):
                c.number_format = "$#,##0"
                c.alignment = Alignment(horizontal="right", vertical="center")
            elif isinstance(valor, (int, float)):
                c.alignment = Alignment(horizontal="center", vertical="center")
            else:
                c.alignment = Alignment(horizontal="left", vertical="center")

        fila_actual = fila_actual + 1

    # Fila final de TOTAL GENERAL
    if fila_total:
        ws.row_dimensions[fila_actual].height = 24
        for col_idx, valor in enumerate(fila_total, start=1):
            c = ws.cell(row=fila_actual, column=col_idx, value=valor)
            c.font = fuente_total
            c.fill = fondo_total
            c.border = borde_total

            if col_idx in cols_moneda and isinstance(valor, (int, float)):
                c.number_format = "$#,##0"
                c.alignment = Alignment(horizontal="right", vertical="center")
            elif isinstance(valor, (int, float)):
                c.alignment = Alignment(horizontal="center", vertical="center")
            else:
                c.alignment = Alignment(horizontal="left", vertical="center")

    # Ajustar automáticamente el ancho de cada columna
    for col_idx in range(1, num_cols + 1):
        letra = get_column_letter(col_idx)
        max_largo = len(str(encabezados[col_idx - 1]))
        for fila_r in range(4, fila_actual + 1):
            val = ws.cell(row=fila_r, column=col_idx).value
            if val is not None:
                texto = f"${val:,.0f}" if (col_idx in cols_moneda and isinstance(val, (int, float))) else str(val)
                if len(texto) > max_largo:
                    max_largo = len(texto)
        ws.column_dimensions[letra].width = max(max_largo + 5, 14)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}.xlsx"'
    wb.save(response)
    return response


def descargar_excel(request):
    seccion = request.GET.get("seccion", "stock_general")

    # 1. Resumen por categorías
    if seccion == "resumen_categorias":
        resumen = Categoria.objects.annotate(
            cantidad_productos=Count("productos"),
            precio_promedio=Avg("productos__precio"),
            stock_total=Sum("productos__stock"),
        ).order_by("nombre")

        encabezados = ["Categoría", "Cantidad de Productos", "Precio Promedio CLP", "Stock Acumulado", "Valorizado Estimado CLP"]
        filas = []
        total_prods = 0
        total_stock = 0
        total_valorizado = 0
        suma_promedios = 0

        for cat in resumen:
            prom = int(round(cat.precio_promedio)) if cat.precio_promedio is not None else 0
            stock = cat.stock_total or 0
            valorizado_cat = prom * stock
            filas.append([cat.nombre, cat.cantidad_productos, prom, stock, valorizado_cat])
            total_prods = total_prods + cat.cantidad_productos
            total_stock = total_stock + stock
            total_valorizado = total_valorizado + valorizado_cat
            suma_promedios = suma_promedios + prom

        prom_general = int(round(suma_promedios / len(filas))) if filas else 0
        fila_total = ["TOTAL GENERAL", total_prods, prom_general, total_stock, total_valorizado]

        return generar_respuesta_xls(
            "reporte_resumen_categorias",
            "Resumen de Inventario por Categoría",
            encabezados,
            filas,
            fila_total=fila_total,
            cols_moneda=[3, 5],
        )

    # 2. Stock crítico
    if seccion == "stock_critico":
        productos_criticos = (
            Producto.objects.select_related("categoria")
            .filter(stock__lte=10)
            .order_by("stock", "nombre")
        )
        encabezados = ["ID", "Producto", "Categoría", "Precio Unitario CLP", "Stock Actual", "Valorizado CLP", "Estado"]
        filas = []
        suma_stock_critico = 0
        suma_valor_critico = 0

        for p in productos_criticos:
            nombre_cat = p.categoria.nombre if p.categoria else "Sin categoría"
            estado = "Sin stock" if p.stock == 0 else "Stock crítico"
            valorizado = p.precio * p.stock
            filas.append([p.id, p.nombre, nombre_cat, p.precio, p.stock, valorizado, estado])
            suma_stock_critico = suma_stock_critico + p.stock
            suma_valor_critico = suma_valor_critico + valorizado

        fila_total = ["TOTAL", f"{len(filas)} productos en alerta", "—", "—", suma_stock_critico, suma_valor_critico, "—"]
        return generar_respuesta_xls(
            "reporte_stock_critico",
            "Control de Reposición y Stock Crítico",
            encabezados,
            filas,
            fila_total=fila_total,
            cols_moneda=[4, 6],
        )

    # 3. Registro global de ventas y pedidos
    if seccion == "ventas":
        pedidos = Pedido.objects.select_related("usuario").prefetch_related("detalles").all()
        encabezados = [
            "N° Pedido",
            "Fecha",
            "Cliente",
            "Correo",
            "Producto",
            "Cantidad",
            "Precio Unitario CLP",
            "Subtotal Línea CLP",
        ]
        filas = []
        total_unidades = 0
        total_ingresos = 0

        for ped in pedidos:
            fecha_str = ped.fecha.strftime("%d/%m/%Y %H:%M")
            correo = ped.usuario.email or "-"
            detalles = ped.detalles.all()
            if detalles:
                for d in detalles:
                    sub = d.subtotal()
                    filas.append([
                        f"#{ped.id}",
                        fecha_str,
                        ped.usuario.username,
                        correo,
                        d.nombre_producto,
                        d.cantidad,
                        d.precio_unitario,
                        sub,
                    ])
                    total_unidades = total_unidades + d.cantidad
                    total_ingresos = total_ingresos + sub
            else:
                filas.append([f"#{ped.id}", fecha_str, ped.usuario.username, correo, "-", 0, 0, ped.total])
                total_ingresos = total_ingresos + ped.total

        fila_total = ["TOTAL VENTAS", f"{pedidos.count()} pedidos", "—", "—", "—", total_unidades, "—", total_ingresos]
        return generar_respuesta_xls(
            "registro_global_ventas",
            "Registro Global de Pedidos y Ventas",
            encabezados,
            filas,
            fila_total=fila_total,
            cols_moneda=[7, 8],
        )

    # 4. Stock por categoría específica (ej: cat_1, cat_2...) o Stock General
    productos = Producto.objects.select_related("categoria").all()
    nombre_archivo = "inventario_stock_general"
    titulo = "Inventario General de Stock"

    if seccion.startswith("cat_"):
        cat_id = seccion.replace("cat_", "")
        if cat_id.isdigit():
            categoria = Categoria.objects.filter(id=int(cat_id)).first()
            if categoria:
                productos = productos.filter(categoria=categoria)
                nombre_archivo = f"stock_{categoria.nombre.lower()}"
                titulo = f"Inventario de Stock - Categoría {categoria.nombre}"

    encabezados = ["ID", "Producto", "Categoría", "Precio Unitario CLP", "Stock Disponible", "Valorizado CLP"]
    filas = []
    suma_stock = 0
    suma_valorizado = 0

    for p in productos:
        nombre_cat = p.categoria.nombre if p.categoria else "Sin categoría"
        valorizado = p.precio * p.stock
        filas.append([p.id, p.nombre, nombre_cat, p.precio, p.stock, valorizado])
        suma_stock = suma_stock + p.stock
        suma_valorizado = suma_valorizado + valorizado

    fila_total = ["TOTAL GENERAL", f"{len(filas)} productos", "—", "—", suma_stock, suma_valorizado]
    return generar_respuesta_xls(
        nombre_archivo,
        titulo,
        encabezados,
        filas,
        fila_total=fila_total,
        cols_moneda=[4, 6],
    )





