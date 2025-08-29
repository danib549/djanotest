from django import forms
from .models import Project
from django.conf import settings

# Centralized Choices Definitions
ENVIRONMENT_CHOICES = [
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
]

OPERATION_CHOICES = [
    ('set', 'set'),
    ('get', 'get'),
    ('general', 'general'),
]

SUB_COMMAND_CHOICES = [
    ('sub_command_1', 'Sub Command 1'),
    ('sub_command_2', 'Sub Command 2'),
    ('sub_command_3', 'Sub Command 3'),
]

COMPONENT_CHOICES = [
    ('component_1', 'Component 1'),
    ('component_2', 'Component 2'),
    ('component_3', 'Component 3'),
]

PACKET_CHOICES = [
    ('packet_1', 'Packet 1'),
    ('packet_2', 'Packet 2'),
    ('packet_3', 'Packet 3'),
]

PARAMETERS_CHOICES = [
    ('param_1', 'Parameter 1'),
    ('param_2', 'Parameter 2'),
    ('param_3', 'Parameter 3'),
]

VALUE_MANIPULATION_CHOICES = [
    ('no-change', 'No Change'),
    ('fixed', 'Fixed Value'),
    ('random', 'Random Value'),
    ('enum', 'Enum'),
    ('Parameters', 'Parameters')
]

OPERATOR_CHOICES = [
    ('+', '+'),
    ('-', '-'),
    ('*', '*'),
    ('/', '/')
]

TOLERANCE_TYPE_CHOICES = [
    ('percentage', 'Percentage'),
    ('fixed', 'Fixed Time')
]

TIME_TOLERANCE_CHOICES = [
    ('reach-value', 'Time to Reach Value'),
    ('stable-value', 'Period of Stable Value')
]

TRANSMITION_LINE = [
    ('Real', 'Real'),
    ('Test', 'Test'),
    ('Test2', 'Test2'),
]

SCRIPT_ERROR_BEHAVIOR = [
    ('continue', 'Continue'),
    ('stop', 'Stop'),
    ('retry', 'Retry'),
]

# New Form: ParameterConfigForm (Used in the modal)
class ParameterConfigForm(forms.Form):
    """Handles the configuration for a SINGLE parameter."""
    parameter_id = forms.ChoiceField(choices=[], label="Select Parameter", required=True)
    
    # Configuration fields matching ParameterConfig inputs
    operator = forms.ChoiceField(choices=OPERATOR_CHOICES, label="Operator", required=False)
    value_manipulation = forms.ChoiceField(choices=VALUE_MANIPULATION_CHOICES, label="Value Manipulation", required=False)

    # Value Options
    value_options = forms.CharField(max_length=200, required=False, label="Value Options")
    fixed_value = forms.FloatField(required=False, label="Fixed Value")
    min_value = forms.FloatField(required=False, label="Min Value")
    max_value = forms.FloatField(required=False, label="Max Value")
    resolution = forms.ChoiceField(choices=TOLERANCE_TYPE_CHOICES, required=False, label="Resolution Type")
    resolution_value = forms.FloatField(required=False, label="Resolution Value")
    enum_value = forms.CharField(max_length=100, required=False, label="Enum Value")
    table_parameters = forms.ChoiceField(choices=[], required=False, label="Table Parameters")

    # Value Tolerance fields
    value_tolerance = forms.ChoiceField(choices=TOLERANCE_TYPE_CHOICES, label="Value Tolerance", required=False)
    percentage = forms.FloatField(required=False, label="Percentage")
    value_tolerance_value = forms.FloatField(required=False, label="Value Tolerance Value")
    
    # Time Tolerance fields
    time_tolerance = forms.ChoiceField(choices=TIME_TOLERANCE_CHOICES, label="Time Tolerance", required=False)
    time_to_reach_value = forms.FloatField(required=False, label="Time to Reach Value")
    time_tolerance_value = forms.FloatField(required=False, label="Time Tolerance Value")

    def __init__(self, *args, **kwargs):
        # packet_id is required to populate the parameter choices dynamically
        packet_id = kwargs.pop('packet_id', None)
        super(ParameterConfigForm, self).__init__(*args, **kwargs)

        if packet_id:
            self.populate_parameter_choices(packet_id)
        else:
            self.fields['parameter_id'].choices = [('', 'Select Packet First')]

    def populate_parameter_choices(self, packet_id):
        try:
            # TODO: Replace with actual database handler when available
            # parameters = settings.AUTOMATION_DB_HANDLER.get_parameters(int(packet_id))
            # For now, use static choices
            self.fields['parameter_id'].choices = [('', 'Select Parameter')] + [
                (choice[0], choice[1]) for choice in PARAMETERS_CHOICES
            ]
        except Exception:
            self.fields['parameter_id'].choices = [('', 'Error loading parameters')]


# Modified Form: ScriptForm (Main step form)
class ScriptForm(forms.Form):
    """Handles the core details of the script step."""
    
    # Core Step Fields
    command = forms.ChoiceField(choices=OPERATION_CHOICES, label="Operation")
    sub_command = forms.ChoiceField(choices=SUB_COMMAND_CHOICES, label="Sub Command", required=False)
    transmition_line = forms.ChoiceField(choices=TRANSMITION_LINE, label="TTC", required=False)

    step_id = forms.IntegerField(widget=forms.HiddenInput(), required=False, label="Step ID")
    
    # Timing Fields
    at_time = forms.FloatField(required=False, label="At Time")
    delay = forms.FloatField(required=False, label="Delay")
    time_tolerance = forms.ChoiceField(choices=TIME_TOLERANCE_CHOICES, label="Time Tolerance", required=False)
    time_tolerance_value = forms.FloatField(required=False, label="Time Tolerance Value")

    # Frame Error Fields
    sync = forms.BooleanField(required=False, label="Sync")
    length_plus = forms.BooleanField(required=False, label="Length Plus")
    length_minus = forms.BooleanField(required=False, label="Length Minus")
    sequence_number = forms.BooleanField(required=False, label="Sequence Number")
    checksum = forms.BooleanField(required=False, label="Checksum")
    
    # Other
    script_error_behavior = forms.ChoiceField(choices=SCRIPT_ERROR_BEHAVIOR, required=False, label="Error Behavior")
    description = forms.CharField(widget=forms.Textarea, required=False, label="Description")

    # Selection Fields
    environment = forms.ChoiceField(choices=ENVIRONMENT_CHOICES, label="Environment", required=False)
    component = forms.ChoiceField(choices=COMPONENT_CHOICES, label="Component", required=False)
    packet = forms.ChoiceField(choices=PACKET_CHOICES, label="Packet", required=False)
    
    # Parameter configuration JSON field to handle configured parameters
    parameters_json = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    # NOTE: ParameterConfig fields are handled by ParameterConfigForm separately

    def __init__(self, *args, **kwargs):
        super(ScriptForm, self).__init__(*args, **kwargs)
        # Initialization logic for environments and dependent fields
        # TODO: Add dynamic population based on selected values


class GlobalSettingsForm(forms.Form):
    project = forms.ModelChoiceField(queryset=Project.objects.none(), label="Select Project")
    test_name = forms.CharField(max_length=100, required=True)
    Requirment_id = forms.CharField(max_length=100, required=False)

    def __init__(self, user, *args, **kwargs):
        super(GlobalSettingsForm, self).__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(users=user)