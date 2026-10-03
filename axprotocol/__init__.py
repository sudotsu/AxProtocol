"""AxProtocol public Python API.

The package surface stays importable without requiring model credentials. The
heavy orchestration stack is imported only when `run_chain()` is actually
called; deterministic utilities, validators, detection helpers, and Sentinel
can therefore be used independently.
"""

__version__ = "2.4.0"


def run_chain(*args, **kwargs):
    """Run the AxProtocol role chain, importing the model runtime lazily."""
    from axp.orchestration import run_chain as _run_chain

    return _run_chain(*args, **kwargs)


# Offline/deterministic utilities are safe to expose eagerly.
from axp.utils.config_fingerprint import compute_config_hash
from axp.utils.session_logging import log_session

from axp.validation import validate_S, validate_A, validate_P, validate_C, validate_X

from axp.detection import (
    detect_sycophancy,
    detect_contradiction,
    detect_ambiguity_in_objective,
    unresolved_ambiguity,
    detect_wants_praise,
    precedence_inversion,
    overconfidence_no_evidence,
)

__all__ = [
    "run_chain",
    "compute_config_hash",
    "log_session",
    "validate_S",
    "validate_A",
    "validate_P",
    "validate_C",
    "validate_X",
    "detect_sycophancy",
    "detect_contradiction",
    "detect_ambiguity_in_objective",
    "unresolved_ambiguity",
    "detect_wants_praise",
    "precedence_inversion",
    "overconfidence_no_evidence",
    "__version__",
]
