"""Plugin system for ATHF extensions."""

from importlib.metadata import entry_points
from typing import Any, Dict, Optional, Type

from click import Command


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
            eps = entry_points(group="athf.commands")

            for ep in eps:
                command = ep.load()
                cls.register_command(ep.name, command)
        except Exception:
            pass  # No plugins installed yet

        try:
            eps = entry_points(group="athf.agents")

            for ep in eps:
                agent = ep.load()
                cls.register_agent(ep.name, agent)
        except Exception:
            pass  # No plugins installed yet
