import httpx

from connectors.base import Connector, ToolSpec, register


@register
class WebhookConnector(Connector):
    kind = "generic_webhook"

    def tool_specs(self) -> list[ToolSpec]:
        actions = self.config.get("actions") or ["call"]
        return [
            ToolSpec(
                name="generic_webhook_call",
                description=(
                    "Call tenant's configured webhook to perform a backend action. "
                    f"Allowed action_name values: {', '.join(actions)}."
                ),
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "action_name": {"type": "string", "enum": actions},
                        "payload": {"type": "object"},
                    },
                    "required": ["action_name", "payload"],
                },
                kind=self.kind,
            )
        ]

    async def execute(self, tool_name: str, args: dict) -> dict:
        if tool_name != "generic_webhook_call":
            return {"ok": False, "error": f"unsupported tool {tool_name}"}

        url = self.config.get("url")
        if not url:
            return {"ok": False, "error": "webhook url not configured"}

        action_name = args.get("action_name")
        allowed = self.config.get("actions") or []
        if allowed and action_name not in allowed:
            return {"ok": False, "error": f"action {action_name} not allowed"}

        headers = {"Content-Type": "application/json"}
        auth_header = self.creds.get("auth_header_value")
        auth_header_name = self.creds.get("auth_header_name", "Authorization")
        if auth_header:
            headers[auth_header_name] = auth_header

        body = {"action": action_name, "payload": args.get("payload", {})}

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, json=body, headers=headers)

        try:
            data = resp.json()
        except Exception:
            data = {"text": resp.text}

        return {
            "ok": resp.is_success,
            "status_code": resp.status_code,
            "data": data,
            "external_id": data.get("id") if isinstance(data, dict) else None,
        }
