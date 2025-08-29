# script_data.py
import copy
import hashlib
import json
# Import necessary tools from the typing module
from typing import Any, Dict, List, Optional, get_type_hints, Type, Union, TypeVar

# Define a TypeVar bound to Serializable for use in classmethods
T = TypeVar('T', bound='Serializable')

class Serializable:
    """A base class that provides recursive methods to serialize an object to a dictionary and deserialize from a dictionary."""

    def to_dict(self) -> Dict[str, Any]:
        """
        Recursively converts the object's attributes to a dictionary.
        """
        # Use deepcopy to ensure that the original object is not modified
        data = copy.deepcopy(self.__dict__)

        for key, value in data.items():
            data[key] = self._serialize_value(value)

        return data

    def _serialize_value(self, value: Any) -> Any:
        """Helper function to serialize a single value."""
        if isinstance(value, Serializable):
            return value.to_dict()
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        else:
            return value

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Recursively reconstructs an object from a dictionary using type hints.
        """
        instance = cls()
        if not isinstance(data, dict):
             raise TypeError(f"Expected a dictionary for deserialization into {cls.__name__}, but got {type(data).__name__}")

        try:
            # Get type hints for the class.
            # We provide globals() to ensure nested classes defined in this file are resolved.
            type_hints = get_type_hints(cls, globalns=globals())
        except (NameError, TypeError) as e:
            # Fallback if get_type_hints fails
            print(f"Warning: Could not retrieve all type hints for {cls.__name__}: {e}")
            type_hints = {}

        for key, value in data.items():
            # Safety check: Only set attributes that are defined in the class structure
            if hasattr(instance, key):
                field_type = type_hints.get(key)
                # Use the helper to deserialize the value based on the expected type
                deserialized_value = cls._deserialize_value(value, field_type)
                setattr(instance, key, deserialized_value)
        return instance

    @classmethod
    def _deserialize_value(cls, value: Any, field_type: Optional[Type]) -> Any:
        """Helper function to deserialize a single value based on its type hint."""

        if value is None:
            return None

        if field_type:
            origin = getattr(field_type, '__origin__', None)
            args = getattr(field_type, '__args__', [])

            # Handle Optional (Union[T, None])
            if origin is Union and type(None) in args:
                non_none_args = [arg for arg in args if arg is not type(None)]
                if non_none_args:
                    return cls._deserialize_value(value, non_none_args[0])

            # Handle nested Serializable subclasses
            if isinstance(field_type, type) and issubclass(field_type, Serializable):
                if isinstance(value, dict):
                    return field_type.from_dict(value)
                return value # If already an object or corrupted data

            # Handle Lists
            if origin in (list, List):
                if isinstance(value, list):
                    item_type = args[0] if args else None
                    return [cls._deserialize_value(item, item_type) for item in value]

            # Handle Dicts
            if origin in (dict, Dict):
                if isinstance(value, dict):
                    value_type = args[1] if len(args) > 1 else None
                    return {k: cls._deserialize_value(v, value_type) for k, v in value.items()}

            # Handle basic type casting
            if field_type is float and isinstance(value, (int, str)):
                try:
                    return float(value)
                except (ValueError, TypeError):
                    pass

        # Fallback
        return value

# --- Data Structure Classes ---

class ParameterConfig(Serializable):
    """Holds the configuration and calculated values for a single parameter."""
    def __init__(self):
        # Input Configuration
        self.value_manipulation: Optional[str] = 'no-change'
        self.min_value: Optional[float] = None
        self.max_value: Optional[float] = None
        self.resolution: Optional[str] = None
        self.resolution_value: Optional[float] = None
        self.fixed_value: Optional[Any] = None
        self.enum_value: Optional[Any] = None

        # GET specific Input
        self.operator: Optional[str] = "="
        self.value_tolerance: Optional[str] = None
        self.value_tolerance_value: Optional[float] = None

        # Output fields
        self.value: Optional[Any] = None
        self.expected_value: Optional[Any] = None
        self.min_accepted_value: Optional[float] = None
        self.max_accepted_value: Optional[float] = None

class StepData(Serializable):
    """Represents the definition and final state of a script step."""
    def __init__(self):
        # Core Identification and Command
        self.step_id: Optional[int] = None
        self.command: Optional[str] = None
        self.description: Optional[str] = None

        # Timing Configuration
        self.at_time: Optional[str] = None
        self.delay: Optional[str] = None

        # Multi-Parameter Configuration
        self.parameters: Dict[str, ParameterConfig] = {}

        # Other fields
        self.time_tolerance: Optional[str] = None
        self.time_tolerance_value: Optional[str] = None
        self.loop_id: Optional[str] = None
        self.loop_repeat: str = '1'
        self.step_repeat: str = '1'
        self.loop_background: Optional[bool] = None
        self.Step_loop_enabled: Optional[bool] = None
        self.priority_loop_repeat: bool = False
        self.priority_bg: bool = False
        self.environment: Optional[str] = None
        self.sub_command: Optional[str] = None
        self.component: Optional[str] = None
        self.packet: Optional[str] = None
        self.transmition_line: Optional[str] = None
        self.script_error_behavior: Optional[str] = None
        # Ensure all keys used in the session manager are present
        self.frame_errors: Dict[str, Optional[bool]] = {'sync': None, 'checksum': None, 'length_plus': None, 'length_minus': None, 'sequence_number': None}


class ScriptData(Serializable):
    """Container for the script steps and metadata."""
    def __init__(self):
        # Initialize steps and variables correctly as lists
        self.steps: List[StepData] = []
        self.project: Optional[int] = None
        self.test_name: Optional[str] = None
        self.variables: List[Dict[str, Any]] = []
        self.checksum: Optional[str] = None

    @staticmethod
    def default_dict() -> Dict[str, Any]:
        """Returns a default dictionary structure for an empty script."""
        return {
            'steps': [],
            'project': None,
            'test_name': None,
            'variables': [],
            'checksum': None
        }

    def calculate_checksum(self) -> str:
        """Calculates a checksum based on the entire serialized script data."""
        data_dict = self.to_dict()
        # Remove the existing checksum before calculating the new one
        data_dict.pop('checksum', None)

        # Use json.dumps with sorted keys for a consistent, canonical string representation
        data_string = json.dumps(data_dict, sort_keys=True)
        return hashlib.md5(data_string.encode()).hexdigest()