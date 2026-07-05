"""Invoke OpenAPI operations via the machine-generated OPERATIONS registry."""
from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterator, Mapping, Optional, Union
from urllib.parse import quote

from ._config import resolve_service_base_url
from ._generated.operations import OPERATIONS, OperationSpec
from ._http import AsyncHttpClient, HttpClient

HttpLike = Union[HttpClient, AsyncHttpClient]


def _format_path(template: str, path_params: Mapping[str, Any]) -> str:
    segments = template.split("/")
    formatted: list[str] = []
    for segment in segments:
        if segment.startswith("{") and segment.endswith("}"):
            key = segment[1:-1]
            if key not in path_params:
                raise ValueError(f"Missing path parameter {key!r} for {template!r}")
            formatted.append(quote(str(path_params[key]), safe=""))
        else:
            formatted.append(segment)
    return "/".join(formatted)


def get_operation(operation_id: str) -> OperationSpec:
    try:
        return OPERATIONS[operation_id]
    except KeyError as exc:
        raise KeyError(
            f"Unknown API operation {operation_id!r}. "
            "Upgrade modus-sdk or report a version mismatch."
        ) from exc


def format_operation_path(
    operation_id: str,
    path_params: Optional[Mapping[str, Any]] = None,
) -> str:
    """Resolve an operation's URL path from the generated registry.

    Used by streaming resources (e.g. scope/workflow runs) so agent-service run
    paths come from the spec rather than a hardcoded literal.
    """
    return _format_path(get_operation(operation_id)["path"], path_params or {})


def operation_base_url(http: HttpLike, op: OperationSpec) -> str:
    return resolve_service_base_url(
        http.config,
        op["service"],
        op["server_url"],
    )


def invoke_operation(
    http: HttpClient,
    operation_id: str,
    *,
    path_params: Optional[Mapping[str, Any]] = None,
    query: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
) -> Any:
    """Call a spec operation through HttpClient (sync)."""
    op = get_operation(operation_id)
    path = _format_path(op["path"], path_params or {})
    method = op["method"]
    params = query or None
    base_url = operation_base_url(http, op)

    if method == "GET":
        return http.get(path, params=params, base_url=base_url)
    if method == "POST":
        return http.post(path, json=json_body, base_url=base_url)
    if method == "PATCH":
        return http.patch(path, json=json_body, params=params, base_url=base_url)
    if method == "PUT":
        raise NotImplementedError("PUT operations are not in the public modus-api spec")
    if method == "DELETE":
        return http.delete(path, base_url=base_url)
    raise ValueError(f"Unsupported HTTP method {method!r}")


def invoke_operation_stream(
    http: HttpClient,
    operation_id: str,
    *,
    path_params: Optional[Mapping[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
) -> Iterator[str]:
    """Stream a spec operation through HttpClient."""
    op = get_operation(operation_id)
    path = _format_path(op["path"], path_params or {})
    return http.stream(op["method"], path, json=json_body, base_url=operation_base_url(http, op))


async def invoke_operation_async(
    http: AsyncHttpClient,
    operation_id: str,
    *,
    path_params: Optional[Mapping[str, Any]] = None,
    query: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
) -> Any:
    """Call a spec operation through AsyncHttpClient."""
    op = get_operation(operation_id)
    path = _format_path(op["path"], path_params or {})
    method = op["method"]
    params = query or None
    base_url = operation_base_url(http, op)

    if method == "GET":
        return await http.get(path, params=params, base_url=base_url)
    if method == "POST":
        return await http.post(path, json=json_body, base_url=base_url)
    if method == "PATCH":
        return await http.patch(path, json=json_body, params=params, base_url=base_url)
    if method == "PUT":
        raise NotImplementedError("PUT operations are not in the public modus-api spec")
    if method == "DELETE":
        return await http.delete(path, base_url=base_url)
    raise ValueError(f"Unsupported HTTP method {method!r}")


def invoke_operation_stream_async(
    http: AsyncHttpClient,
    operation_id: str,
    *,
    path_params: Optional[Mapping[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
) -> AsyncIterator[str]:
    """Stream a spec operation through AsyncHttpClient."""
    op = get_operation(operation_id)
    path = _format_path(op["path"], path_params or {})
    return http.stream(op["method"], path, json=json_body, base_url=operation_base_url(http, op))
