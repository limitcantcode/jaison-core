def portable_path(target_path: str):
    return target_path.encode("unicode_escape").decode()
