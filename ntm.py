#!/usr/bin/env python3
# ntm.py — Network Traffic Monitor

import psutil
import time
import sys
import json
import argparse
from typing import Dict


# ===================== UTILS =====================

def humanize_bytes(value: float, rate: bool = False) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    idx = 0

    while value >= 1024 and idx < len(units) - 1:
        value /= 1024
        idx += 1

    suffix = "/s" if rate else ""
    return f"{value:.1f} {units[idx]}{suffix}"


# ===================== DATA COLLECTOR =====================

class TrafficCollector:
    def __init__(self, iface: str, use_ema: bool = True, alpha: float = 0.2):
        counters = psutil.net_io_counters(pernic=True)
        if not counters:
            raise RuntimeError("No network interfaces found")

        self.iface = iface
        self.use_ema = use_ema
        self.alpha = alpha

        self.start_time = time.time()
        self.last_time = self.start_time

        self.start_counters = self._read_counters()
        self.prev_counters = self.start_counters.copy()

        self.sent_ema = 0.0
        self.recv_ema = 0.0
        self.ema_initialized = False

    def _read_counters(self) -> Dict[str, int]:
        counters = psutil.net_io_counters(pernic=True)

        if self.iface == "all":
            return {
                "sent": sum(c.bytes_sent for c in counters.values()),
                "recv": sum(c.bytes_recv for c in counters.values()),
            }

        if self.iface not in counters:
            raise ValueError(f"Interface '{self.iface}' not found")

        c = counters[self.iface]
        return {"sent": c.bytes_sent, "recv": c.bytes_recv}

    def sample(self) -> dict:
        now = time.time()
        interval = max(now - self.last_time, 0.01)

        try:
            current = self._read_counters()
        except (ValueError, KeyError):
            print("Network interface lost. Exiting.")
            sys.exit(1)

        sent_rate = (current["sent"] - self.prev_counters["sent"]) / interval
        recv_rate = (current["recv"] - self.prev_counters["recv"]) / interval

        if self.use_ema:
            if not self.ema_initialized:
                self.sent_ema = sent_rate
                self.recv_ema = recv_rate
                self.ema_initialized = True
            else:
                self.sent_ema = self.alpha * sent_rate + (1 - self.alpha) * self.sent_ema
                self.recv_ema = self.alpha * recv_rate + (1 - self.alpha) * self.recv_ema
        else:
            self.sent_ema = sent_rate
            self.recv_ema = recv_rate

        total_sent = current["sent"] - self.start_counters["sent"]
        total_recv = current["recv"] - self.start_counters["recv"]

        self.prev_counters = current
        self.last_time = now

        return {
            "iface": self.iface,
            "interval": interval,
            "sent_Bps": sent_rate,
            "recv_Bps": recv_rate,
            "sent_ema_Bps": self.sent_ema,
            "recv_ema_Bps": self.recv_ema,
            "ema_enabled": self.use_ema,
            "ema_alpha": self.alpha,
            "total_sent_B": total_sent,
            "total_recv_B": total_recv,
            "uptime": now - self.start_time,
            "timestamp": now,
        }


# ===================== RENDERERS =====================

class Renderer:
    def render(self, data: dict):
        raise NotImplementedError


class PlainRenderer(Renderer):
    def render(self, d: dict):
        print(
            f"[{time.strftime('%H:%M:%S')}] "
            f"OUT {humanize_bytes(d['sent_Bps'], True)} | "
            f"IN {humanize_bytes(d['recv_Bps'], True)} | "
            f"TOTAL {humanize_bytes(d['total_sent_B'])}/"
            f"{humanize_bytes(d['total_recv_B'])}"
        )


class JsonRenderer(Renderer):
    def render(self, d: dict):
        print(json.dumps(d, ensure_ascii=False))


class AnsiRenderer(Renderer):
    def __init__(self, view: str = "both"):
        self.view = view
        self.max_sent = 1.0
        self.max_recv = 1.0
        self.bar_width = 50

    def _bar(self, value, max_value):
        ratio = min(value / max_value, 1.0)
        filled = int(ratio * self.bar_width)
        return "█" * filled + " " * (self.bar_width - filled)

    def render(self, d: dict):
        sys.stdout.write("\033[2J\033[H")

        raw_sent = d["sent_Bps"]
        raw_recv = d["recv_Bps"]
        ema_sent = d["sent_ema_Bps"]
        ema_recv = d["recv_ema_Bps"]

        if self.view == "raw":
            bar_sent, bar_recv = raw_sent, raw_recv
        else:
            bar_sent, bar_recv = ema_sent, ema_recv

        self.max_sent = max(self.max_sent, bar_sent)
        self.max_recv = max(self.max_recv, bar_recv)

        mode = self.view.upper()
        print("\033[1;34m" + "=" * 60)
        print(f"NETWORK TRAFFIC [{d['iface']}] ({mode})".center(60))
        print("=" * 60 + "\033[0m\n")

        print("\033[1mCurrent Speed:\033[0m")

        if self.view == "both":
            print(
                f"  OUT: raw \033[90m{humanize_bytes(raw_sent, True):>10}\033[0m | "
                f"avg \033[32m{humanize_bytes(ema_sent, True):>10}\033[0m"
            )
            print(
                f"  IN:  raw \033[90m{humanize_bytes(raw_recv, True):>10}\033[0m | "
                f"avg \033[36m{humanize_bytes(ema_recv, True):>10}\033[0m"
            )
        elif self.view == "ema":
            print(f"  OUT: \033[32m{humanize_bytes(ema_sent, True):>12}\033[0m")
            print(f"  IN:  \033[36m{humanize_bytes(ema_recv, True):>12}\033[0m")
        else:
            print(f"  OUT: \033[32m{humanize_bytes(raw_sent, True):>12}\033[0m")
            print(f"  IN:  \033[36m{humanize_bytes(raw_recv, True):>12}\033[0m")

        print("\n\033[1mTraffic Level:\033[0m")
        print(f"  OUT [\033[32m{self._bar(bar_sent, self.max_sent)}\033[0m]")
        print(f"  IN  [\033[36m{self._bar(bar_recv, self.max_recv)}\033[0m]")

        print("\n\033[1mTotal since start:\033[0m")
        print(f"  Sent: {humanize_bytes(d['total_sent_B'])}")
        print(f"  Recv: {humanize_bytes(d['total_recv_B'])}")
        print(f"  Time: {int(d['uptime'])} sec")

        print("\n\033[90m" + "-" * 60)
        print("Ctrl+C to exit | " + time.strftime("%H:%M:%S"))
        sys.stdout.flush()


# ===================== CLI =====================

def main():
    parser = argparse.ArgumentParser(description="Network Traffic Monitor")
    parser.add_argument("--iface", default="all", help="Interface name or 'all'")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--plain", action="store_true", help="Plain text output")
    parser.add_argument("--interval", type=float, default=1.0, help="Refresh interval")

    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--count", type=int, help="Number of iterations")

    parser.add_argument("--ema", action="store_true", default=True)
    parser.add_argument("--no-ema", action="store_true", help="Disable EMA")
    parser.add_argument("--ema-alpha", type=float, default=0.2)

    parser.add_argument(
        "--view",
        choices=["raw", "ema", "both"],
        default="both",
        help="Display mode"
    )

    args = parser.parse_args()

    use_ema = not args.no_ema
    if not (0 < args.ema_alpha <= 1):
        print("EMA alpha must be between 0 and 1")
        sys.exit(1)

    collector = TrafficCollector(
        args.iface,
        use_ema=use_ema,
        alpha=args.ema_alpha
    )

    if args.json:
        renderer = JsonRenderer()
    elif args.plain:
        renderer = PlainRenderer()
    else:
        renderer = AnsiRenderer(view=args.view)

    iterations = 1 if args.once else args.count
    i = 0

    try:
        while True:
            data = collector.sample()
            renderer.render(data)
            i += 1

            if iterations is not None and i >= iterations:
                break

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
