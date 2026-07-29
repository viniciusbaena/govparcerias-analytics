"""Versioned connector/plugin registry."""
from dataclasses import dataclass

@dataclass(frozen=True)
class PluginManifest:
    plugin_id: str
    version: str
    official_base_url: str
    domains: tuple[str, ...]
    supports_documents: bool = False

class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, PluginManifest] = {}

    def register(self, manifest: PluginManifest) -> None:
        if not manifest.official_base_url.startswith("https://"):
            raise ValueError("Plugins devem usar uma URL oficial HTTPS.")
        self._plugins[manifest.plugin_id] = manifest

    def list(self) -> list[PluginManifest]:
        return sorted(self._plugins.values(), key=lambda item: item.plugin_id)
