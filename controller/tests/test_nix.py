from thymis_controller.nix import convert_python_value_to_nix


def test_write_nix_value():
    assert convert_python_value_to_nix("hello") == '"hello"'
    assert convert_python_value_to_nix("hello\n") == '"hello\\n"'
    assert convert_python_value_to_nix({"a": "b"}) == '{\n  a = "b";\n}'
    assert convert_python_value_to_nix({"a": {"b": "c"}}) == '{\n  a.b = "c";\n}'
    assert (
        convert_python_value_to_nix({"a": {"b c": {"d": "e"}}})
        == '{\n  a."b c".d = "e";\n}'
    )
    assert convert_python_value_to_nix(True) == "true"
    assert convert_python_value_to_nix(False) == "false"
    assert convert_python_value_to_nix(["a", "b"]) == '["a" "b"]'
    assert convert_python_value_to_nix({"": ""}) == '{\n  "" = "";\n}'
    assert convert_python_value_to_nix({"1abc": ""}) == '{\n  "1abc" = "";\n}'
    assert convert_python_value_to_nix({}) == "{}"
