import importlib
import inspect
import os


# pyright: reportAny=false
def load_provider(
    provider_type: str,
    env_var: str,
    default: str,
    base_class: type,
) -> object:
    name = os.environ.get(env_var, default)
    try:
        module = importlib.import_module(f"app.providers.{provider_type}.{name}")
    except ModuleNotFoundError:
        msg = (
            f"Unknown {provider_type} provider: {name}. "
            f"Create app/providers/{provider_type}/{name}.py "
            f"with a class extending {base_class.__name__}."
        )
        raise ValueError(msg) from None

    for _, obj in inspect.getmembers(module):
        if (
            inspect.isclass(obj)
            and issubclass(obj, base_class)
            and obj is not base_class
        ):
            return obj()

    msg = (
        f"No {provider_type} provider class found in "
        f"app.providers.{provider_type}.{name}."
    )
    raise ValueError(msg)
