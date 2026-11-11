from django.contrib import admin
from .models import Categoria, Producto, Pedido, DetallePedido, ConsultaCliente


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "descripcion")
    search_fields = ("nombre",)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "categoria", "precio", "stock")
    list_filter = ("categoria",)
    search_fields = ("nombre", "descripcion")


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "fecha", "total")


@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "pedido", "nombre_producto", "cantidad", "precio_unitario")


@admin.register(ConsultaCliente)
class ConsultaClienteAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "correo", "producto_interes", "fecha")
    list_filter = ("fecha", "producto_interes")
    search_fields = ("nombre", "correo", "mensaje")

