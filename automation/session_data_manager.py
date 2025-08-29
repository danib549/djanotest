# session_data_manager.py
import logging
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.http import HttpRequest
from typing import Optional, List, Dict, Any
import uuid
# Import the data structure definitions
from .script_data import ScriptData, StepData, ParameterConfig
# Import the database manager
from .script_db_manager import Script_db_Manager

logger = logging.getLogger(__name__)

# Central session keys
SESSION_SCRIPT_KEY = 'current_script_data'
SESSION_META_KEY = 'current_script_meta'
SESSION_ARCHITECT_KEY = 'automation_architect_list'
SESSION_CONTEXT_PROJECT_ID = 'context_project_id'

class ScriptDataManager:
    def __init__(self, request: HttpRequest):
        self.request = request
        self.session = request.session

    # --- Core Session Management (Working with Dictionaries) ---

    def get_script_data(self) -> Dict[str, Any]:
        """Retrieves the script data dictionary from the session."""
        # Data is stored as a dictionary (JSON) in the session.
        session_data = self.session.get(SESSION_SCRIPT_KEY)

        if not session_data or not isinstance(session_data, dict):
            # Return a default empty structure if nothing is found
            return ScriptData.default_dict()
        
        # Ensure basic structure is present
        if 'steps' not in session_data:
            session_data['steps'] = []
        if 'variables' not in session_data:
            session_data['variables'] = []

        return session_data

    def save_script_data(self, script_data: Dict[str, Any]):
        """Saves the script data dictionary to the session."""
        # Data is stored directly as a dictionary.
        print(script_data)
        self.session[SESSION_SCRIPT_KEY] = script_data
        self.session.modified = True

    # --- Metadata and Context Management ---

    def get_meta(self) -> Dict[str, Any]:
        return self.session.get(SESSION_META_KEY, {})

    def update_meta(self, **kwargs):
        meta = self.get_meta()
        meta.update(kwargs)
        self.session[SESSION_META_KEY] = meta
        self.session.modified = True

    def clear_script_session(self):
        if SESSION_SCRIPT_KEY in self.session:
            del self.session[SESSION_SCRIPT_KEY]
        if SESSION_META_KEY in self.session:
            del self.session[SESSION_META_KEY]
        self.session.modified = True

    # Context Management (Assuming Project model exists and is imported)
    def set_context_project_id(self, project_id: int):
        self.session[SESSION_CONTEXT_PROJECT_ID] = project_id
        self.session.modified = True

    def get_context_project_id(self) -> Optional[int]:
        return self.session.get(SESSION_CONTEXT_PROJECT_ID)

    def _get_project_context(self): # -> Project: (Type hint removed for brevity if Project model isn't shown)
        """Helper to securely retrieve the project context for DB operations."""
        project_id = self.get_context_project_id()
        if not project_id:
             raise ValueError("Project context not set in session.")
        # Security check: Ensure user has access to this project
        # Assuming Project model is imported and available
        from .models import Project
        return get_object_or_404(Project, id=int(project_id), users=self.request.user)

    # --- Script Creation Workflow ---

    def initialize_script_session(self, project_id: int = None, test_name: str = None):
        """Initializes a new script session."""
        # Get existing data if not clearing
        existing_data = self.get_script_data() if not (project_id and test_name) else None
        
        if project_id and test_name:
            self.clear_script_session()
            # Initialize with the default dictionary structure
            script_data = ScriptData.default_dict()
            script_data['project'] = project_id
            script_data['test_name'] = test_name
            self.save_script_data(script_data)
            self.update_meta(max_loop_id=0, editing_script_id=None)
            self.set_context_project_id(project_id)
        elif existing_data and existing_data.get('project'):
            # Session already exists with project
            pass
        else:
            # Initialize empty session if needed
            script_data = ScriptData.default_dict()
            self.save_script_data(script_data)
            self.update_meta(max_loop_id=0, editing_script_id=None)

    def load_script_into_session(self, script_data_instance: ScriptData, script_id: int):
        """Loads an existing ScriptData instance (e.g., from DB) into the session as a dictionary."""

        # *** Convert the loaded Object into a Dictionary for session storage ***
        script_data_dict = script_data_instance.to_dict()
        self.save_script_data(script_data_dict)

        # Calculate max_loop_id from loaded steps (now working on the dictionary)
        max_id = 0
        for step in script_data_dict.get('steps', []):
            try:
                loop_id_val = step.get('loop_id')
                lid = int(loop_id_val) if loop_id_val else 0
                if lid > max_id:
                    max_id = lid
            except (ValueError, TypeError):
                continue

        self.update_meta(max_loop_id=max_id, editing_script_id=script_id)
        if script_data_instance.project:
            self.set_context_project_id(script_data_instance.project)

    def script_creator_add_or_edit_step(self, form_data: dict):
        """Adds or edits a step using form data, manipulating the session dictionary."""
        script_data = self.get_script_data()

        if script_data.get('project') is None:
             raise ValueError("No script initialized in session.")

        step_id_str = form_data.get('step_id')
        new_step_dict = form_data.copy()

        # 1. Restructure flat form data to match the nested dictionary structure.
        frame_errors = {
            'sync': new_step_dict.pop('sync', False),
            'length_plus': new_step_dict.pop('length_plus', False),
            'length_minus': new_step_dict.pop('length_minus', False),
            'sequence_number': new_step_dict.pop('sequence_number', False),
            'checksum': new_step_dict.pop('checksum', False),
        }
        new_step_dict['frame_errors'] = frame_errors

        # Process parameters - now handling JSON from the new parameter configuration modal
        parameters_json = new_step_dict.pop('parameters_json', '{}')
        try:
            import json
            parameters_dict = json.loads(parameters_json) if parameters_json else {}
        except (json.JSONDecodeError, TypeError):
            parameters_dict = {}
        
        # Process each parameter configuration to ensure all fields are present
        for param_id, config in parameters_dict.items():
            # Ensure each parameter has all the individual fields
            processed_config = {
                'parameter_id': config.get('parameter_id', param_id),
                'operator': config.get('operator', '+'),
                'value_manipulation': config.get('value_manipulation', 'no-change'),
                # Value Options
                'value_options': config.get('value_options', ''),
                'fixed_value': config.get('fixed_value', None),
                'min_value': config.get('min_value', None),
                'max_value': config.get('max_value', None),
                'resolution': config.get('resolution', None),
                'resolution_value': config.get('resolution_value', None),
                'enum_value': config.get('enum_value', None),
                'table_parameters': config.get('table_parameters', None),
                # Value Tolerance
                'value_tolerance': config.get('value_tolerance', None),
                'percentage': config.get('percentage', None),
                'value_tolerance_value': config.get('value_tolerance_value', None),
                # Time Tolerance
                'time_tolerance': config.get('time_tolerance', None),
                'time_to_reach_value': config.get('time_to_reach_value', None),
                'time_tolerance_value': config.get('time_tolerance_value', None),
            }
            parameters_dict[param_id] = processed_config

        new_step_dict['parameters'] = parameters_dict

        # 2. Add or Update the step in the 'steps' list
        if step_id_str:
            # Edit existing step
            try:
                step_id = int(step_id_str)
                index = step_id - 1
                if 0 <= index < len(script_data['steps']):
                    new_step_dict['step_id'] = step_id
                    script_data['steps'][index] = new_step_dict
                else:
                    raise IndexError("Step ID out of range for editing.")
            except (ValueError, TypeError):
                 raise ValueError("Invalid Step ID format.")
        else:
            # Add new step
            new_step_id = len(script_data['steps']) + 1
            new_step_dict['step_id'] = new_step_id
            script_data['steps'].append(new_step_dict)

        self.save_script_data(script_data)

    # --- Step Manipulation (Working with Dictionaries) ---

    def delete_step(self, step_id: int) -> Optional[Dict[str, Any]]:
        script_data = self.get_script_data()
        steps_list = script_data.get('steps', [])
        original_length = len(steps_list)

        # Filter out the step
        script_data['steps'] = [step for step in steps_list if step.get('step_id') != step_id]

        if len(script_data['steps']) == original_length:
            return None # Step not found

        # Reassign step IDs sequentially
        for i, step in enumerate(script_data['steps']):
            step['step_id'] = i + 1

        self.save_script_data(script_data)
        return script_data

    def move_step(self, step_id: int, direction: str) -> Optional[Dict[str, Any]]:
        script_data = self.get_script_data()
        script_steps = script_data.get('steps', [])

        try:
            # Ensure step_id is treated as int for index calculation
            index = int(step_id) - 1
        except ValueError:
            return None

        if index < 0 or index >= len(script_steps):
            return None

        # Loop constraint logic (accessing dictionary keys)
        if script_steps[index].get('Step_loop_enabled', False):
             return script_data

        if direction == 'up' and index > 0:
            if script_steps[index - 1].get('Step_loop_enabled', False):
                 return script_data
            # Swap steps and update IDs within the dictionaries
            script_steps[index], script_steps[index - 1] = script_steps[index - 1], script_steps[index]
            script_steps[index]['step_id'], script_steps[index - 1]['step_id'] = script_steps[index - 1]['step_id'], script_steps[index]['step_id']

        elif direction == 'down' and index < len(script_steps) - 1:
            if script_steps[index + 1].get('Step_loop_enabled', False):
                 return script_data
            # Swap steps and update IDs within the dictionaries
            script_steps[index], script_steps[index + 1] = script_steps[index + 1], script_steps[index]
            script_steps[index]['step_id'], script_steps[index + 1]['step_id'] = script_steps[index + 1]['step_id'], script_steps[index]['step_id']

        self.save_script_data(script_data)
        return script_data

    def get_step_by_id(self, step_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a dictionary representing the step."""
        script_data = self.get_script_data()
        steps_list = script_data.get('steps', [])
        try:
            index = int(step_id) - 1
            if 0 <= index < len(steps_list):
                return steps_list[index]
        except (ValueError, TypeError):
            pass
        return None

    # --- Loop Configuration (Working with Dictionaries) ---

    def update_step_loop_config(self, step_id: int, loop_config: dict):
        script_data = self.get_script_data()
        # Get the step dictionary
        step = self.get_step_by_id(step_id)

        if not step:
            raise ValueError("Step not found.")

        Step_loop_enable = loop_config.get('Step_loop_enable', False)

        if Step_loop_enable:
            detected_loop_id = self.Auto_step_loop_id_detector(step_id, loop_config.get('loop_id'))

            # Update the dictionary keys
            step['step_repeat'] = loop_config.get('step_repeat', '1')
            step['loop_repeat'] = loop_config.get('loop_repeat', '1')
            step['loop_id'] = str(detected_loop_id) # Store consistently as string
            step['loop_background'] = loop_config.get('loop_background', False)
            step['Step_loop_enabled'] = True
        else:
            step['Step_loop_enabled'] = False
            step['loop_id'] = '0'

        # Since 'step' is a reference to the dictionary within script_data['steps'],
        # updating 'step' directly updates script_data.
        self.save_script_data(script_data)
        return script_data

    def Auto_step_loop_id_detector(self, step_id, input_loop_id):
        
        def get_neighbor_loop_id(neighbor_id):
            try:
                step = self.get_step_by_id(neighbor_id)
                loop_id_val = step.get('loop_id') if step else None
                return int(loop_id_val) if loop_id_val else 0
            except (ValueError, TypeError):
                return 0

        previous_loop_id = get_neighbor_loop_id(step_id - 1)
        next_loop_id = get_neighbor_loop_id(step_id + 1)

        try:
            input_loop_id = int(input_loop_id) if input_loop_id else 0
        except (ValueError, TypeError):
            input_loop_id = 0

        meta = self.get_meta()
        max_loop_id = meta.get('max_loop_id', 0)

        # Logic remains the same
        if input_loop_id != 0:
            return_loop_id = input_loop_id
        elif previous_loop_id != 0 and next_loop_id == 0:
            return_loop_id = previous_loop_id
        elif next_loop_id != 0:
            return_loop_id = next_loop_id
        else:
            return_loop_id = max_loop_id + 1

        if return_loop_id > max_loop_id:
            self.update_meta(max_loop_id=return_loop_id)

        return return_loop_id

    # --- Variable Management (Working with Dictionaries) ---

    def add_variable(self, var_name, data_type, var_value):
        script_data = self.get_script_data()
        
        new_variable = {
            'id': len(script_data['variables']),
            'name': var_name,
            'data_type': data_type,
            'value': var_value,
        }
        script_data['variables'].append(new_variable)
        self.save_script_data(script_data)
        return script_data['variables']

    def edit_variable(self, variable_id: int, new_value=None, new_data_type=None):
        script_data = self.get_script_data()
        variables_list = script_data.get('variables', [])
        found = False
        for variable in variables_list:
            if variable.get('id') == variable_id:
                if new_value is not None:
                    variable['value'] = new_value
                if new_data_type is not None:
                    variable['data_type'] = new_data_type
                found = True
                break

        if found:
            self.save_script_data(script_data)
        return found, variables_list

    def delete_variable(self, variable_id: int) -> List[Dict[str, Any]]:
        """Deletes a variable from the script data."""
        script_data = self.get_script_data()
        variables = script_data.get('variables', [])
        
        # Remove the variable with the specified ID
        script_data['variables'] = [v for v in variables if v.get('id') != variable_id]
        
        # Reassign IDs to maintain sequence
        for i, var in enumerate(script_data['variables']):
            var['id'] = i
            
        self.save_script_data(script_data)
        return script_data['variables']

    # --- Database Interaction ---

    def save_script(self, user, project): # project: Project (Type hint removed for brevity)
        """
        Converts the session dictionary to a ScriptData object and saves it to the database.
        """
        script_data_dict = self.get_script_data()
        meta = self.get_meta()

        if not script_data_dict.get('steps'):
            raise ValueError("Cannot save an empty script.")

        # Ensure project ID is set in the dictionary before conversion
        script_data_dict['project'] = project.id

        # *** KEY LOGIC: Convert Dictionary to Object just before saving ***
        try:
            # This utilizes the Serializable.from_dict to reconstruct the objects
            script_data_instance = ScriptData.from_dict(script_data_dict)
        except Exception as e:
            logger.error(f"Error converting session dictionary to ScriptData object before save: {e}")
            raise ValueError(f"Script data structure is invalid and cannot be saved: {e}")

        # The DB manager expects a ScriptData instance
        db_manager = Script_db_Manager(script_data_instance, project)
        
        # Pass user and test_name for new scripts
        script_id = db_manager.save_script_to_db(
            editing_script_id=meta.get('editing_script_id'),
            user=user,
            test_name=script_data_dict.get('test_name')
        )
        
        # Store the script_id in meta for future edits if it's a new script
        if not meta.get('editing_script_id'):
            self.update_meta(editing_script_id=script_id)

        self.clear_script_session()

    def get_script_versions(self, script_id):
        """Helper to fetch script versions using the browsing context."""
        project = self._get_project_context()
        manager = Script_db_Manager(None, project)
        return manager.get_script_versions(script_id)

    # --- Automation Architect Management (Already uses dictionaries) ---

    def initialize_automation_architect_session(self):
        self.session[SESSION_ARCHITECT_KEY] = []
        self.session.modified = True

    def get_architect_list(self) -> List[Dict]:
        return self.session.get(SESSION_ARCHITECT_KEY, [])

    def save_architect_list(self, architect_list: List[Dict]):
        self.session[SESSION_ARCHITECT_KEY] = architect_list
        self.session.modified = True

    def add_script_to_automation(self, script_id, version_id):
        project = self._get_project_context()
        manager = Script_db_Manager(None, project)
        # Loads Object from DB
        script_data_instance = manager.load_script_version(script_id, version_id)

        if not script_data_instance:
            raise ValueError(f"Version {version_id} for Script ID {script_id} not found.")

        # Convert Object to Dictionary for Architect list
        script_dict = script_data_instance.to_dict()

        # Add metadata
        script_dict['type'] = 'script'
        script_dict['id'] = script_id
        script_dict['version_id'] = version_id
        script_dict['instance_id'] = str(uuid.uuid4())

        architect_list = self.get_architect_list()
        architect_list.append(script_dict)
        self.save_architect_list(architect_list)

    def add_delay_to_automation(self, delay):
        delay_data = {
            'type': 'delay',
            'delay': delay,
            'instance_id': str(uuid.uuid4())
        }
        architect_list = self.get_architect_list()
        architect_list.append(delay_data)
        self.save_architect_list(architect_list)

    def update_architect_variable(self, instance_id, variable_name, new_value=None, new_data_type=None):
        architect_list = self.get_architect_list()
        variable_updated = False

        for item in architect_list:
            if item.get('instance_id') == instance_id and item.get('type') == 'script':
                for variable in item.get('variables', []):
                    if variable['name'] == variable_name:
                        if new_value is not None:
                            variable['value'] = new_value
                        if new_data_type is not None:
                            variable['data_type'] = new_data_type
                        variable_updated = True
                        break
                if variable_updated:
                    break

        if variable_updated:
            self.save_architect_list(architect_list)

        return variable_updated