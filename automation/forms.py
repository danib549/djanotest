from django import forms
from .models import Project

class ScriptForm(forms.Form):
    ENVIRONMENT_CHOICES = [
        ('option_111111111111111111111111111111111111111111', 'Option 1'),
        ('option_2', 'Option 2'),
        ('option_3', 'Option 3'),
    ]

    COMMAND_CHOICES = [
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

    environment = forms.ChoiceField(choices=ENVIRONMENT_CHOICES, label="Environment")
    command = forms.ChoiceField(choices=COMMAND_CHOICES, label="Command")
    sub_command = forms.ChoiceField(choices=SUB_COMMAND_CHOICES, label="Sub Command")
    component = forms.ChoiceField(choices=COMPONENT_CHOICES, label="Component")
    packet = forms.ChoiceField(choices=PACKET_CHOICES, label="Packet")
    transmition_line = forms.ChoiceField(choices=TRANSMITION_LINE, label="Transmition Line")
    parameters = forms.ChoiceField(choices=PARAMETERS_CHOICES, label="Parameters")
    operator = forms.ChoiceField(choices=OPERATOR_CHOICES, label="Operator")
    value_manipulation = forms.ChoiceField(choices=VALUE_MANIPULATION_CHOICES, label="Value Manipulation")
    fixed_value = forms.FloatField(required=False, label="Fixed Value")
    min_value = forms.FloatField(required=False, label="Min Value")
    max_value = forms.FloatField(required=False, label="Max Value")
    resolution = forms.ChoiceField(choices=TOLERANCE_TYPE_CHOICES, required=False, label="Resolution Type")
    resolution_value = forms.FloatField(required=False, label="Resolution Value")
    enum_value = forms.CharField(max_length=100, required=False, label="Enum Value")

    step_id = forms.IntegerField(widget=forms.HiddenInput(), required=False, label="Step ID")
    at_time = forms.FloatField(required=False, label="At Time")
    delay = forms.FloatField(required=False, label="Delay")
    sync = forms.BooleanField(required=False, label="Sync")
    length_plus = forms.BooleanField(required=False, label="Length Plus")
    length_minus = forms.BooleanField(required=False, label="Length Minus")
    sequence_number = forms.BooleanField(required=False, label="Sequence Number")
    checksum = forms.BooleanField(required=False, label="Checksum")

    value_tolerance = forms.ChoiceField(choices=TOLERANCE_TYPE_CHOICES, label="Value Tolerance")
    value_tolerance_value = forms.FloatField(required=False)
    time_tolerance = forms.ChoiceField(choices=TIME_TOLERANCE_CHOICES, label="Time Tolerance")
    time_tolerance_value = forms.FloatField(required=False)
    description = forms.CharField(widget=forms.Textarea, required=False, label="Description")


class GlobalSettingsForm(forms.Form):
    project = forms.ModelChoiceField(queryset=Project.objects.none(), label="Select Project")
    test_name = forms.CharField(max_length=100, required=True)
    Requirment_id = forms.CharField(max_length=100, required=False)

    def __init__(self, user, *args, **kwargs):
        super(GlobalSettingsForm, self).__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(users=user)
