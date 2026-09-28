import logging

logger = logging.getLogger(__name__)
RATE_LIMIT_MESSAGE = "We're experiencing high traffic right now. Please try again in a moment."


class AIServiceError(Exception):
    def __init__(self, user_message, status_code=502):
        super().__init__(user_message)
        self.user_message = user_message
        self.status_code = status_code


def friendly_error(error):
    body = getattr(error, "body", "")
    if isinstance(body, (dict, list)):
        body = str(body)
    combined = f"{error} {body}".lower()
    if getattr(error, "status_code", None) == 429 or any(
        phrase in combined for phrase in ("rate limit", "rate-limit", "too many requests", "quota exceeded")
    ):
        return AIServiceError(RATE_LIMIT_MESSAGE, 429)
    logger.exception("AI service request failed", exc_info=error)
    return AIServiceError("AI analysis is temporarily unavailable. Please try again shortly.", 502)
