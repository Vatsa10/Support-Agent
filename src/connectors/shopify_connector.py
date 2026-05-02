import httpx

from connectors.base import Connector, ToolSpec, register


@register
class ShopifyConnector(Connector):
    kind = "shopify"

    def _base_url(self) -> str:
        shop = self.config.get("shop")
        if not shop:
            raise RuntimeError("Shopify config.shop missing (e.g. 'acme' for acme.myshopify.com)")
        version = self.config.get("api_version", "2024-07")
        return f"https://{shop}.myshopify.com/admin/api/{version}"

    def _headers(self) -> dict:
        token = self.creds.get("access_token")
        if not token:
            raise RuntimeError("Shopify access_token missing")
        return {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}

    def tool_specs(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="cancel_order",
                description="Cancel a Shopify order. Provide order_id, reason, and refund (bool) to also issue refund.",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                        "reason": {"type": "string", "enum": ["customer", "fraud", "inventory", "declined", "other"]},
                        "refund": {"type": "boolean", "default": False},
                    },
                    "required": ["order_id"],
                },
                kind=self.kind,
            ),
            ToolSpec(
                name="replace_order",
                description="Create replacement (duplicate) draft order for the customer of order_id, then cancel the original. Provide order_id and reason.",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["order_id"],
                },
                kind=self.kind,
            ),
        ]

    async def execute(self, tool_name: str, args: dict) -> dict:
        base = self._base_url()
        headers = self._headers()

        async with httpx.AsyncClient(timeout=30.0) as client:
            if tool_name == "cancel_order":
                order_id = args["order_id"]
                body = {"reason": args.get("reason", "customer")}
                if args.get("refund"):
                    body["refund"] = True
                resp = await client.post(
                    f"{base}/orders/{order_id}/cancel.json", json=body, headers=headers
                )
                data = _safe_json(resp)
                return _result(resp, data)

            if tool_name == "replace_order":
                order_id = args["order_id"]
                # 1) Fetch original
                r1 = await client.get(f"{base}/orders/{order_id}.json", headers=headers)
                if not r1.is_success:
                    return _result(r1, _safe_json(r1))
                order = (r1.json() or {}).get("order", {})
                line_items = [
                    {"variant_id": li.get("variant_id"), "quantity": li.get("quantity")}
                    for li in order.get("line_items", [])
                    if li.get("variant_id")
                ]
                customer = order.get("customer") or {}
                draft = {
                    "draft_order": {
                        "line_items": line_items,
                        "customer": {"id": customer.get("id")} if customer.get("id") else None,
                        "note": f"Replacement for order {order_id}: {args.get('reason','')}",
                        "use_customer_default_address": True,
                    }
                }
                draft["draft_order"] = {k: v for k, v in draft["draft_order"].items() if v is not None}
                r2 = await client.post(f"{base}/draft_orders.json", json=draft, headers=headers)
                draft_data = _safe_json(r2)
                if not r2.is_success:
                    return _result(r2, draft_data)
                # 2) Cancel original
                r3 = await client.post(
                    f"{base}/orders/{order_id}/cancel.json",
                    json={"reason": "other"},
                    headers=headers,
                )
                return {
                    "ok": r3.is_success,
                    "status_code": r3.status_code,
                    "data": {"draft_order": draft_data, "cancel_original": _safe_json(r3)},
                    "external_id": (draft_data.get("draft_order") or {}).get("id")
                        if isinstance(draft_data, dict) else None,
                }

        return {"ok": False, "error": f"unsupported tool {tool_name}"}


def _safe_json(resp: httpx.Response):
    try:
        return resp.json()
    except Exception:
        return {"text": resp.text}


def _result(resp: httpx.Response, data) -> dict:
    return {
        "ok": resp.is_success,
        "status_code": resp.status_code,
        "data": data,
        "external_id": (data.get("order") or {}).get("id")
            if isinstance(data, dict) and isinstance(data.get("order"), dict) else None,
    }
