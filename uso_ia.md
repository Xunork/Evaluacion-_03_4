# Uso de IA - Evaluacion 3

## Parte 1: Registro de consultas

### Consulta 1: Estructura inicial y poblamiento de productos
Prompt: "¿Como puedo organizar los modelos de Producto y Categoria en Django para un catalogo de ferreteria con 40 productos y cargar los datos iniciales con un comando?"
Resumen de respuesta: La IA propuso la estructura de modelos con clave foranea entre Producto y Categoria, junto con un comando personalizado seed.py para insertar las categorias y los 40 productos de ferreteria.
Que se uso o modifico: Se uso la base del comando seed agregando el campo de imagen en el modelo Producto para asociar cada herramienta con su foto en la carpeta static.

### Consulta 2: Formularios web para el CRUD del catalogo
Prompt: "¿Me puedes ayudar a armar las vistas de crear, editar y eliminar productos usando ModelForm para manejar todo desde la pagina en vez del admin?"
Resumen de respuesta: La IA mostro como crear la clase ProductoForm en forms.py y como usarla en las vistas recibiendo request.POST, ademas de una vista de confirmacion para eliminar registros por metodo POST.
Que se uso o modifico: Se adaptaron los nombres de las rutas y se cambiaron las redirecciones para que despues de crear, editar o borrar un producto el usuario vuelva al listado del catalogo.

### Consulta 3: Consultas con el ORM para los reportes
Prompt: "¿Como se usa annotate y aggregate en el ORM de Django para sacar la cantidad de productos, el promedio de precio y la suma de stock por categoria, y otro reporte que filtre el stock bajo?"
Resumen de respuesta: La IA explico como importar Count, Avg y Sum desde django.db.models para agrupar por categoria en una vista, y como usar filter(stock__lte=10) junto con order_by en la segunda vista.
Que se uso o modifico: Se agrego un ciclo simple en la vista para redondear los promedios a numeros enteros antes de pasarlos al contexto del template.

### Consulta 4: Validaciones en ModelForm y uso de sesiones
Prompt: "¿Como puedo validar el largo minimo del nombre y mensaje en un formulario de contacto con ModelForm y guardar en la sesion los ultimos 3 productos visitados?"
Resumen de respuesta: La IA indico como definir los metodos clean_nombre y clean_mensaje dentro del formulario y como guardar una lista de IDs en request.session recortando los primeros 3 elementos.
Que se uso o modifico: Se ajustaron los mensajes de error en espanol y se agrego tambien un contador de visitas al catalogo dentro de la misma sesion.

### Consulta 5: Opciones de diseno para el frontend
Prompt: "¿Que opciones de diseno y paleta de colores me recomiendas para que el frontend de la ferreteria se vea mas limpio, minimalista y profesional?"
Resumen de respuesta: La IA sugirio usar una paleta neutra con fondo claro, tarjetas blancas con bordes finos, tipografia limpia y contenedores de imagen con object-fit contain para que las fotos de los productos no se recorten.
Que se uso o modifico: Se aplicaron las variables de color en style.css y se corrigio especificamente el color del texto en los botones de los encabezados porque al principio quedaba negro sobre fondo negro.


## Parte 2: Explicacion del proceso

Para desarrollar esta evaluacion utilice la IA como guia cuando tenia dudas puntuales sobre la sintaxis de Django o cuando queria ver mejores opciones para estructurar las vistas y el diseno del frontend. En lugar de pedirle todo de una sola vez, fui consultando etapa por etapa segun lo que iba necesitando: primero el manejo de los formularios con ModelForm para el CRUD, despues las funciones de agregacion del ORM para los reportes y finalmente el tema de las validaciones y las sesiones.
Las respuestas que me funcionaron casi directo fueron las consultas del ORM con annotate, Count, Avg y Sum, y tambien la forma de validar campos en el formulario de clientes usando los metodos clean, porque la estructura era clara y cuadraba bien con los modelos que ya tenia creados.
Por otro lado, tuve que modificar y corregir varias cosas en la parte visual y en la integracion con mis templates. Por ejemplo, cuando le pedi recomendaciones para el CSS del frontend, algunas reglas de enlaces cambiaban el color de los botones y hacian que el texto de crear producto no se viera, asi que tuve que revisar el archivo de estilos y separar las clases de los botones. Tambien tuve que ajustar las imagenes de los productos y redondear los promedios de precios en la vista para que no salieran con decimales largos en la tabla del reporte.
Trabajar de esta forma me sirvio para entender mucho mejor como funcionan las consultas agrupadas del ORM en las vistas, como proteger y validar formularios con CSRF y ModelForm, y como usar request.session para recordar datos del usuario entre distintas paginas.
