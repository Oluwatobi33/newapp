# taskapp/apps.py
from django.apps import AppConfig

class TaskappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'taskapp'

    def ready(self):
        # This prevents the built-in User model from being loaded
        from django.contrib.auth.models import User
        from django.db.models.signals import class_prepared
        
        def skip_builtin_user(sender, **kwargs):
            if sender.__name__ == "User" and sender.__module__ == "django.contrib.auth.models":
                raise class_prepared.SkipClass
                
        class_prepared.connect(skip_builtin_user)