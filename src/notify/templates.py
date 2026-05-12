"""HTML email templates. Plain, brand-aligned, no external assets."""

BLUE = "#1B4DFF"
INK = "#0A0A0A"


def _shell(title: str, body_html: str) -> str:
    return f"""<!doctype html>
<html><body style="margin:0;padding:0;background:#fafafa;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif;color:{INK};">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#fafafa;padding:32px 16px;">
  <tr><td align="center">
    <table width="540" cellpadding="0" cellspacing="0" style="background:#fff;border:1px solid #e5e5e5;">
      <tr><td style="padding:20px 28px;border-bottom:1px solid #e5e5e5;">
        <span style="display:inline-block;width:8px;height:8px;background:{BLUE};vertical-align:middle;margin-right:8px;"></span>
        <span style="font-family:Georgia,serif;font-size:18px;letter-spacing:-0.02em;">Resolve<span style="color:{BLUE}">.</span></span>
      </td></tr>
      <tr><td style="padding:32px 28px;font-size:14.5px;line-height:1.6;color:#0a0a0a;">
        <h1 style="font-family:Georgia,serif;font-weight:400;font-size:28px;line-height:1.1;margin:0 0 16px;letter-spacing:-0.025em;">{title}</h1>
        {body_html}
      </td></tr>
      <tr><td style="padding:18px 28px;border-top:1px solid #e5e5e5;font-size:11.5px;color:#a3a3a3;font-family:ui-monospace,Menlo,monospace;">
        Resolve · made for operators
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>"""


def password_reset(name: str, link: str) -> tuple[str, str]:
    return (
        "Reset your Resolve password",
        _shell(
            "Reset your password.",
            f"""<p>Hi {name or 'there'},</p>
<p>Use the link below to choose a new password. It expires in 30 minutes.</p>
<p style="margin:24px 0;"><a href="{link}" style="display:inline-block;background:{INK};color:#fff;text-decoration:none;padding:12px 18px;font-size:13.5px;">Reset password</a></p>
<p style="font-size:12.5px;color:#525252;">If you didn't request this, ignore this email — nothing will change.</p>
<p style="font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:#a3a3a3;word-break:break-all;">{link}</p>""",
        ),
    )


def email_verify(name: str, link: str) -> tuple[str, str]:
    return (
        "Confirm your email for Resolve",
        _shell(
            "Confirm your email.",
            f"""<p>Hi {name or 'there'},</p>
<p>Confirm your email address so we can send approval alerts, budget notices, and security updates to the right place.</p>
<p style="margin:24px 0;"><a href="{link}" style="display:inline-block;background:{INK};color:#fff;text-decoration:none;padding:12px 18px;font-size:13.5px;">Verify email</a></p>
<p style="font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:#a3a3a3;word-break:break-all;">{link}</p>""",
        ),
    )


def approval_queued(name: str, tool_name: str, reason: str, link: str) -> tuple[str, str]:
    return (
        f"Approval needed: {tool_name.replace('_', ' ')}",
        _shell(
            "An action is awaiting your review.",
            f"""<p>Hi {name or 'there'},</p>
<p>Resolve paused a <strong>{tool_name}</strong> call for human review.</p>
<p style="font-size:13px;color:#525252;background:#fafaf8;border:1px solid #e5e5e5;padding:10px 12px;">{reason}</p>
<p style="margin:24px 0;"><a href="{link}" style="display:inline-block;background:{INK};color:#fff;text-decoration:none;padding:12px 18px;font-size:13.5px;">Review approval queue</a></p>""",
        ),
    )


def budget_threshold(name: str, used: int, cap: int, pct: int, link: str) -> tuple[str, str]:
    return (
        f"Token budget at {pct}% — Resolve",
        _shell(
            f"Token budget at {pct}%.",
            f"""<p>Hi {name or 'there'},</p>
<p>You've used <strong>{used:,}</strong> of your <strong>{cap:,}</strong>-token monthly cap this month ({pct}%).</p>
<p style="margin:24px 0;"><a href="{link}" style="display:inline-block;background:{INK};color:#fff;text-decoration:none;padding:12px 18px;font-size:13.5px;">Configure budget</a></p>""",
        ),
    )


def integration_unhealthy(name: str, kind: str, link: str) -> tuple[str, str]:
    return (
        f"Integration unhealthy: {kind}",
        _shell(
            "An integration has stopped responding.",
            f"""<p>Hi {name or 'there'},</p>
<p>The circuit breaker opened on your <strong>{kind}</strong> integration after repeated failures. Action tools backed by {kind} are temporarily paused.</p>
<p style="margin:24px 0;"><a href="{link}" style="display:inline-block;background:{INK};color:#fff;text-decoration:none;padding:12px 18px;font-size:13.5px;">Check integration</a></p>""",
        ),
    )
