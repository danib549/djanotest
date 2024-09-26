from django.http import JsonResponse
from .models import Script
from django.shortcuts import get_object_or_404

class ScriptDataManager:
    def __init__(self, request):
        self.request = request
        self.session = request.session

    def initialize_script_session(self):
        if 'script' not in self.session:
            self.session['script'] = []
            self.session.modified = True

    def add_or_edit_step(self, form):
        if 'script' not in self.session:
            raise ValueError("No script initialized in session.")

        step_id = form.cleaned_data.get('step_id')
        if not step_id:
            step_id = len(self.session['script']) + 1  # Assign new ID if not provided

        step_data = {
            'step_id': step_id,
            'environment': form.cleaned_data['environment'],
            'command': form.cleaned_data['command'],
            'sub_command': form.cleaned_data['sub_command'],
            'component': form.cleaned_data['component'],
            'packet': form.cleaned_data['packet'],
            'parameters': form.cleaned_data['parameters'],
            'value_manipulation': form.cleaned_data['value_manipulation'],
            'operator': form.cleaned_data['operator'],
            'min_value': form.cleaned_data.get('min_value', None),
            'max_value': form.cleaned_data.get('max_value', None),
            'resolution': form.cleaned_data.get('resolution', None),
            'resolution_value': form.cleaned_data.get('resolution_value', None),
            'fixed_value': form.cleaned_data.get('fixed_value', None),
            'enum_value': form.cleaned_data.get('enum_value', None),
            'at_time': form.cleaned_data['at_time'],
            'delay': form.cleaned_data['delay'],
            'value_tolerance': form.cleaned_data['value_tolerance'],
            'value_tolerance_value': form.cleaned_data['value_tolerance_value'],
            'time_tolerance': form.cleaned_data['time_tolerance'],
            'time_tolerance_value': form.cleaned_data['time_tolerance_value'],
            'frame_errors': {
                'sync': form.cleaned_data.get('sync', False),
                'length_plus': form.cleaned_data.get('length_plus', False),
                'length_minus': form.cleaned_data.get('length_minus', False),
                'sequence_number': form.cleaned_data.get('sequence_number', False),
                'checksum': form.cleaned_data.get('checksum', False)
            },
            'description': form.cleaned_data['description'] or ''
        }

        existing_step_index = next(
            (index for (index, d) in enumerate(self.session['script']) if d['step_id'] == step_data['step_id']), None)

        if existing_step_index is not None:
            self.session['script'][existing_step_index] = step_data
        else:
            # Add a new step
            self.session['script'].append(step_data)

        self.session.modified = True

        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'step_data': step_data})
        return None

    def get_step_from_session(self, step_id):
        try:
            return self.session['script'][step_id-1]
        except:
            raise ValueError("No script initialized in session.")

        # return None

    def save_script(self, user, project):
        script_id = self.session.get('editing_script_id')
        if script_id:
            script = get_object_or_404(Script, id=script_id, user=user)
        else:
            script = Script(user=user, project=project, test_name=self.session['test_name'])

        script.save_script(self.session['script'],self.session["script_version"])
        self.session.pop('editing_script_id', None)
        self.session.modified = True

    def delete_step(self, step_id):
        self.session['script'] = [step for step in self.session['script'] if step['step_id'] != step_id]

        for i, step in enumerate(self.session['script']):
            step['step_id'] = i + 1

        self.session.modified = True

        return self.session['script']

    def move_step(self, step_id, direction):
        script_steps = self.session['script']
        step_id = int(step_id)
        index = int(self.session['script'][step_id - 1]['step_id'] - 1)
        print(script_steps)
        print(index)
        if index is not None:
            if direction == 'up' and index > 0:
                script_steps[index], script_steps[index - 1] = script_steps[index - 1], script_steps[index]
                script_steps[index]['step_id'], script_steps[index - 1]['step_id'] = script_steps[index - 1]['step_id'], \
                script_steps[index]['step_id']
            elif direction == 'down' and index < len(script_steps) - 1:
                script_steps[index], script_steps[index + 1] = script_steps[index + 1], script_steps[index]
                script_steps[index]['step_id'], script_steps[index + 1]['step_id'] = script_steps[index + 1]['step_id'], \
                script_steps[index]['step_id']
            return script_steps
        else:
            return None


