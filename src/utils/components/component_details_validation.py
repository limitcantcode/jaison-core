from typing import Any
import json
import os

from utils.helpers.singleton import Singleton
from utils.logging import create_sys_logger


class DetailSchemaPath:
    def __init__(self, type: str, path: str):
        self.type = type
        self.path = path


class DetailSchema:
    def __init__(self, type: str, schema: dict):
        self.type = type
        self.schema = schema


class ComponentDetailsValidator(metaclass=Singleton):
    """
    Singleton used for validation of component details against a schema.  
    Schemas can be found at `src/utils/components/details_schemas`.
    """

    def __init__(self):
        self.logger = create_sys_logger()
        self.schemas = self._read_schemas()
        self.defaults = self._read_defaults()


    def _read_schemas(self)-> dict[str, DetailSchema]:
        SCHEMA_DIR_PATH = os.path.join(os.path.dirname(__file__), "details_schemas")
        SCHEMA_BASE_PATH = os.path.join(SCHEMA_DIR_PATH, "base.json")
        SCHEMA_FEATURES_PATH = os.path.join(SCHEMA_DIR_PATH, "features.json")

        paths = [
            DetailSchemaPath("base", SCHEMA_BASE_PATH),
            DetailSchemaPath("features", SCHEMA_FEATURES_PATH),
        ]
        result: dict[str, DetailSchema] = {}

        for path in paths:
            with open(path.path) as f:
                schema = json.load(f)
                result[path.type] = DetailSchema(path.type, schema)
        
        return result


    def _read_defaults(self)-> dict[str, DetailSchema]:
        SCHEMA_DIR_PATH = os.path.join(os.path.dirname(__file__), "details_schemas")
        SCHEMA_BASE_DEFAULTS_PATH = os.path.join(SCHEMA_DIR_PATH, "base_defaults.json")
        SCHEMA_FEATURES_DEFAULTS_PATH = os.path.join(SCHEMA_DIR_PATH, "features_defaults.json")

        paths = [
            DetailSchemaPath("base", SCHEMA_BASE_DEFAULTS_PATH),
            DetailSchemaPath("features", SCHEMA_FEATURES_DEFAULTS_PATH),
        ]
        result: dict[str, DetailSchema] = {}

        for path in paths:
            with open(path.path) as f:
                schema = json.load(f)
                result[path.type] = DetailSchema(path.type, schema)
        
        return result


    def is_valid(self, component_details: dict)-> bool:
        """
        Validates the details of a component against the schema.
        This function assumes that details are an opaque object.
        Schemas can be found at `src/utils/components/details_schemas`.
        """
        self.component_details: dict = component_details

        base_schema: dict[str, Any] = self.schemas["base"].schema
        valid: bool = True

        # Get component name
        component_name: str = "unknown"
        if "name" in self.component_details:
            component_name = self.component_details["name"]
        elif "id" in self.component_details:
            component_name = self.component_details["id"]
        
        # Check if all fields are present and values have the correct type
        for key, expected_type in base_schema.items():
            if key not in self.component_details:
                self.logger.error(f'Missing key "{key}" in details of component "{component_name}"')
                valid = False
                continue
            
            val_type = type(self.component_details[key]).__name__
            if val_type != expected_type:
                self.logger.error(f'Invalid type for key "{key}" in details of component "{component_name}". Expected type {expected_type}, got {val_type}')
                valid = False
        
        if not valid:
            return False
        
        # TODO: Handle features when added to component details
        # TODO: Make sure to update base.json and base_defaults.json before enabling this
        return True

        features_schema = self.schemas["features"].schema
        component_type = self.component_details["type"]
        component_features = self.component_details["features"]
        
        # If component type is not standard componenent type: t2t, ttsc, ttsg, stt
        # Still valid, but handling of features is not guaranteed
        if component_type not in features_schema:
            self.logger.warning(f'No feature schema found for component of type "{component_type}"')
            return True

        # Check if all features are present and values have the correct type
        for feature, expected_type in features_schema[component_type].items():
            if feature not in component_features:
                self.logger.warning(f'Missing feature "{feature}" in details of component "{component_name}"')
                continue

            val_type = type(self.component_details[key]).__name__
            if val_type != expected_type: # Error case
                self.logger.error(f'Invalid type for feature "{feature}" in details of component "{component_name}". Expected type {expected_type}, got {val_type}')
                valid = False

        return valid
    

    def to_valid(self, invalid_details: dict)-> dict:
        """
        Generates a valid component details object from an invalid one.
        """
        valid_details: dict = {}
        base_schema_defaults: dict[str, Any] = self.defaults["base"].schema

        self.logger.info("Original details:")
        self.logger.info(json.dumps(invalid_details, indent=4))

        valid_details = base_schema_defaults | invalid_details

        self.logger.info("Patched details:")
        self.logger.info(json.dumps(valid_details, indent=4))
        
        # TODO: Handle features when added to component details
        # TODO: Make sure to update base.json and base_defaults.json before enabling this
        return valid_details
        
        features_schema_defaults = self.defaults["features"].schema
        component_type: str = valid_details["type"]

        if "features" in invalid_details:
            valid_details["features"] = features_schema_defaults[component_type] | invalid_details["features"]
        else:
            valid_details["features"] = features_schema_defaults[component_type]
        
        return valid_details
        