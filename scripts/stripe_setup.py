"""One-shot (idempotent) Stripe setup for Driftwatch. Creates the Dev and Ops products,
their AUD monthly prices, and a payment link each. Safe to re-run: looks up by the
`driftwatch_tier` metadata key before creating anything.

Key is read from STRIPE_SECRET_KEY or a path in STRIPE_KEY_FILE. Never passed as an argument.
Uses only: products:write, prices:write, payment_links:write (plus reads of the same).
No stripe SDK dependency — plain HTTPS so it runs anywhere python does.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.stripe.com/v1"
TAX_CODE = "txcd_10103001"  # Software as a Service (SaaS), business use — required by Managed Payments

TIERS = {
    "dev": {"name": "Driftwatch Dev", "amount": 22900, "currency": "aud",
            "description": "Dependency-aware breaking-change alerts for one repo. 100 sources, Slack/email, weekly brief."},
    "ops": {"name": "Driftwatch Ops", "amount": 74900, "currency": "aud",
            "description": "Everything in Dev plus 300 sources incl. bot-walled docs, compliance questionnaire, audit log."},
}


def _key() -> str:
    k = os.environ.get("STRIPE_SECRET_KEY") or (Path(os.environ["STRIPE_KEY_FILE"]).read_text().strip() if os.environ.get("STRIPE_KEY_FILE") else "")
    if not k.startswith(("sk_live_", "rk_live_", "sk_test_", "rk_test_")):
        sys.exit("No Stripe key in STRIPE_SECRET_KEY or STRIPE_KEY_FILE")
    return k


def call(method: str, path: str, data: dict | None = None) -> dict:
    body = urllib.parse.urlencode(_flatten(data or {})).encode() if data else None
    req = urllib.request.Request(f"{API}{path}", data=body, method=method,
                                 headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        err = json.load(e).get("error", {})
        sys.exit(f"Stripe {e.code} on {method} {path}: {err.get('message')}")


def _flatten(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        key = f"{prefix}[{k}]" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        elif isinstance(v, list):
            for i, item in enumerate(v):
                out.update(_flatten(item, f"{key}[{i}]") if isinstance(item, dict) else {f"{key}[{i}]": item})
        else:
            out[key] = v
    return out


def ensure(tier: str, spec: dict) -> dict:
    # product
    q = urllib.parse.quote('metadata["driftwatch_tier"]:"%s"' % tier)
    found = call("GET", f"/products/search?query={q}&limit=1")["data"]
    product = found[0] if found else call("POST", "/products", {
        "name": spec["name"], "description": spec["description"], "tax_code": TAX_CODE,
        "metadata": {"driftwatch_tier": tier, "managed_by": "driftwatch-vault"}})
    if product.get("tax_code") != TAX_CODE:
        product = call("POST", f"/products/{product['id']}", {"tax_code": TAX_CODE})
    # price (active, matching amount/currency/monthly)
    prices = call("GET", f"/prices?product={product['id']}&active=true&limit=10")["data"]
    price = next((p for p in prices if p["unit_amount"] == spec["amount"] and p["currency"] == spec["currency"]
                  and (p.get("recurring") or {}).get("interval") == "month"), None)
    if not price:
        price = call("POST", "/prices", {"product": product["id"], "unit_amount": spec["amount"], "currency": spec["currency"],
                                         "recurring": {"interval": "month"}, "metadata": {"driftwatch_tier": tier}})
    # payment link
    links = [l for l in call("GET", "/payment_links?active=true&limit=100")["data"] if l.get("metadata", {}).get("driftwatch_tier") == tier]
    link = links[0] if links else call("POST", "/payment_links", {
        "line_items": [{"price": price["id"], "quantity": 1}],
        "allow_promotion_codes": "true",
        "metadata": {"driftwatch_tier": tier},
        "after_completion": {"type": "hosted_confirmation", "hosted_confirmation": {
            "custom_message": "You're in. Reply to the receipt email with your repo URL (read-only access is fine) and your first brief lands within one cycle."}},
    })
    return {"tier": tier, "product_id": product["id"], "price_id": price["id"], "payment_link": link["url"],
            "amount": f"{spec['currency'].upper()} {spec['amount']/100:.2f}/month", "livemode": product.get("livemode")}


if __name__ == "__main__":
    out = [ensure(t, s) for t, s in TIERS.items()]
    print(json.dumps(out, indent=1))
    dest = Path(os.environ.get("STRIPE_CONFIG_OUT", Path(__file__).resolve().parent.parent / "config" / "stripe.json"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({o["tier"]: o for o in out}, indent=1))
    print(f"\nwrote {dest} · livemode={out[0]['livemode']}")
