# backend/skills/base.py
#
# V2+ Extension Point — Abstract Base Skill
#
# In Version 2, concrete skills (BrowserSkill, StudySkill, etc.) will subclass
# BaseSkill and be registered in the SkillRegistry. For now this file defines
# the interface so that V2 can plug in cleanly without touching conversation.py.

from abc import ABC, abstractmethod


class BaseSkill(ABC):
    """
    Abstract base class for all EV skills.

    Every skill must implement:
        - name: short identifier string
        - description: human-readable description (used for intent routing in V2)
        - can_handle(intent): return True if this skill should handle the given intent
        - execute(context): run the skill and return a response string
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short unique identifier for this skill, e.g. 'browser'."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description, e.g. 'Searches the web using the browser'."""
        ...

    @abstractmethod
    def can_handle(self, intent: str) -> bool:
        """
        Return True if this skill should handle the given intent string.

        In V2 this will be powered by intent detection. For now it is a
        placeholder that always returns False.

        Args:
            intent: The detected intent from the user's message.

        Returns:
            bool: True if this skill can handle the intent.
        """
        ...

    @abstractmethod
    def execute(self, context: dict) -> str:
        """
        Execute the skill and return a response string.

        Args:
            context: A dict containing at minimum:
                - 'user_message': str  — the raw user message
                - 'intent': str        — the detected intent
                - 'history': list      — conversation history so far

        Returns:
            str: The skill's response to be shown/spoken to the user.
        """
        ...
