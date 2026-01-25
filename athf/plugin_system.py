"""Plugin system for ATHF extensions."""
from typing import Dict, Type, Callable
import importlib.metadata
from click import Command


class PluginRegistry:
    """Central registry for ATHF plugins."""

    _agents: Dict[str, Type] = {}
    _commands: Dict[str, Command] = {}

    @classmethod
    def register_agent(cls, name: str, agent_class: Type) -> None:
        """Register an agent plugin."""
        cls._agents[name] = agent_class

    @classmethod
    def register_command(cls, name: str, command: Command) -> None:
        """Register a CLI command plugin."""
        cls._commands[name] = command

    @classmethod
    def get_agent(cls, name: str) -> Type:
        """Get registered agent by name."""
        return cls._agents.get(name)

    @classmethod
    def get_command(cls, name: str) -> Command:
        """Get registered command by name."""
        return cls._commands.get(name)

    @classmethod
    def load_plugins(cls) -> None:
        """Auto-discover and load all installed plugins."""
        try:
            for ep in importlib.metadata.entry_points(group='athf.commands'):
                command = ep.load()
                cls.register_command(ep.name, command)
        except Exception:
            pass  # No plugins installed yet

        try:
            for ep in importlib.metadata.entry_points(group='athf.agents'):
                agent = ep.load()
                cls.register_agent(ep.name, agent)
        except Exception:
            pass  # No plugins installed yet
