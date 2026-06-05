"""Prompt registry service errors."""


class PromptNotFoundError(Exception):
    """Raised when no enabled prompt exists for a task."""


class PromptVariableMissingError(Exception):
    """Raised when a prompt render variable is missing."""

    def __init__(self, variable_name: str):
        super().__init__(variable_name)
        self.variable_name = variable_name


class PromptTemplateInvalidError(Exception):
    """Raised when a prompt template fails save-time validation."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class PromptRenderError(Exception):
    """Raised when rendering fails for a malformed stored template."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class PromptDisabledError(Exception):
    """Raised when an explicit prompt selection points at a disabled row."""


class PromptLayerMismatchError(Exception):
    """Raised when an explicit prompt belongs to another specific layer."""
