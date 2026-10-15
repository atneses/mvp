"""Load the plugins listed in settings.ENABLED_COUNTRIES and look them up by code."""

from functools import cache
from importlib import import_module

from django.conf import settings

from countries.base import CountryPlugin


class UnknownCountryError(LookupError):
    pass


def get_plugin(code: str) -> CountryPlugin:
    plugins = _load_plugins()
    try:
        return plugins[code]
    except KeyError:
        raise UnknownCountryError(
            f"Country {code!r} is not enabled. Enabled: {', '.join(plugins)}."
        ) from None


def enabled_countries() -> list[str]:
    return list(_load_plugins())


@cache
def _load_plugins() -> dict[str, CountryPlugin]:
    # Loaded once; each country lives in countries/<code>/plugin.py as `plugin`.
    plugins = {}
    for code in settings.ENABLED_COUNTRIES:
        plugin = import_module(f"countries.{code.lower()}.plugin").plugin
        if not isinstance(plugin, CountryPlugin) or plugin.code != code:
            raise TypeError(f"countries.{code.lower()}.plugin does not implement CountryPlugin.")
        plugins[code] = plugin
    return plugins
