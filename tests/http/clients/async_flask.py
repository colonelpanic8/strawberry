from __future__ import annotations

from typing import Any, Dict, Optional

from flask import Flask
from flask import Request as FlaskRequest
from flask import Response as FlaskResponse
from strawberry.flask.views import AsyncGraphQLView as BaseAsyncGraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.schema.config import StrawberryConfig
from strawberry.types import ExecutionResult
from tests.http.schema import Query, get_schema

from ..context import get_context
from .base import ResultOverrideFunction
from .flask import FlaskHttpClient


class GraphQLView(BaseAsyncGraphQLView[Dict[str, object], Query]):
    methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"]

    result_override: ResultOverrideFunction = None

    def __init__(self, *args: Any, **kwargs: Any):
        self.result_override = kwargs.pop("result_override")
        super().__init__(*args, **kwargs)

    async def get_root_value(self, request: FlaskRequest) -> Query:
        await super().get_root_value(request)  # for coverage
        return Query()

    async def get_context(
        self, request: FlaskRequest, response: FlaskResponse
    ) -> Dict[str, object]:
        context = await super().get_context(request, response)

        return get_context(context)

    async def process_result(
        self, request: FlaskRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return await super().process_result(request, result)


class AsyncFlaskHttpClient(FlaskHttpClient):
    def __init__(
        self,
        graphiql: bool = True,
        allow_queries_via_get: bool = True,
        schema_config: Optional[StrawberryConfig] = None,
        result_override: ResultOverrideFunction = None,
    ):
        self.app = Flask(__name__)
        self.app.debug = True

        view = GraphQLView.as_view(
            "graphql_view",
            schema=get_schema(config=schema_config),
            graphiql=graphiql,
            allow_queries_via_get=allow_queries_via_get,
            result_override=result_override,
        )

        self.app.add_url_rule(
            "/graphql",
            view_func=view,
        )
