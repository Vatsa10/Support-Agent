import httpx

from connectors._http import IntegrationUnhealthy, request_with_retry
from connectors.base import Connector, ToolSpec, register

STRIPE_BASE = "https://api.stripe.com/v1"


@register
class StripeConnector(Connector):
    kind = "stripe"

    def tool_specs(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="issue_refund",
                description="Refund a Stripe charge. Provide charge_id (e.g. ch_... or pi_...), amount in major currency units, currency code, and reason.",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "charge_id": {"type": "string"},
                        "amount": {"type": "number", "description": "amount in major units, e.g. 12.50 for $12.50"},
                        "currency": {"type": "string", "default": "usd"},
                        "reason": {"type": "string"},
                    },
                    "required": ["charge_id", "amount"],
                },
                kind=self.kind,
            ),
            ToolSpec(
                name="cancel_subscription",
                description="Cancel a Stripe subscription. Provide subscription_id (sub_...) and reason.",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "subscription_id": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["subscription_id"],
                },
                kind=self.kind,
            ),
        ]

    def _auth(self) -> dict:
        api_key = self.creds.get("api_key")
        if not api_key:
            raise RuntimeError("Stripe api_key missing")
        return {"Authorization": f"Bearer {api_key}"}

    async def execute(self, tool_name: str, args: dict) -> dict:
        try:
            if tool_name == "issue_refund":
                charge_id = args["charge_id"]
                amount = args["amount"]
                minor = int(round(float(amount) * 100))
                form = {"amount": str(minor), "reason": args.get("reason", "requested_by_customer")}
                if charge_id.startswith("pi_"):
                    form["payment_intent"] = charge_id
                else:
                    form["charge"] = charge_id
                resp = await request_with_retry(
                    tenant_id=self.tenant_id or "",
                    kind=self.kind,
                    method="POST",
                    url=f"{STRIPE_BASE}/refunds",
                    headers={**self._auth(), "Content-Type": "application/x-www-form-urlencoded"},
                    data=form,
                )
            elif tool_name == "cancel_subscription":
                sub_id = args["subscription_id"]
                resp = await request_with_retry(
                    tenant_id=self.tenant_id or "",
                    kind=self.kind,
                    method="DELETE",
                    url=f"{STRIPE_BASE}/subscriptions/{sub_id}",
                    headers=self._auth(),
                )
            else:
                return {"ok": False, "error": f"unsupported tool {tool_name}"}
        except IntegrationUnhealthy as e:
            return {"ok": False, "error": "integration_unhealthy", "data": {"reason": str(e)}}

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
