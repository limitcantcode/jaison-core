def create_response(status: int, message: str, response: dict):
    return (
        {
            "status": status,
            "message": message,
            "response": response
        },
        status
    )