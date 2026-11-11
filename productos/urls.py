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
]
