import base64

import httpx

from connectors.base import Connector, ToolSpec, register


@register
class ZendeskConnector(Connector):
    kind = "zendesk"

    def _base_url(self) -> str:
        sub = self.config.get("subdomain")
        if not sub:
            raise RuntimeError("Zendesk config.subdomain missing")
        return f"https://{sub}.zendesk.com/api/v2"

    def _auth_header(self) -> dict:
        email = self.creds.get("email")
        token = self.creds.get("api_token")
        if not email or not token:
            raise RuntimeError("Zendesk creds missing email/api_token")
        raw = f"{email}/token:{token}".encode("utf-8")
        return {"Authorization": "Basic " + base64.b64encode(raw).decode("ascii")}

    def tool_specs(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="close_zendesk_ticket",
                description="Close a Zendesk ticket. Provide ticket_id and a public_comment to leave on close.",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "ticket_id": {"type": "string"},
                        "public_comment": {"type": "string"},
                    },
                    "required": ["ticket_id"],
                },
                kind=self.kind,
            ),
            ToolSpec(
                name="comment_zendesk_ticket",
                description="Add a comment to a Zendesk ticket. Provide ticket_id, body, and public (bool).",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "ticket_id": {"type": "string"},
                        "body": {"type": "string"},
                        "public": {"type": "boolean", "default": True},
                    },
                    "required": ["ticket_id", "body"],
                },
                kind=self.kind,
            ),
        ]

    async def execute(self, tool_name: str, args: dict) -> dict:
        base = self._base_url()
        headers = {**self._auth_header(), "Content-Type": "application/json"}
        ticket_id = args["ticket_id"]

        async with httpx.AsyncClient(timeout=20.0) as client:
            if tool_name == "close_zendesk_ticket":
                body = {"ticket": {"status": "closed"}}
                if args.get("public_comment"):
                    body["ticket"]["comment"] = {
                        "body": args["public_comment"],
                        "public": True,
                    }
                resp = await client.put(
                    f"{base}/tickets/{ticket_id}.json", json=body, headers=headers
                )
            elif tool_name == "comment_zendesk_ticket":
                body = {
                    "ticket": {
                        "comment": {
                            "body": args["body"],
                            "public": bool(args.get("public", True)),
                        }
                    }
                }
                resp = await client.put(
                    f"{base}/tickets/{ticket_id}.json", json=body, headers=headers
                )
            else:
                return {"ok": False, "error": f"unsupported tool {tool_name}"}

        try:
            data = resp.json()
        except Exception:
            data = {"text": resp.text}
        return {
            "ok": resp.is_success,
            "status_code": resp.status_code,
            "data": data,
            "external_id": str((data.get("ticket") or {}).get("id"))
                if isinstance(data, dict) and isinstance(data.get("ticket"), dict) else None,
        }
