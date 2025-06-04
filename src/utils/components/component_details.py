import os
from typing import Any
from .error import InvalidComponentConfig



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
        details: dict[str, Any],
        listing: dict[str, Any]
    ):
        self.comp_type: str = details["type"]
        self.id: str = details["id"]
        self.name: str = details["name"]

        self.is_windows_compatible: bool = details["is_windows_compatible"]
        self.is_unix_compatible: bool = details["is_unix_compatible"]
        self.run_script: str = details["windows_run_script"] if os.name=='nt' else details["unix_run_script"]

        self.directory: str | None = listing["directory"]
        self.endpoint: str | None = None

        endpoint = listing["endpoint"]

        if endpoint:
            self.update_endpoint(endpoint)

    def update_endpoint(self, endpoint: str):
        self.endpoint = endpoint
