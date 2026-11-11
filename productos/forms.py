from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Producto, Categoria, ConsultaCliente


class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo electrónico")

    class Meta:
        model = User
        fields = ("username", "email")
        labels = {
            "username": "Nombre de usuario",
        }


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "categoria", "precio", "stock", "imagen", "descripcion"]
        labels = {
            "nombre": "Nombre del producto",
            "categoria": "Categoría",
            "precio": "Precio ($ CLP)",
            "stock": "Stock disponible",
            "imagen": "Ruta o URL de imagen (opcional)",
            "descripcion": "Descripción",
        }
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3, "placeholder": "Descripción breve del producto..."}),
            "imagen": forms.TextInput(attrs={"placeholder": "/static/img/productos/default.svg o URL https://..."}),
        }

    def clean_precio(self):
        precio = self.cleaned_data.get("precio")
        if precio is not None and precio <= 0:
            raise forms.ValidationError("El precio debe ser mayor a 0.")
        return precio


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion"]
        labels = {
            "nombre": "Nombre de la categoría",
            "descripcion": "Descripción",
        }
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 2}),
        }


class ConsultaClienteForm(forms.ModelForm):
    class Meta:
        model = ConsultaCliente
        fields = ["nombre", "correo", "producto_interes", "mensaje"]
        labels = {
            "nombre": "Tu nombre completo",
            "correo": "Correo electrónico",
            "producto_interes": "Producto de interés (opcional)",
            "mensaje": "Mensaje o consulta",
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Ej: Juan Pérez (mínimo 3 caracteres)"}),
            "correo": forms.EmailInput(attrs={"placeholder": "ejemplo@correo.cl"}),
            "mensaje": forms.Textarea(attrs={"rows": 4, "placeholder": "Escribe tu consulta (mínimo 10 caracteres)..."}),
        }
        error_messages = {
            "nombre": {
                "required": "El nombre es obligatorio.",
            },
            "correo": {
                "required": "El correo electrónico es obligatorio.",
                "invalid": "Ingresa un correo electrónico válido (ejemplo@dominio.cl).",
            },
            "mensaje": {
                "required": "El mensaje de la consulta es obligatorio.",
            },
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get("nombre", "").strip()
        if len(nombre) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres.")
        return nombre

    def clean_mensaje(self):
        mensaje = self.cleaned_data.get("mensaje", "").strip()
        if len(mensaje) < 10:
            raise forms.ValidationError("El mensaje debe tener al menos 10 caracteres.")
        return mensaje

