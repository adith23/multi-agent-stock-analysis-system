class ReviewSubmissionError(ValueError):
    """Base error for a rejected PM review submission."""


class ReviewConflictError(ReviewSubmissionError):
    """Optimistic-lock or idempotency conflict."""


class ReviewExpiredError(ReviewSubmissionError):
    """Review request passed its decision deadline."""
