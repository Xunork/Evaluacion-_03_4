# Evaluacion 3 - Ferreteria El Martillo

## Descripcion del proyecto
Aplicacion web de catalogo online para una ferreteria local desarrollada en Django (Seccion A). Permite ver el catalogo de 40 productos desde la base de datos SQLite, gestionar productos mediante formularios web (crear, editar y eliminar con confirmacion), revisar dos reportes generados con el ORM de Django, enviar consultas de clientes validadas con ModelForm y manejar sesiones para el carrito y los ultimos productos visitados.

## Como ejecutar el proyecto
1. Entrar a la carpeta del proyecto y activar el entorno virtual.
2. Ejecutar las migraciones con `python manage.py migrate`.
3. Cargar los 40 productos y usuarios de prueba con `python manage.py seed`.
4. Iniciar el servidor con `python manage.py runserver`.

## Credenciales de prueba
- Administrador: usuario `admin` / clave `admin123`
- Cliente: usuario `cliente` / clave `cliente123`

## Etapas y commits realizados
- `etapa-0-entorno`: Configuracion inicial del proyecto, modelos base y carga de los 40 productos en la base de datos.
- `etapa-1-crud`: Formularios web para crear, editar y eliminar productos con confirmacion.
- `etapa-2-reportes`: Reporte de resumen por categoria (annotate y aggregate) y reporte de stock critico (filter y order_by).
- `etapa-3-clientes`: Modelo y formulario de consultas de clientes con validaciones, token CSRF y sesiones de productos visitados.
- `Mejora-Diseño`: Ajuste visual minimalista y carga de fotografias reales para los 40 productos.
- `entrega-final`: Incorporacion de la documentacion de uso de IA y revision final.
