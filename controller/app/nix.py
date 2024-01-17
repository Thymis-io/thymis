def convert_python_value_to_nix(value):
    if isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, list):
        return f"[{' '.join([convert_python_value_to_nix(v) for v in value])}]"
    else:
        return str(value)
