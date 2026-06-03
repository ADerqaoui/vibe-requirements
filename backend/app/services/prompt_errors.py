"""Prompt registry service errors."""


class PromptNotFoundError(Exception):
    """Raised when no enabled prompt exists for a task."""


class PromptVariableMissingError(Exception):
    """Raised when a prompt render variable is missing."""

    def __init__(self, variable_name: str):
        super().__init__(variable_name)
        self.variable_name = variable_name
