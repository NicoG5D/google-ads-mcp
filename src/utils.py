import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar

import grpc
from google.ads.googleads.errors import GoogleAdsException
from google.protobuf.json_format import MessageToDict

E = TypeVar("E")


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def load_dotenv(dotenv_path: str = ".env") -> None:
    path = Path(dotenv_path)
    if not path.is_absolute():
        # Try relative to the caller's file location before falling back to cwd
        caller_dir = Path(__file__).parent.parent
        candidate = caller_dir / dotenv_path
        if candidate.exists():
            path = candidate
    if not path.exists():
        return  # .env is optional — env vars may already be set by the caller

    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def resolve_customer_id(customer_id: Optional[str]) -> str:
    """Return customer_id if provided, otherwise fall back to GOOGLE_ADS_CUSTOMER_ID.

    Raises ValueError if neither is set.
    """
    from src.sdk_client import (
        get_default_customer_id,
    )  # local import avoids circular dep

    value = customer_id or get_default_customer_id()
    if not value:
        raise ValueError(
            "customer_id is required. Pass it explicitly or set GOOGLE_ADS_CUSTOMER_ID in .env."
        )
    return value.replace("-", "")


def format_customer_id(customer_id: str) -> str:
    """Format a customer ID by removing hyphens.

    Google Ads customer IDs can be provided with or without hyphens.
    This function ensures they are in the format expected by the API (without hyphens).

    Args:
        customer_id: The customer ID with or without hyphens (e.g., "123-456-7890" or "1234567890")

    Returns:
        The customer ID without hyphens (e.g., "1234567890")
    """
    return customer_id.replace("-", "")


def resolve_enum(enum_class: Any, value: str, param_name: str = "parameter") -> Any:
    """Safely convert a string to a protobuf enum value.

    Raises ``ValueError`` with a list of valid values instead of a raw
    ``AttributeError`` when the caller supplies an invalid name.
    """
    result = getattr(enum_class, value, None)
    if result is not None:
        return result
    try:
        valid = sorted(m.name for m in enum_class if not m.name.startswith("_"))
    except TypeError:
        valid = []
    raise ValueError(
        f"Invalid {param_name} '{value}'. Valid values: {', '.join(valid)}"
    )


def ensure_list(value: Any) -> List[str]:
    """Normalize a value to a list of strings.

    MCP clients may send array parameters as JSON-encoded strings
    (e.g., '["a", "b"]') instead of actual arrays. This handles both cases.
    """
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        value = value.strip()
        if value.startswith("["):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except (json.JSONDecodeError, ValueError):
                pass
        # Single value — wrap in a list
        return [value]
    return list(value)


def is_resource_exhausted(ex: Exception) -> bool:
    """Check if an exception is a gRPC RESOURCE_EXHAUSTED error.

    The Google Ads SDK interceptor intentionally does NOT wrap
    RESOURCE_EXHAUSTED in GoogleAdsException — it raises a raw
    grpc.RpcError so that api_core can retry it.  In our MCP layer
    we catch it ourselves to give the LLM a clear "do not retry" signal.
    """
    if isinstance(ex, grpc.RpcError) and hasattr(ex, "code"):
        try:
            return ex.code() == grpc.StatusCode.RESOURCE_EXHAUSTED
        except Exception:
            pass
    return False


RATE_LIMIT_MSG = (
    "RATE_LIMITED: Google Ads Planning API allows only 1 request per second "
    "per customer ID. Do NOT retry this request immediately. "
    "Wait at least 60 seconds before trying again."
)


def format_ads_error(ex: GoogleAdsException) -> str:
    """Extract LLM-readable error messages from a GoogleAdsException.

    Includes error code, field location, and message so the LLM can diagnose
    root causes (e.g. developer token access level, invalid field values).
    """
    parts: list[str] = []
    failure = getattr(ex, "failure", None)
    errors = getattr(failure, "errors", None)
    if errors is not None:
        try:
            for error in errors:
                # Build error_code string (e.g. "AUTHORIZATION_ERROR / DEVELOPER_TOKEN_NOT_APPROVED")
                error_code = getattr(error, "error_code", None)
                code_str = ""
                if error_code is not None:
                    # Find the first non-zero enum field on error_code
                    for field in error_code._meta.fields:  # type: ignore[union-attr]
                        val = getattr(error_code, field.name, None)
                        if val is not None and val != 0:
                            code_str = f"{field.name.upper()} / {type(val).__name__}.{val.name}"
                            break

                # Field location (e.g. "operations[0].create.advertising_channel_type")
                location = getattr(error, "location", None)
                loc_str = ""
                if location is not None:
                    field_path_elements = getattr(location, "field_path_elements", [])
                    if field_path_elements:
                        loc_parts = []
                        for el in field_path_elements:
                            idx = getattr(el, "index", None)
                            name = getattr(el, "field_name", "")
                            loc_parts.append(
                                f"{name}[{idx}]" if idx is not None else name
                            )
                        loc_str = f" [field: {'.'.join(loc_parts)}]"

                msg = error.message or "Unknown error"
                entry = (
                    f"[{code_str}]{loc_str} {msg}" if code_str else f"{msg}{loc_str}"
                )
                parts.append(entry)
        except (TypeError, AttributeError):
            parts = []

    if parts:
        summary = "; ".join(parts)
    elif failure is not None:
        str_method = getattr(failure, "__str__", None)
        summary = str_method() if callable(str_method) else str(failure)
    else:
        summary = str(ex)

    request_id = getattr(ex, "request_id", None)
    suffix = f" (request_id={request_id})" if request_id else ""
    return f"Google Ads API error: {summary}{suffix}"


def serialize_proto_message(
    message: Any, use_integers_for_enums: bool = False
) -> Dict[str, Any]:
    """Serialize a proto-plus message to a dictionary.

    Args:
        message: A proto-plus message object
        use_integers_for_enums: If True, return enum values as integers instead of strings

    Returns:
        A dictionary representation of the message
    """
    try:
        # For proto-plus messages, we need to convert to the underlying protobuf message
        if hasattr(message, "_pb"):
            # This is a proto-plus message
            return MessageToDict(
                message._pb,
                preserving_proto_field_name=True,
                use_integers_for_enums=use_integers_for_enums,
            )
        else:
            # This is a regular protobuf message
            return MessageToDict(
                message,
                preserving_proto_field_name=True,
                use_integers_for_enums=use_integers_for_enums,
            )
    except Exception as e:
        # Fallback to manual conversion if MessageToDict fails
        logger = get_logger(__name__)
        logger.warning(f"Failed to serialize message with MessageToDict: {e}")

        # Try to convert manually
        result = {}
        if hasattr(message, "__dict__"):
            for key, value in message.__dict__.items():
                if not key.startswith("_"):
                    result[key] = str(value) if value is not None else None
        return result
