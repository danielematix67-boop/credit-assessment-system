import importlib
import pkgutil

import src.rules


def discover_rules() -> None:
    """
    Discover and import all rule modules.

    Rule modules are imported once by Python's import system.
    Importing an already loaded module does not re-execute it.
    Therefore this function is idempotent and must not be used
    to rebuild a cleared Rule registry.
    
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