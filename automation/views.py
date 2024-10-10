from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from .forms import ScriptForm, GlobalSettingsForm
from .models import Script, Project
from .seasion_data_manager import ScriptDataManager
from .script_db_manager import Script_db_Manager



def delete_variable(request, variable_id):
    if request.method == 'DELETE':
        # Retrieve current variables from session
        variables = request.session.get('variables', [])
        # Remove the variable with the specified index
        if 0 <= variable_id < len(variables):
            del variables[variable_id]

        # Update the session
        request.session['variables'] = variables
        request.session.modified = True

        # Render the updated table
        return render(request, 'partials/variable_table.html', {'variables': variables})

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def global_settings(request):
    if request.method == 'POST':
        form = GlobalSettingsForm(user=request.user, data=request.POST)
        if form.is_valid():
            project = form.cleaned_data['project']
            test_name = form.cleaned_data['test_name']  # Get the test_name
            Requirment_id = form.cleaned_data['Requirment_id']
            request.session['script_version'] = 1
            request.session['project_id'] = project.id
            request.session['test_name'] = test_name + '- Time - ' + datetime.now().strftime('%Y-%m-%d %H-%M-%S')
            # request.session['Requirment_id'] = Requirment_id
            request.session['script'] = []
            request.session['variables'] = []
            request.session.modified = True
            return redirect('create_script')
    else:
        form = GlobalSettingsForm(user=request.user)

    return render(request, 'automation/global_settings.html', {'form': form})

@login_required
def add_variable(request):
    if request.method == 'POST':
        var_name = request.POST.get('var_name')
        data_type = request.POST.get('data_type')
        var_value = request.POST.get('var_value')

        # Retrieve current variables from session or initialize as an empty list
        variables = request.session.get('variables', [])
        # Add the new variable to the session list
        variables.append({
            'name': var_name,
            'data_type': data_type,
            'value': var_value
        })

        # Save the updated variables list in the session
        request.session['variables'] = variables
        request.session.modified = True

        # Render and return only the variable table to be updated
        return render(request, 'partials/variable_table.html', {'variables': variables})

    return JsonResponse({'error': 'Invalid request'}, status=400)


# views.py
def get_script_versions(request):
    script_id = request.GET.get('script_id')
    script = Script.objects.get(id=script_id)

    manager = Script_db_Manager(script, script.project)
    versions = manager.get_script_versions()

    return render(request, 'partials/version_options.html', {'versions': versions})


@login_required
def create_script(request):
    script_data_manager = ScriptDataManager(request)
    script_data_manager.initialize_script_session()

    project_id = request.session.get('project_id')
    project = get_object_or_404(Project, id=project_id, users=request.user)

    if request.method == 'POST':
        form = ScriptForm(request.POST)

        if form.is_valid():
            if request.POST.get('action') == 'save':
                # Save the entire script
                script_data_manager.save_script(request.user, project)
                return redirect('script_list')
            else:
                script_data_manager.add_or_edit_step(form)

                if request.headers.get('HX-Request'):  # HTMX request
                    return render(request, 'partials/step_list.html', {
                        'session_script': request.session['script']
                    })

    # Regular form rendering
    form = ScriptForm()
    return render(request, 'automation/create_script.html', {
        'form': form,
        'session_script': request.session['script'],
        'variables' : request.session.get('variables', []),
    })


# def delete_script(request, script_id):
#     if request.method == "POST":
#         script = get_object_or_404(Script, id=script_id)
#         script.delete()
#
#     return redirect('script_list')

@login_required
def delete_step(request, step_id):
    if request.method == 'POST':
        script_data_manager = ScriptDataManager(request)
        updated_steps = script_data_manager.delete_step(step_id)

        if request.headers.get('HX-Request'):  # Handle HTMX request
            return render(request, 'partials/step_list.html', {
                'session_script': updated_steps  # Send updated step list to HTMX
            })

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def load_step(request, step_id):
    script_data_manager = ScriptDataManager(request)
    step_data = script_data_manager.get_step_from_session(step_id)

    if step_data:
        return JsonResponse(step_data)

    return JsonResponse({'error': 'Step not found'}, status=404)
    # Send back the step data as JSON



@login_required
def get_scripts_by_project(request):
    project_id = request.GET.get('project_id')
    try:
        if project_id:
            project = get_object_or_404(Project, id=project_id)
            scripts = Script.objects.filter(project=project)
        else:
            scripts = Script.objects.all()
    except Exception as e:
        print(e)


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
    if request.method == 'POST':
        script_id = request.POST.get('script_id')
        version_id = request.POST.get('version_id')  #

        if script_id and version_id:
            script = get_object_or_404(Script, id=script_id, user=request.user)
            manager = Script_db_Manager(script, script.project)

            # Load the specific version of the script
            script_content = manager.load_script_version(int(version_id))

            project = get_object_or_404(Project, name=script_content['project'])
            request.session['project_id'] = project.id
            request.session['script'] = script_content['steps']
            request.session['editing_script_id'] = script.id  # Store script_id to indicate editing
            request.session['script_version'] = version_id
            request.session.modified = True

            return redirect('create_script')
    return redirect('script_list')


@csrf_exempt
def update_step_order(request):
    if request.method == 'POST':
        step_id = request.POST.get('step_id')
        direction = request.POST.get('direction')

        script_data_manager = ScriptDataManager(request)
        updated_steps = script_data_manager.move_step(step_id, direction)
        if updated_steps is not None:
            request.session['script'] = updated_steps
            request.session.modified = True

            return render(request, 'partials/step_list.html', {
                'session_script': updated_steps
            })
        return JsonResponse({'error': 'Step not found'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=405)
