class PRNotFoundError(Exception):
    """
    PR not found
    """


class AuthorNotFoundError(Exception):
    """
    Author not found
    """


class TeamNotFoundError(Exception):
    """
    Team not found
    """


class PRExistsError(Exception):
    """
    PR already exists
    """


class PRMergedError(Exception):
    """
    PR was merged, changes are forbidden
    """


class ReviewerNotAssignedError(Exception):
    """
    Reviewer is not assigned to this PR
    """


class NoCandidateError(Exception):
    """
    No active candidates available for reassignment
    """
