"""Invoke OpenAPI operations via the machine-generated OPERATIONS registry."""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Union
from urllib.parse import quote

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
            f"Unknown operationId {operation_id!r}. Regenerate with pnpm nx run modus-sdk:generate."
        ) from exc


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

    if method == "GET":
        return http.get(path, params=params)
    if method == "POST":
        return http.post(path, json=json_body)
    if method == "PATCH":
        return http.patch(path, json=json_body, params=params)
    if method == "PUT":
        raise NotImplementedError("PUT operations are not in the public modus-api spec")
    if method == "DELETE":
        return http.delete(path)
    raise ValueError(f"Unsupported HTTP method {method!r}")


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

    if method == "GET":
        return await http.get(path, params=params)
    if method == "POST":
        return await http.post(path, json=json_body)
    if method == "PATCH":
        return await http.patch(path, json=json_body, params=params)
    if method == "PUT":
        raise NotImplementedError("PUT operations are not in the public modus-api spec")
    if method == "DELETE":
        return await http.delete(path)
    raise ValueError(f"Unsupported HTTP method {method!r}")
