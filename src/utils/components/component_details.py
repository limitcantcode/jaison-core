import os
from .error import InvalidComponentConfig
from .component_workers import COMPONENT_COLLECTION

COMPONENT_TYPES = list(COMPONENT_COLLECTION.keys())

class ComponentDetails():
    '''
    component_type: (int) Specifies kind of component by number (refer to COMPONENT_TYPES)
    id: (str) Ideally unique ID
    name: (str) Human readable name
    directory: (kwarg str) (1) Full filepath to directory to root of component's project
    run_script: (kwarg str) (1) Full filepath to script that loads environment and runs project 
    is_windows_compatible: (kwarg bool) (1) Whether compatible with Windows machines
    is_unix_compatible: (kwarg bool) (1) Whether compatible with Unix-based machines
    endpoint: (kwarg str) (1,2) URI running project lives on 

    (1) Must specify either endpoint, or directory, run_script, is_windows_compatible, and is_unix_compatible
    (2) If component is supposed to already be running before component is made, endpoint is set on initialization.
        If component should be started up when component is made, endpoint is None
    '''

    def __init__(
        self,
        comp_type: int,
        id: str,
        name: str,
        directory: str = None,
        windows_run_script: str = None,
        unix_run_script: str = None,
        is_windows_compatible: bool = False,
        is_unix_compatible: bool = False,
        endpoint: str = None
    ):

        self.comp_type = comp_type
        self.id = id
        self.name = name 
        self.directory = directory 
        self.run_script = windows_run_script if os.name=='nt' else unix_run_script
        self.is_windows_compatible = is_windows_compatible 
        self.is_unix_compatible = is_unix_compatible
        if endpoint:
            self.update_endpoint(endpoint)

    def update_endpoint(self, endpoint: str):
        self.endpoint = endpoint
