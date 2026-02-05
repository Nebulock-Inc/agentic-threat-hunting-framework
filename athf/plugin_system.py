"""Plugin system for ATHF extensions."""

import sys
from typing import Any, Dict, Optional, Type

from click import Command

# Handle importlib.metadata API changes across Python versions
if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
else:
    # Python 3.8-3.9: use importlib_metadata backport API
    try:
        from importlib.metadata import entry_points
    except ImportError:
        from importlib_metadata import entry_points  # type: ignore


class PluginRegistry:
    """Central registry for ATHF plugins."""

    _agents: Dict[str, Type[Any]] = {}
    _commands: Dict[str, Command] = {}

    @classmethod
    def register_agent(cls, name: str, agent_class: Type[Any]) -> None:
        """Register an agent plugin."""
        cls._agents[name] = agent_class

    @classmethod
    def register_command(cls, name: str, command: Command) -> None:
        """Register a CLI command plugin."""
        cls._commands[name] = command

    @classmethod
    def get_agent(cls, name: str) -> Optional[Type[Any]]:
        """Get registered agent by name."""
        return cls._agents.get(name)

    @classmethod
    def get_command(cls, name: str) -> Optional[Command]:
        """Get registered command by name."""
        return cls._commands.get(name)

    @classmethod
    def load_plugins(cls) -> None:
        """Auto-discover and load all installed plugins."""
        try:
            # Python 3.10+ uses group= parameter, 3.8-3.9 uses dict-like access
            if sys.version_info >= (3, 10):
                eps = entry_points(group="athf.commands")
            else:
                eps = entry_points().get("athf.commands", [])

            for ep in eps:
                command = ep.load()
                cls.register_command(ep.name, command)
        except Exception:
            pass  # No plugins installed yet

        try:
            # Python 3.10+ uses group= parameter, 3.8-3.9 uses dict-like access
            if sys.version_info >= (3, 10):
                eps = entry_points(group="athf.agents")
            else:
                eps = entry_points().get("athf.agents", [])

            for ep in eps:
                agent = ep.load()
                cls.register_agent(ep.name, agent)
        except Exception:
            pass  # No plugins installed yet
