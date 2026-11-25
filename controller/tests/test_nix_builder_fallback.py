from thymis_controller.nix import builder_unavailable


def test_detects_unreachable_builder():
    assert builder_unavailable("error: cannot connect to 'ssh://root@100.64.0.7'")
    assert builder_unavailable(b"error: Failed to find a machine for remote build!")
    assert builder_unavailable(
        "ssh: connect to host 100.64.0.7 port 22: Connection refused"
    )


def test_ignores_normal_build_failure():
    assert not builder_unavailable("error: builder for '/nix/store/foo.drv' failed")
    assert not builder_unavailable(b"error: hash mismatch")
