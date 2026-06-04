from importlib import import_module
from pathlib import Path


def test_handler_template_notebook_exists():
    assert Path("nbs/handlers/handler_template.ipynb").exists()


def test_handler_template_module_exports_smoke():
    module = import_module("marisco.handlers.handler_template")

    assert hasattr(module, "TemplateCB")
    assert hasattr(module, "load_data")
    assert hasattr(module, "get_attrs")
    assert hasattr(module, "encode")
