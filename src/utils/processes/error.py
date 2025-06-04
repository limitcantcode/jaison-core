class UnknownProcessError(Exception):
    def __init__(self, process):
        super().__init__("No process {} exists".format(process))
        
class UnloadedProcessError(Exception):
    def __init__(self, process):
        super().__init__("Process {} is not loaded".format(process))
        
class DuplicateLink(Exception):
    def __init__(self, link_id, process):
        super().__init__("Link ID {} already linked to process {}".format(link_id, process))

class MissingLink(Exception):
    def __init__(self, link_id, process):
        super().__init__("Link ID {} is not linked to process {}".format(link_id, process))