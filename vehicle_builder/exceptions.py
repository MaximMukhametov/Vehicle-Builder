import json
from typing import Optional, Any

from aiohttp.typedefs import LooseHeaders
from aiohttp.web_exceptions import HTTPNotFound


class JsonHTTPNotFound(HTTPNotFound):
    def __init__(
            self,
            *,
            headers: Optional[LooseHeaders] = None,
            reason: Optional[str] = None, body: Any = None,
            text: Optional[str] = None,
            content_type: Optional[str] = None,
    ) -> None:
        text = json.dumps({"error": {"code": 404, "message": text}})
        content_type = "application/json"
        super().__init__(headers=headers, reason=reason, body=body, text=text, content_type=content_type)
