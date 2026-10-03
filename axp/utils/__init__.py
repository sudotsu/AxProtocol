"""
AxProtocol utilities.

Offline utilities must remain usable without importing the OpenAI runtime.
LLM helpers are therefore exposed lazily while logging, config hashing,
Sentinel helpers, and other local utilities remain importable on their own.
"""

from .logging import configure_logging
from .helpers import (
    shingles,
    redundancy_score,
    uniqueness_nudge,
    extract_json_block,
    violates_exclusions,
    strict_reprompt,
    load_role_shapes,
)
from .sentinel import sentinel_verify
from .errors import append_session_error, write_sys_preview
from .session_logging import log_session, extract_kpi_rows
from .config_fingerprint import compute_config_hash, get_config_files_list


def __getattr__(name):
    """Lazily expose LLM helpers so offline tooling does not require OpenAI."""
    if name in {"get_llm_client", "call_llm"}:
        from .llm import get_llm_client, call_llm
        return {"get_llm_client": get_llm_client, "call_llm": call_llm}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "configure_logging",
    "get_llm_client",
    "call_llm",
    "shingles",
    "redundancy_score",
    "uniqueness_nudge",
    "extract_json_block",
    "violates_exclusions",
    "strict_reprompt",
    "load_role_shapes",
    "sentinel_verify",
    "append_session_error",
    "write_sys_preview",
    "log_session",
    "extract_kpi_rows",
    "compute_config_hash",
    "get_config_files_list",
]
