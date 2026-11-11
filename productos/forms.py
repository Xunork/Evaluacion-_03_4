from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Producto, Categoria


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
