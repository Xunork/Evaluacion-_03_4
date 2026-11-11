from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing, name="inicio"),
    path("catalogo/", views.tienda, name="tienda"),
    path("producto/<int:pk>/", views.detalle, name="detalle"),
    path("login/", views.vista_login, name="login"),
    path("logout/", views.vista_logout, name="logout"),
    path("registro/", views.vista_registro, name="registro"),
    path("carrito/", views.carrito_ver, name="carrito"),
    path("carrito/agregar/<int:pk>/", views.carrito_agregar, name="carrito_agregar"),
    path("carrito/quitar/<int:pk>/", views.carrito_quitar, name="carrito_quitar"),
    path("carrito/actualizar/<int:pk>/", views.carrito_actualizar, name="carrito_actualizar"),
    path("checkout/", views.checkout, name="checkout"),
    path("mis-pedidos/", views.mis_pedidos, name="mis_pedidos"),
    # Rutas Etapa 1: CRUD web con formularios
    path("panel/", views.panel_admin, name="panel_admin"),
    path("panel/nuevo/", views.producto_crear, name="producto_crear"),
    path("panel/editar/<int:pk>/", views.producto_editar, name="producto_editar"),
    path("panel/eliminar/<int:pk>/", views.producto_eliminar, name="producto_eliminar"),
    path("panel/categorias/", views.categorias_admin, name="categorias_admin"),
    # Rutas Etapa 2: Reportes con ORM
    path("reporte-resumen/", views.reporte_resumen, name="reporte_resumen"),
    path("reporte-critico/", views.reporte_critico, name="reporte_critico"),
]
