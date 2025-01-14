import os
import yaml
import grpc
from typing import Union
from jaison_grpc.client import MetadataInformerStub
from .error import UnknownComponent, UnloadedComponentError, MissingComponentConfig, InvalidComponentConfig, InvalidComponentListing
from .component import Component
from .component_details import ComponentDetails
from utils.logging import create_sys_logger

class ComponentManager():
    logger = create_sys_logger()
    loaded_components = {} # <component type>: Component
    available_components = {} # <component type>: <list of ComponentDetails>

    def __init__(self, component_config: str):
        self.os_type = os.name
        self.reload_config(component_config)

    def reload_config(self, filepath: str):
        self.logger.debug(f"Loading component configuration: {filepath}")
        if not (filepath.endswith('.yaml') and os.path.isfile(filepath)):
            raise MissingComponentConfig(f"Component config {filepath} does not exist.")
        
        with open(filepath) as f:
            try:
                yaml_dict = yaml.safe_load(f)
                if 'components' not in yaml_dict:
                    raise InvalidComponentListing("Component listing is missing. Please add 'components'.")
                components = yaml_dict['components']
                self.logger.debug(f"Loaded components config: {components}")
            except Exception as err:
                self.logger.error(f"Could not parse config: {filepath}")
                self.logger.error(err)
                raise err

            for listing in components:
                try:
                    metadata = None
                    if 'directory' in listing:
                        with open(os.path.join(listing['directory'],'metadata.yaml'), 'r') as f:
                            listing['endpoint'] = None
                            metadata = yaml.safe_load(f)
                        if self.os_type=='nt' and not metadata['is_windows_compatible']:
                            self.logger.warning("Component {} in {} is not compatible with Windows. Skipping...".format(metadata['id'],listing['directory']))
                        elif self.os_type=='posix' and not metadata['is_unix_compatible']:
                            self.logger.warning("Component {} in {} is not compatible with Unix. Skipping...".format(metadata['id'],listing['directory']))
                    elif 'endpoint' in listing:
                        listing['directory'] = None
                        with grpc.aio.insecure_channel(listing.endpoint) as channel:
                            stub = MetadataInformerStub(channel)
                            metadata = stub.metadata()
                    else:
                        raise InvalidComponentListing(f"Following component listing missing on of 'directory' or 'endpoint': {listing}")

                    self.logger.debug(f"For component listing {listing}, got metadata: {metadata}")
                    if metadata['type'] not in self.available_components:
                        self.available_components[metadata['type']] = []
                    self.available_components[metadata['type']].append(
                        ComponentDetails(
                            metadata['type'],
                            metadata['id'],
                            metadata['name'],
                            listing['directory'],
                            metadata['windows_run_script'],
                            metadata['unix_run_script'],
                            metadata['is_windows_compatible'],
                            metadata['is_unix_compatible'],
                            endpoint=listing['endpoint']
                        )
                    )
                    self.logger.info(f"Loaded component configuration: {filepath}")
                except Exception as err:
                    self.logger.error(f"Failed to add a component.")
                    self.logger.error(err)
                    self.logger.warning("Skipping...")

    def load_components(self, components: Union[str, list[str]], reload: bool = False):
        '''
        Inputs:
            components: (Union[str, list[str]]) component IDs
            reload: (optional bool) If true, force reload components, even if they already are loaded
        Outputs:
            None
        Errors:
            UnknownComponent: When no available component with that ID exists
        '''
        self.logger.debug(f"Loading component(s) with ID(s): {components}")
        component_ids = components
        if type(component_ids) == str:
            component_ids = [components]

        for comp_id in component_ids:
            # Skip if loaded and reload not set
            if not reload:
                is_skippable = False
                for comp_type in self.loaded_components:
                    if self.loaded_components[comp_type].details.id == comp_id:
                        self.logger.info(f"Component {components} already loaded. Skipping...")
                        is_skippable = True
                        break
                if is_skippable: continue

            # Proceed to find and load new component
            is_done = False
            for comp_type in self.available_components:
                for details in self.available_components[comp_type]:
                    if details.id == comp_id:
                        self.logger.debug(f"Found component details: {details}.")
                        try:
                            self.logger.debug(f"Unloading previous component...")
                            self.unload_components(comp_type)
                            self.logger.debug(f"Unloaded previous component...")
                        except:
                            self.logger.debug(f"No component to unload.")
                        self.logger.debug(f"Starting new component {comp_id}...")
                        self.loaded_components[comp_type] = self._start_component(details)
                        self.logger.debug(f"Started new component {comp_id}.")
                        is_done = True
                        break
                if is_done: break
            if is_done: continue

            # No detail object with matching component ID found
            raise UnknownComponent(f"Component of id '{comp_id}' not found")
        
        self.logger.debug(f"Finished loading all components.")
        
    def unload_components(self, components: Union[str, list[str]]):
        '''
        Inputs:
            components: (Union[str, list[str]]) component types
        Outputs:
            None
        Errors:
            UnloadedComponentError: When no available component of that type is loaded
        '''
        comp_list = components
        if type(comp_list) is str:
            comp_list = [components]
        for comp_type in comp_list:
            self.logger.debug(f"Unloading component of type: {comp_type}...")
            if comp_type not in self.loaded_components:
                raise UnloadedComponentError(f"No loaded components of type '{comp_type}'")
            self.loaded_components[comp_type].close()
            del self.loaded_components[comp_type]
            self.logger.debug(f"Unloaded component of type: {comp_type}...")

    def cleanup(self):
        self.unload_components(list(self.loaded_components.keys()))
        
    async def use(self, comp_type: str, payload, run_id: str = "example_run_id"):
        if comp_type not in self.loaded_components:
            raise UnloadedComponentError(f"No loaded components of type '{comp_type}'")
        
        self.logger.debug(f"Streaming from {comp_type} component...")
        async for run_id, result in self.loaded_components[comp_type](run_id, payload):
            yield run_id, result

    def _start_component(self, comp_details: ComponentDetails):
        self.logger.debug(f"Starting new component with details: {comp_details}")
        new_component = Component(comp_details)
        self.logger.debug(f"Started new component with details: {comp_details}")
        return new_component