"""Shared provider failure classification for repair and V4 model queries."""

class ProviderTransientError(RuntimeError):
    """Safe to retry through LitellmModel.query; never an abort exception."""

    def __init__(self, error_type, status_code):
        self.error_type, self.status_code = error_type, status_code
        # Do not include provider bodies, which can contain credentials.
        super().__init__(f'{error_type} (status {status_code}); reservation retained')


def provider_failure(exc):
    # Offline verification only needs the exception type, not LiteLLM's model
    # registry initialization. Paid model routes import this dependency first.
    import litellm

    response = getattr(exc, 'response', None)
    code = getattr(exc, 'status_code', None) or getattr(response, 'status_code', None)
    body = '\n'.join(str(part) for part in (
        getattr(response, 'text', ''), getattr(exc, 'body', ''),
        getattr(exc, 'message', ''), str(exc)) if part)
    message = body.casefold()
    if code in (401, 403):
        return 'AUTH_ERROR', code
    if (code == 402 or 'insufficient balance' in message or 'insufficient_balance' in message
            or (code == 429 and any(word in message for word in (
                'quota', 'budget', 'balance', 'insufficient', 'allocation exceeded',
                'credit exhausted', 'credits exhausted')))):
        return 'BUDGET_CAP', code
    if code in (408, 429, 500, 502, 503, 504) or isinstance(exc, (
            litellm.Timeout, litellm.APIConnectionError, litellm.ServiceUnavailableError)):
        return 'TRANSIENT', code
    return 'API_ERROR', code
