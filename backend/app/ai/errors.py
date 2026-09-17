"""AI runtime exception hierarchy."""


class ModelRuntimeError(RuntimeError):
    """Base error raised by the model runtime."""


class ProviderUnavailableError(ModelRuntimeError):
    """The selected provider cannot currently accept a request."""


class CapabilityError(ModelRuntimeError):
    """An executor does not satisfy required capabilities."""


class StructuredOutputError(ModelRuntimeError):
    """Provider output failed schema validation."""


class AllProvidersFailedError(ModelRuntimeError):
    """Every eligible provider failed after retries."""

    def __init__(self, failures: dict[str, str]) -> None:
        self.failures = failures
        details = "; ".join(f"{provider}: {reason}" for provider, reason in failures.items())
        super().__init__(f"all providers failed: {details}")
