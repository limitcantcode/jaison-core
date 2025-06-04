def create_response(status: int, message: str, response: dict, headers = None):
    if headers is None:
        return ({
            "status": status,
            "message": message,
            "response": response
        }, status)
    else:
        return ({
            "status": status,
            "message": message,
            "response": response
        }, status, headers)

def create_preflight(methods: str):
    return ("Success", 200, {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': methods,
        'Access-Control-Allow-Headers': 'Content-Type'})
