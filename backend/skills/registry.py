# backend/skills/registry.py
#
# V2+ Extension Point — Skill Registry
#
# In Version 2, skills will be registered here and the ConversationManager
# will call SkillRegistry.route(intent) to see if any skill should handle
# the request before falling back to raw Gemini.
#
# In Version 1 (MVP), route() always returns None → all requests go to Gemini.

from __future__ import annotations
from typing import Optional
from .base import BaseSkill


class SkillRegistry:
    """
    Maintains a list of registered skills and routes intents to the right one.

    Usage (V2+):
        registry = SkillRegistry()
        registry.register(BrowserSkill())
        skill = registry.route("search_web")
        if skill:
            response = skill.execute(context)
        else:
            response = gemini.send(history)
    """

    def __init__(self) -> None:
        self._skills: list[BaseSkill] = []

    def register(self, skill: BaseSkill) -> None:
        """
        Register a skill with the registry.

        Args:
            skill: An instance of a BaseSkill subclass.
        """
        self._skills.append(skill)
        print(f"[SkillRegistry] Registered skill: {skill.name}")

    def route(self, intent: str) -> Optional[BaseSkill]:
        """
        Find and return the first skill that can handle the given intent.

        In V1 (MVP) no skills are registered so this always returns None,
        which signals the ConversationManager to use Gemini directly.

        Args:
            intent: The detected intent string from the user's message.

        Returns:
            The matching BaseSkill, or None if no skill matches.
        """
        for skill in self._skills:
            if skill.can_handle(intent):
                return skill
        return None

    def list_skills(self) -> list[str]:
        """Return a list of registered skill names (useful for debugging)."""
        return [skill.name for skill in self._skills]
