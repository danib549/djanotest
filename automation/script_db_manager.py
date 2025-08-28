import os
import pickle
from django.conf import settings
from cryptography.fernet import Fernet
from django.db import connection

class Script_db_Manager:
    def __init__(self, script, project):
        self.script = script
        self.project = project

    def encrypt_data(self, data):
        fernet = self.project.get_fernet()
        return fernet.encrypt(pickle.dumps(data))

    def decrypt_data(self, encrypted_data):
        fernet = self.project.get_fernet()
        return pickle.loads(fernet.decrypt(encrypted_data))

    def save_script(self, script_steps):
        print("project id :",self.project.id)

        script_content = {
            'project': self.project.name,
            'steps': script_steps
        }
        print(script_content)

        encrypted_data = self.encrypt_data(script_content)
        self.script.script_data = encrypted_data
        self.save_script_to_db(encrypted_data)
        self.save_to_file(encrypted_data)


    def save_to_file(self, encrypted_data):
        project_folder = os.path.join(settings.MEDIA_ROOT, 'scripts', f'project_{self.project.id}')
        os.makedirs(project_folder, exist_ok=True)

        file_path = os.path.join(project_folder, f'script_{self.script.id}_{self.script.script_version}.ScriptQ')
        with open(file_path, 'wb') as f:
            f.write(encrypted_data)
    def decrypt_script(self, encrypted_data):
        return self.decrypt_data(encrypted_data)

    def load_script_version(self, version_number):
        table_name = f"project_{self.project.id}_scriptversion"

        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT script_data FROM {table_name}
                WHERE script_id = %s AND version_number = %s;
            """, [self.script.id, version_number])

            row = cursor.fetchone()
            if row:
                encrypted_data = row[0]
                return self.decrypt_script(encrypted_data)

        return None

    def create_project_table_script_versions(self, project_id):
        print("project id:", project_id)
        table_name = f"project_{project_id}_scriptversion"
        with connection.cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    script_id INTEGER NOT NULL REFERENCES automation_script(id),
                    version_number INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    script_data BLOB
                );
            """)

    def save_script_to_db(self,encrypted_data):
        if self.script.script_version == 0:
            self.script.script_version = 1
        else:
            self.script.script_version += 1
        self.script.save()
        print("script version :" , self.script.script_version)
        table_name = f"project_{self.project.id}_scriptversion"
        with connection.cursor() as cursor:
            cursor.execute(f"""
                INSERT INTO {table_name} (script_id, version_number, script_data, created_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP);
            """, [self.script.id, self.script.script_version, encrypted_data])
        
    def get_script_versions(self):

        table_name = f"project_{self.project.id}_scriptversion"
        
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT version_number, created_at FROM {table_name}
                WHERE script_id = %s ORDER BY version_number ASC;
            """, [self.script.id])

            rows = cursor.fetchall()
            versions = [{'version_number': row[0], 'created_at': row[1]} for row in rows]

        return versions