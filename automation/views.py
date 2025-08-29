# views.py
import logging
import os
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

# Import forms and models
from .forms import ScriptForm, GlobalSettingsForm
from .models import Project, Script
# Import the refactored managers
from .session_data_manager import ScriptDataManager
from .script_db_manager import Script_db_Manager

# Setup logger
logger = logging.getLogger('automation_views')

# --- Script Creation Workflow Views ---

@login_required
def global_settings(request):
    """Handle global settings form to initialize script creation."""
    try:
        if request.method == 'POST':
            form = GlobalSettingsForm(user=request.user, data=request.POST)
            if form.is_valid():
                project = form.cleaned_data['project']
                test_name_base = form.cleaned_data['test_name']

                # Security Check
                if not project.users.filter(id=request.user.id).exists():
                    raise PermissionDenied("You don't have access to this project")

                data_manager = ScriptDataManager(request)
                test_name = f"{test_name_base} - Time - {datetime.now().strftime('%Y-%m-%d %H-%M-%S')}"

                # Initializes the session with a dictionary structure
                data_manager.initialize_script_session(project.id, test_name)

                messages.success(request, 'Global settings saved successfully')
                return redirect('create_script')
            else:
                messages.error(request, 'Please correct the errors below')
        else:
            # Clear previous session if the user visits the page directly (GET)
            ScriptDataManager(request).clear_script_session()
            form = GlobalSettingsForm(user=request.user)

        return render(request, 'automation/global_settings.html', {'form': form})

    except Exception as e:
        logger.error(f"Error in global_settings view: {e}")
        messages.error(request, f'An unexpected error occurred: {e}')
        return redirect('error')

@login_required
def create_script(request):
    """Main view for creating and editing script steps."""
    script_data_manager = ScriptDataManager(request)
    script_data_manager.initialize_script_session()
    
    # Get the script data dictionary from the session
    current_script_data = script_data_manager.get_script_data()

    # Check if session is initialized properly (accessing dictionary keys)
    project_id = current_script_data.get('project')
    test_name = current_script_data.get('test_name')

    if not project_id or not test_name:
        messages.warning(request, 'Session expired or not initialized. Please configure settings or load a script.')
        return redirect('global_settings')

    # Security check
    project = get_object_or_404(Project, id=project_id, users=request.user)

    if request.method == 'POST':
        form = ScriptForm(request.POST)
        if form.is_valid():
            try:
                if request.POST.get('action') == 'save':
                    with transaction.atomic():
                        # Manager handles conversion from Dict to Object here
                        script_data_manager.save_script(request.user, project)
                        messages.success(request, 'Script saved successfully')
                        return redirect('script_list')

                else:
                    # Add or Edit Step (Manager handles dictionary manipulation)
                    script_data_manager.script_creator_add_or_edit_step(form.cleaned_data)

                    # Handle HTMX response
                    if request.headers.get('HX-Request'):
                        # Reload data dictionary after modification
                        updated_script_data = script_data_manager.get_script_data()
                        # Data is already serialized (it's a dictionary)
                        return render(request, 'partials/step_list.html', {
                            'session_script': updated_script_data.get('steps', [])
                        })
            except ValueError as e:
                 # Catch validation errors (e.g. from save_script conversion)
                logger.error(f"Validation error during script creation POST: {e}")
                messages.error(request, f"An error occurred: {e}")
                if request.headers.get('HX-Request'):
                    return HttpResponseBadRequest(f"Error processing request: {e}")
            except Exception as e:
                logger.error(f"Error during script creation POST: {e}", exc_info=True)
                messages.error(request, f"An unexpected error occurred: {e}")
                if request.headers.get('HX-Request'):
                    return HttpResponseBadRequest(f"Error processing request: {e}")

        else:
            # Handle form validation errors
            logger.warning(f"Invalid form submission: {form.errors}")
            if request.headers.get('HX-Request'):
                return HttpResponseBadRequest('Invalid form data')
            messages.error(request, 'Please correct the form errors')

    # GET request: Render the main creation page
    # Data is already a dictionary, ready for the template context
    context = {
        'form': ScriptForm(),
        'session_script': current_script_data.get('steps', []),
        'variables': current_script_data.get('variables', []),
        'test_name': test_name,
    }
    return render(request, 'automation/create_script.html', context)

# --- Variable Management Views ---

@login_required
def add_variable(request):
    if request.method == 'POST':
        var_name = request.POST.get('var_name')
        data_type = request.POST.get('data_type')
        var_value = request.POST.get('var_value')

        script_data_manager = ScriptDataManager(request)
        variables = script_data_manager.add_variable(var_name, data_type, var_value)

        # Render and return only the variable table to be updated
        return render(request, 'partials/variable_table.html', {'variables': variables})

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def delete_variable(request, variable_id):
    if request.method == 'DELETE':
        script_data_manager = ScriptDataManager(request)
        try:
            variables = script_data_manager.delete_variable(int(variable_id))
            # Render the updated table
            return render(request, 'partials/variable_table.html', {'variables': variables})
        except ValueError:
            return JsonResponse({'error': 'Invalid variable ID'}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)

# --- Step Management Views (HTMX/AJAX) ---

@login_required
def delete_step(request, step_id):
    if request.method == 'POST':
        script_data_manager = ScriptDataManager(request)
        try:
            # Manager handles dictionary manipulation
            updated_script_data = script_data_manager.delete_step(int(step_id))
        except ValueError:
             return JsonResponse({'error': 'Invalid step ID'}, status=400)

        if updated_script_data is None:
             if request.headers.get('HX-Request'):
                 return HttpResponse(status=204) # No Content
             return JsonResponse({'error': 'Step not found'}, status=404)

        if request.headers.get('HX-Request'):
            # Data is already a dictionary
            return render(request, 'partials/step_list.html', {
                'session_script': updated_script_data.get('steps', [])
            })

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def load_step(request, step_id):
    """AJAX view to load step data into the form for editing."""
    script_data_manager = ScriptDataManager(request)
    try:
        # Get the step dictionary
        step_data_dict = script_data_manager.get_step_by_id(int(step_id))
    except ValueError:
        return JsonResponse({'error': 'Invalid step ID'}, status=400)

    if step_data_dict:
        # CRITICAL: Flatten nested structures (like 'frame_errors' and 'parameters') because the form expects flat fields.
        response_data = step_data_dict.copy()
        
        # Flatten frame_errors
        frame_errors = response_data.pop('frame_errors', {})
        if isinstance(frame_errors, dict):
            response_data.update(frame_errors)
        
        # Handle parameters based on environment
        parameters = response_data.pop('parameters', {})
        if parameters:
            # For environment 2, we need to send parameters with indices
            if response_data.get('environment') == '2':
                for idx, (param_name, param_config) in enumerate(parameters.items(), 1):
                    response_data[f'param_name_{idx}'] = param_name
                    if isinstance(param_config, dict):
                        for key, value in param_config.items():
                            response_data[f'{key}_{idx}'] = value
            else:
                # For environment 1, single parameter
                if parameters:
                    first_param = list(parameters.keys())[0]
                    response_data['selected_parameter'] = first_param
                    param_config = parameters[first_param]
                    if isinstance(param_config, dict):
                        response_data['parameter_value'] = param_config.get('value')
                        response_data['expected_value'] = param_config.get('expected_value')
        
        return JsonResponse(response_data)

    return JsonResponse({'error': 'Step not found'}, status=404)

@csrf_exempt
@login_required
def update_step_order(request):
    if request.method == 'POST':
        step_id = request.POST.get('step_id')
        direction = request.POST.get('direction')

        if not step_id or not direction:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        script_data_manager = ScriptDataManager(request)
        try:
            # Manager handles dictionary manipulation
            updated_script_data = script_data_manager.move_step(int(step_id), direction)
        except ValueError:
            return JsonResponse({'error': 'Invalid step ID'}, status=400)

        if updated_script_data:
            # Render the updated list for HTMX (data is a dictionary)
            return render(request, 'partials/step_list.html', {
                'session_script': updated_script_data.get('steps', [])
            })

        return JsonResponse({'error': 'Step not found or move invalid'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def update_step_loop(request):
    if request.method == 'POST':
        script_manager = ScriptDataManager(request)
        try:
            step_id = int(request.POST.get('step_id'))

            # Extract loop configuration from POST data
            loop_config = {
                'step_repeat': request.POST.get('step_repeat'),
                'loop_repeat': request.POST.get('loop_repeat'),
                'loop_id': request.POST.get('loop_id'),
                'loop_background': request.POST.get('loop_background') == "on",
                'Step_loop_enable': request.POST.get('Step_loop_enable') == "on",
            }

            # Manager handles dictionary manipulation
            updated_script_data = script_manager.update_step_loop_config(step_id, loop_config)

            # Render and return the updated step list for HTMX (data is a dictionary)
            return render(request, 'partials/step_list.html', {
                'session_script': updated_script_data.get('steps', [])
            })

        except (ValueError, TypeError) as e:
            logger.error(f"Error updating step loop: {e}")
            return HttpResponseBadRequest(f"Invalid data provided: {e}")

    return redirect('error')

# --- Script Loading/Listing Views ---

@login_required
def get_scripts_by_project(request):
    project_id = request.GET.get('project_id')
    try:
        if project_id:
            project = get_object_or_404(Project, id=project_id, users=request.user)
            scripts = Script.objects.filter(project=project, user=request.user)
        else:
            scripts = Script.objects.filter(user=request.user)
    except Exception as e:
        logger.error(f"Error getting scripts by project: {e}")
        scripts = Script.objects.none()

    return render(request, 'partials/script_list.html', {'scripts': scripts})

@login_required
def script_list(request):
    user_projects = Project.objects.filter(users=request.user)
    selected_project_id = request.GET.get('project_id')

    if selected_project_id:
        selected_project = get_object_or_404(Project, id=selected_project_id, users=request.user)
        scripts = Script.objects.filter(user=request.user, project=selected_project)
    else:
        scripts = None

    return render(request, 'automation/script_list.html', {
        'scripts': scripts,
        'projects': user_projects,
        'selected_project_id': selected_project_id,
    })

@login_required
def load_script(request):
    """Handles the form submission to load a script version into the creator."""
    if request.method == 'POST':
        script_id = request.POST.get('script_id')
        version_id = request.POST.get('version_id')

        data_manager = ScriptDataManager(request)

        try:
            # Get the script and ensure user has access
            script = get_object_or_404(Script, id=script_id, user=request.user)
            project = script.project
            
            # Security check
            if not project.users.filter(id=request.user.id).exists():
                raise PermissionDenied("You don't have access to this project")
            
            db_manager = Script_db_Manager(None, project)
            # Load the ScriptData object (Deserialized via Pickle by DB Manager)
            script_data_instance = db_manager.load_script_version(script_id, version_id)

            if script_data_instance:
                # Load into session (Session Manager converts Object -> Dict here)
                data_manager.load_script_into_session(script_data_instance, int(script_id))

                messages.success(request, f"Script version {version_id} loaded successfully.")
                return redirect('create_script')
            else:
                messages.error(request, "Could not load the selected script version.")

        except (ValueError, PermissionDenied) as e:
            messages.error(request, f"Cannot load script: {e}")
        except Exception as e:
            logger.error(f"Error loading script: {e}")
            messages.error(request, "An unexpected error occurred while loading the script.")

    return redirect('script_list')

def get_script_versions(request):
    script_id = request.GET.get('script_id')
    try:
        script = get_object_or_404(Script, id=script_id, user=request.user)
        
        manager = Script_db_Manager(None, script.project)
        versions = manager.get_script_versions(script_id)
        
        return render(request, 'partials/version_options.html', {'versions': versions})
    except Exception as e:
        logger.error(f"Error getting script versions: {e}")
        return JsonResponse({'error': 'Could not fetch versions'}, status=500)