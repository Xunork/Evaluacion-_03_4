from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from productos.models import Categoria, Producto, Pedido


PALETA_CATEGORIAS = {
    "Herramientas": ("#ea580c", "#fed7aa", "🔨"),
    "Fijaciones": ("#475569", "#e2e8f0", "🔩"),
    "Pinturas": ("#0284c7", "#bae6fd", "🎨"),
    "Electricidad": ("#ca8a04", "#fef08a", "⚡"),
    "Plomería": ("#0d9488", "#99f6e4", "🔧"),
}


def generar_svg_producto(ruta_archivo, nombre, categoria):
    color_fuerte, color_suave, icono = PALETA_CATEGORIAS.get(
        categoria, ("#ea580c", "#fed7aa", "🧰")
    )
    nombre_corto = nombre[:22] + ("..." if len(nombre) > 22 else "")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 200" width="320" height="200">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{color_suave}"/>
      <stop offset="100%" stop-color="#ffffff"/>
    </linearGradient>
  </defs>
  <rect width="320" height="200" rx="16" fill="url(#bg)"/>
  <circle cx="160" cy="82" r="46" fill="#ffffff" stroke="{color_fuerte}" stroke-width="3"/>
  <text x="160" y="98" font-size="44" text-anchor="middle" font-family="sans-serif">{icono}</text>
  <rect x="24" y="142" width="272" height="36" rx="8" fill="{color_fuerte}"/>
  <text x="160" y="165" font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif">{nombre_corto}</text>
</svg>"""
    ruta_archivo.write_text(svg, encoding="utf-8")


class Command(BaseCommand):
    help = "Poblamiento inicial ferretería: cuentas genéricas + 40 productos con imágenes (ES3 Sección A)"

    def handle(self, *args, **kwargs):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@test.cl", "admin123")
            self.stdout.write("Admin creado: admin / admin123")
        else:
            u = User.objects.get(username="admin")
            u.set_password("admin123")
            u.is_staff = True
            u.is_superuser = True
            u.save()
            self.stdout.write("Admin actualizado: admin / admin123")

        if not User.objects.filter(username="cliente").exists():
            User.objects.create_user("cliente", "cliente@test.cl", "cliente123")
            self.stdout.write("Cliente creado: cliente / cliente123")
        else:
            u = User.objects.get(username="cliente")
            u.set_password("cliente123")
            u.save()
            self.stdout.write("Cliente actualizado: cliente / cliente123")

        Pedido.objects.all().delete()
        Producto.objects.all().delete()
        Categoria.objects.all().delete()

        carpeta_img = Path(settings.BASE_DIR) / "static" / "img" / "productos"
        carpeta_img.mkdir(parents=True, exist_ok=True)
        generar_svg_producto(carpeta_img / "default.svg", "Producto Ferretería", "Herramientas")

        cats = {
            "Herramientas": "Manuales y eléctricas",
            "Fijaciones": "Tornillería, tarugos, adhesivos",
            "Pinturas": "Pinturas, brochas y acabados",
            "Electricidad": "Cables, enchufes e iluminación",
            "Plomería": "Gasfitería y agua",
        }
        for nombre, desc in cats.items():
            Categoria.objects.get_or_create(nombre=nombre, defaults={"descripcion": desc})

        prods = [
            ("Martillo carpintero 16oz", "Martillo mango fibra, uña curva.", 12990, 25, "Herramientas"),
            ("Set destornilladores 12 piezas", "Phillips y paleta imantados.", 15990, 18, "Herramientas"),
            ("Alicate universal 8 pulg", "Alicate corte y agarre profesional.", 8990, 30, "Herramientas"),
            ("Llave ajustable 10 pulg", "Llave francesa acero cromado.", 11990, 20, "Herramientas"),
            ("Huincha de medir 5m", "Cinta métrica con freno.", 5990, 40, "Herramientas"),
            ("Nivel de aluminio 60cm", "Nivel 3 burbujas alta precisión.", 13990, 12, "Herramientas"),
            ("Serrucho 20 pulg", "Serrucho dientes templados.", 14990, 10, "Herramientas"),
            ("Caja de herramientas 19 pulg", "Caja plástica con bandeja.", 19990, 8, "Herramientas"),
            ("Taladro percutor 750W", "Taladro 13mm con maletín.", 54990, 6, "Herramientas"),
            ("Esmeril angular 4 1/2", "Esmeril 840W con disco.", 45990, 7, "Herramientas"),
            ("Tornillos madera 4x40 caja 100", "Tornillos zincados Phillips.", 4990, 50, "Fijaciones"),
            ("Tarugos plásticos 8mm bolsa 50", "Tarugos universales grises.", 3490, 60, "Fijaciones"),
            ("Clavos 2 pulg x 1kg", "Clavos corrientes con cabeza.", 3990, 45, "Fijaciones"),
            ("Pernos hexagonales M8 caja 25", "Pernos zincados con tuerca.", 6990, 30, "Fijaciones"),
            ("Silicona selladora transparente", "Cartucho 300ml multiuso.", 2990, 35, "Fijaciones"),
            ("Cinta teflón 12mm x 10m", "Sella roscas gasfitería.", 1490, 80, "Fijaciones"),
            ("Pegamento epóxico 2 toneladas", "Adhesivo 2 componentes 28g.", 6490, 18, "Fijaciones"),
            ("Candado 50mm acero", "Candado cuerpo acero 3 llaves.", 8990, 14, "Fijaciones"),
            ("Pintura látex blanco 5L", "Látex interior mate lavable.", 24990, 10, "Pinturas"),
            ("Esmalte sintético negro 1L", "Esmalte brillante metal/madera.", 8990, 15, "Pinturas"),
            ("Rodillo 23cm + bandeja", "Set rodillo chiporro antigota.", 5990, 25, "Pinturas"),
            ("Brocha profesional 3 pulg", "Brocha cerda sintética.", 3990, 30, "Pinturas"),
            ("Lija madera grano 120 pack 5", "Lijas 9x11 pulg.", 2490, 50, "Pinturas"),
            ("Diluyente aguarrás 1L", "Diluyente pinturas y limpieza.", 4990, 20, "Pinturas"),
            ("Cinta masking 24mm x 40m", "Cinta enmascarar multiuso.", 1990, 45, "Pinturas"),
            ("Pasta muro 5kg", "Pasta acrílica interior.", 7990, 16, "Pinturas"),
            ("Cable THHN 12AWG rollo 10m", "Cable cobre rojo/negro.", 12990, 14, "Electricidad"),
            ("Interruptor simple embutido", "Interruptor 10A blanco.", 2490, 60, "Electricidad"),
            ("Enchufe doble 10A", "Enchufe embutido con tierra.", 3490, 55, "Electricidad"),
            ("Foco LED 9W E27 pack 2", "Ampolletas luz cálida.", 5990, 40, "Electricidad"),
            ("Alargador 5m 3 salidas", "Alargador con interruptor.", 8990, 16, "Electricidad"),
            ("Linterna LED recargable", "Linterna USB 1000 lúmenes.", 11990, 12, "Electricidad"),
            ("Cinta aislante negra 20m", "Cinta PVC 19mm.", 1490, 70, "Electricidad"),
            ("Llave jardín bronce 1/2", "Llave bola jardín pesada.", 7990, 18, "Plomería"),
            ("Flexible agua 40cm par", "Flexibles trenzados HI-HI.", 5990, 22, "Plomería"),
            ("Válvula bola 1/2 pulg", "Válvula corte bronce.", 6990, 20, "Plomería"),
            ("Sifón lavaplatos plástico", "Sifón simple con registro.", 4990, 15, "Plomería"),
            ("Soldadura estaño 100g", "Rollo estaño plomería.", 8990, 10, "Plomería"),
            ("Guantes seguridad anticorte", "Guantes poliuretano talla L.", 5990, 28, "Plomería"),
            ("Teflón líquido 50ml", "Sellador roscas alta presión.", 5490, 24, "Plomería"),
        ]

        indice = 1
        for nombre, desc, precio, stock, cat_nombre in prods:
            cat = Categoria.objects.get(nombre=cat_nombre)
            nombre_archivo = f"prod_{indice}.svg"
            generar_svg_producto(carpeta_img / nombre_archivo, nombre, cat_nombre)
            ruta_web = f"/static/img/productos/{nombre_archivo}"

            Producto.objects.create(
                nombre=nombre,
                descripcion=desc,
                precio=precio,
                stock=stock,
                imagen=ruta_web,
                categoria=cat,
            )
            indice = indice + 1

        self.stdout.write(self.style.SUCCESS(f"Ferretería lista: {Producto.objects.count()} productos con imágenes."))
