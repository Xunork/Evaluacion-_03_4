import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluacion_3.settings')
application = get_asgi_application()
