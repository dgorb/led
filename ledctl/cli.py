"""Tiny command line client for a running ledctl server.

    python -m ledctl.cli color '#ff00aa'
    python -m ledctl.cli fade '#ff00aa' '#00ffee' --period 4
    python -m ledctl.cli rainbow --period 20
    python -m ledctl.cli off | on | status
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def call(base, method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        base + path, data=data, method=method, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return json.load(res)
    except urllib.error.HTTPError as err:
        sys.exit(f"error: {json.load(err).get('error', err)}")
    except urllib.error.URLError as err:
        sys.exit(f"error: cannot reach {base}: {err.reason}")


def main():
    parser = argparse.ArgumentParser(prog="ledctl.cli")
    parser.add_argument("--url", default=os.environ.get("LED_URL", "http://127.0.0.1:5000"))
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("on")
    sub.add_parser("off")
    sub.add_parser("status")
    sub.add_parser("color").add_argument("color")
    fade = sub.add_parser("fade")
    fade.add_argument("start")
    fade.add_argument("end")
    fade.add_argument("--period", type=float, default=4)
    sub.add_parser("rainbow").add_argument("--period", type=float, default=20)
    sub.add_parser("effect").add_argument("name", help="e.g. candle")

    args = parser.parse_args()
    url = args.url.rstrip("/")
    if args.cmd == "status":
        result = call(url, "GET", "/api/state")
    elif args.cmd in ("on", "off"):
        result = call(url, "POST", "/api/power", {"on": args.cmd == "on"})
    elif args.cmd == "color":
        result = call(url, "POST", "/api/color", {"color": args.color})
    elif args.cmd == "fade":
        result = call(url, "POST", "/api/fade", {"start": args.start, "end": args.end, "period": args.period})
    elif args.cmd == "effect":
        result = call(url, "POST", "/api/effect", {"name": args.name})
    else:
        result = call(url, "POST", "/api/rainbow", {"period": args.period})
    print(json.dumps(result))


if __name__ == "__main__":
    main()
