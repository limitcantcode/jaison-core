class UnknownProcessError(Exception):
    def __init__(self, process):
        super().__init__(f"No process {process} exists")


class UnloadedProcessError(Exception):
    def __init__(self, process):
        super().__init__(f"Process {process} is not loaded")


class DuplicateLink(Exception):
    def __init__(self, link_id, process):
        super().__init__(f"Link ID {link_id} already linked to process {process}")


class MissingLink(Exception):
    def __init__(self, link_id, process):
        super().__init__(f"Link ID {link_id} is not linked to process {process}")
