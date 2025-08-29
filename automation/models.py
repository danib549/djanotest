from cryptography.fernet import Fernet
from django.db import models
from django.contrib.auth.models import User
from .script_db_manager import Script_db_Manager
from django.db import models, connection


class Project(models.Model):

    name = models.CharField(max_length=100)
    users = models.ManyToManyField(User, related_name='projects')
    encryption_key = models.BinaryField()

    def save(self, *args, **kwargs):
        if not self.encryption_key:
            # Generate a new key if one does not exist, ensuring it's stored as bytes
            self.encryption_key = Fernet.generate_key()
        super(Project, self).save(*args, **kwargs)
        manager = Script_db_Manager(self, self)
        manager.create_project_table_script_versions( self.id)

    def delete(self, *args, **kwargs):
        table_name = f"project_{self.id}_scriptversion"
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name};")

        super(Project, self).delete(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_fernet(self):
        return Fernet(self.encryption_key)



class Script(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    test_name = models.CharField(max_length=100)
    script_version = models.IntegerField(default=0)

    def save_script(self, script_steps,script_version):
        manager = Script_db_Manager(self, self.project)
        manager.save_script(script_steps)




