from typing import Any

from litestar.datastructures import URL


def include_query_params(url: URL, **kwargs: Any) -> URL:
    query_params = url.query_params.copy()
    query_params.update(kwargs)
    return url.with_replacements(query=query_params)
