from django.db import models
from django.contrib.auth.models import User


class Categoria(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "categorías"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, default="")
    precio = models.PositiveIntegerField(help_text="Precio en CLP")
    stock = models.PositiveIntegerField(default=0)
    imagen = models.CharField(
        max_length=255,
        blank=True,
        default="/static/img/productos/default.jpg",
        help_text="Ruta o URL de la imagen del producto"
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="productos"
    )

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} (${self.precio} - stock: {self.stock})"


class Pedido(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pedidos")
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario.username} - ${self.total}"


class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    nombre_producto = models.CharField(max_length=120, default="")
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.PositiveIntegerField(default=0)

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.nombre_producto} x{self.cantidad}"


class ConsultaCliente(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField()
    mensaje = models.TextField()
    producto_interes = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultas"
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.nombre} ({self.correo}) - {self.fecha.strftime('%d/%m/%Y %H:%M')}"

