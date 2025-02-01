def create_response(status: int, message: str, response: dict): # TODO: document status codes, validate information
    return (
        {
            "status": status,
            "message": message,
            "response": response
        },
        status
    )