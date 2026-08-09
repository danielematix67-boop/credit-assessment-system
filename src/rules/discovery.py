import importlib
import pkgutil

import src.rules


def discover_rules() -> None:
    """
    Import all rule modules so that registered rules are loaded.
    """

    package = src.rules

    for module_info in pkgutil.walk_packages(
        package.__path__,
        package.__name__ + ".",
    ):
        module_name = module_info.name

        if (
            module_name.endswith(".registry")
            or module_name.endswith(".discovery")
            or ".base." in module_name
        ):
            continue

        importlib.import_module(module_name)