import enum
from enum import auto


class QuerySource(enum.Enum):
    USER = auto()
    ROBEAU = auto()
    SYSTEM = auto()
    GREETING = auto()
    MODIFIER = auto()


# Query source aliases
USER = QuerySource.USER
ROBEAU = QuerySource.ROBEAU
SYSTEM = QuerySource.SYSTEM
GREETING = QuerySource.GREETING
MODIFIER = QuerySource.MODIFIER


class TransmissionsInput(enum.Enum):
    # IMPORTANT: These values must match the database text values
    EXPECTATIONS_SET_MESSAGE = "EXPECTATIONS SET"
    EXPECTATIONS_SUCCESS_MESSAGE = "EXPECTATIONS SUCCESS"
    EXPECTATIONS_FAILURE_MESSAGE = "EXPECTATIONS FAILURE"

    ANY_MATCHING_PROMPT_OR_WHISPER_MESSAGE = "ANY MATCHING PROMPT OR WHISPER"
    NO_MATCHING_PROMPT_OR_WHISPER_MESSAGE = "NO MATCHING PROMPT OR WHISPER"


class TransmissionsOutput(enum.Enum):
    # IMPORTANT: These values must match the database text values
    RESET_EXPECTATIONS_MESSAGE = "RESET EXPECTATIONS"


# Transmission aliases (Communication between the script and the database)
EXPECTATIONS_SET = TransmissionsInput.EXPECTATIONS_SET_MESSAGE.value
EXPECTATIONS_SUCCESS = TransmissionsInput.EXPECTATIONS_SUCCESS_MESSAGE.value
EXPECTATIONS_FAILURE = TransmissionsInput.EXPECTATIONS_FAILURE_MESSAGE.value

ANY_MATCHING_PROMPT_OR_WHISPER = (
    TransmissionsInput.ANY_MATCHING_PROMPT_OR_WHISPER_MESSAGE.value
)
NO_MATCHING_PROMPT_OR_WHISPER = (
    TransmissionsInput.NO_MATCHING_PROMPT_OR_WHISPER_MESSAGE.value
)

RESET_EXPECTATIONS = TransmissionsOutput.RESET_EXPECTATIONS_MESSAGE.value

transmissions_output_aliases = [RESET_EXPECTATIONS]
