"""DNS workaround: force resolution via 1.1.1.1 when system resolver fails.

Workaround for broken ISP DNS. Patches socket.getaddrinfo to fall back to
public DNS via dnspython if the system resolver returns gaierror.

Import once at process start (api.server, aiven.py, migrations) before any
network call.
"""
import socket
import os


def install() -> None:
    if os.getenv("DNS_FALLBACK", "1") not in ("1", "true", "yes"):
        return
    try:
        import dns.resolver  # type: ignore
    except ImportError:
        return  # dnspython not installed; skip silently

    public_dns = os.getenv("DNS_FALLBACK_SERVER", "1.1.1.1").split(",")
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = public_dns
    resolver.lifetime = 3.0

    original = socket.getaddrinfo

    def _fallback(host, port, *args, **kwargs):
        try:
            return original(host, port, *args, **kwargs)
        except socket.gaierror:
            try:
                ans = resolver.resolve(host, "A")
            except Exception:
                raise
            ip = ans[0].address
            return original(ip, port, *args, **kwargs)

    socket.getaddrinfo = _fallback  # type: ignore[assignment]
