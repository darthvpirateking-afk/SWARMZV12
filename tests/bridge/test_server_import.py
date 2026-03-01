import importlib


def test_server_imports_without_static_dirs(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    module = importlib.import_module("swarmz_runtime.api.server")
    importlib.reload(module)
    assert module.app is not None
