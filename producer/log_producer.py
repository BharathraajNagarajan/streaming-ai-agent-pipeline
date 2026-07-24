"""
log_producer.py

Simulates a log-shipping agent (the kind of process that would run alongside
a real microservice — an OTel collector, a Filebeat/Fluent Bit sidecar, or an
app-level logger) for a small set of fictional RetailPulse services. Streams
synthetic request-log events directly into Snowflake's BRONZE_SERVICE_EVENTS
table using the Snowpipe Streaming Python SDK.

This does not read from any real service — it generates realistic traffic
patterns and can optionally inject a cascading fault into one service, which
is what makes the downstream Dynamic Tables, dashboard, and Cortex Agent
demo worth watching in real time.

Usage:
    python log_producer.py --profile profile.json --rps 200
    python log_producer.py --profile profile.json --rps 200 --fault inventory_cascade --fault-after 30
    python log_producer.py --dry-run --fault inventory_cascade --fault-after 10
"""

import argparse
import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

SERVICES = [
    "cart-service",
    "checkout-service",
    "inventory-service",
    "recommendation-service",
    "auth-service",
    "notification-service",
    "search-service",
    "shipping-service",
]

ENDPOINTS = {
    "cart-service": ["/cart/add", "/cart/view", "/cart/remove"],
    "checkout-service": ["/checkout/start", "/checkout/confirm"],
    "inventory-service": ["/inventory/check", "/inventory/reserve"],
    "recommendation-service": ["/recommend/similar", "/recommend/trending"],
    "auth-service": ["/auth/login", "/auth/refresh"],
    "notification-service": ["/notify/email", "/notify/sms"],
    "search-service": ["/search/query", "/search/autocomplete"],
    "shipping-service": ["/shipping/rate", "/shipping/label"],
}

REGIONS = ["us-east-1", "us-west-2", "eu-west-1"]

# Fault scenarios: a downstream dependency degrades, and the calling service's
# error rate + latency climb as a result. Modeled after the class of incident
# this whole pipeline exists to catch quickly.
FAULTS = {
    "inventory_cascade": {
        "target_service": "inventory-service",
        "dependency": "warehouse-api",
        "message": "warehouse-api timeout after 3000ms; connection pool exhausted",
    },
    "auth_cascade": {
        "target_service": "auth-service",
        "dependency": "identity-provider",
        "message": "identity-provider p99 latency exceeded 4000ms; token refresh backing up",
    },
}


def make_event(service: str, faulted: bool, fault_cfg: dict) -> dict:
    endpoint = random.choice(ENDPOINTS[service])
    is_heartbeat = random.random() < 0.03

    if faulted:
        status_code = random.choices([200, 500, 503], weights=[15, 55, 30])[0]
        latency_ms = random.randint(2500, 5200)
        level = "ERROR" if status_code >= 500 else "WARN"
        dependency = fault_cfg["dependency"]
        message = fault_cfg["message"]
    else:
        status_code = random.choices([200, 201, 400, 500], weights=[92, 4, 3, 1])[0]
        latency_ms = random.randint(15, 220)
        level = "ERROR" if status_code >= 500 else "INFO"
        dependency = None
        message = "request completed" if status_code < 400 else "client error"

    if is_heartbeat:
        level = "HEARTBEAT"

    return {
        "event_id": str(uuid.uuid4()),
        "event_ts": datetime.now(timezone.utc).isoformat(),
        "service": service,
        "level": level,
        "status_code": status_code,
        "latency_ms": latency_ms,
        "endpoint": endpoint,
        "region": random.choice(REGIONS),
        "trace_id": str(uuid.uuid4()),
        "dependency": dependency,
        "message": message,
    }


def build_client(profile_path: str):
    """
    Lazily imports the Snowpipe Streaming SDK so --dry-run works without it
    installed, and constructs a StreamingIngestClient + channel bound to
    BRONZE_SERVICE_EVENTS. See profile.example.json for the expected shape
    of the profile file.
    """
    from snowflake.ingest.streaming import StreamingIngestClient

    with open(profile_path) as f:
        profile = json.load(f)

    client = StreamingIngestClient(
        "RETAILPULSE_LOG_PRODUCER",
        profile["database"],
        profile["schema"],
        # Auto-created default pipe, named "<TABLE_NAME>-streaming"
        f"{profile['table']}-streaming",
        profile_json=profile_path,
        properties=None,
    )
    channel, status = client.open_channel("RETAILPULSE_LOG_CHANNEL")
    print(f"Opened channel {status.channel_name} (status={status.status_code})")
    return client, channel


def run(args):
    fault_cfg = FAULTS.get(args.fault) if args.fault else None
    fault_target = fault_cfg["target_service"] if fault_cfg else None

    client, channel = (None, None)
    if not args.dry_run:
        client, channel = build_client(args.profile)

    print(f"Streaming at ~{args.rps} events/sec. Ctrl+C to stop.")
    if fault_cfg:
        print(f"Fault '{args.fault}' will trigger on {fault_target} after {args.fault_after}s")

    start = time.time()
    sent = 0
    offset = 0
    append_errors = 0
    try:
        while True:
            elapsed = time.time() - start
            faulted_now = fault_cfg is not None and elapsed >= args.fault_after

            batch_start = time.time()
            for _ in range(args.rps):
                service = random.choice(SERVICES)
                is_target = faulted_now and service == fault_target
                event = make_event(service, is_target, fault_cfg or {})

                if args.dry_run:
                    if sent % 50 == 0:
                        print(json.dumps(event))
                else:
                    offset += 1
                    row = {
                        "RAW_PAYLOAD": event,
                        # Streaming ingestion may not evaluate column DEFAULTs
                        # the way a normal INSERT does, so set this explicitly
                        # rather than relying on BRONZE_SERVICE_EVENTS'
                        # LANDED_AT DEFAULT CURRENT_TIMESTAMP() being honored.
                        "LANDED_AT": datetime.now(timezone.utc).isoformat(),
                    }
                    try:
                        channel.append_row(row, offset_token=str(offset))
                    except Exception as exc:  # surface rejects instead of failing silently
                        append_errors += 1
                        if append_errors <= 5:
                            print(f"[producer] append_row error at offset={offset}: {exc}")
                        if append_errors == 6:
                            print("[producer] suppressing further append_row error logs...")

                sent += 1

            if sent % (args.rps * 5) < args.rps:
                status_note = ""
                if not args.dry_run:
                    status = channel.get_channel_status()
                    status_note = (
                        f" committed_offset={status.latest_committed_offset_token}"
                        f" rows_error_count={getattr(status, 'rows_error_count', 'n/a')}"
                    )
                print(
                    f"[producer] sent={sent} append_errors={append_errors} "
                    f"elapsed={elapsed:.0f}s faulted={faulted_now}{status_note}"
                )

            # pace to ~1 second per batch of `rps` events
            time.sleep(max(0, 1.0 - (time.time() - batch_start)))
    except KeyboardInterrupt:
        print(f"\nStopped. Total events sent: {sent}, append_errors: {append_errors}")
    finally:
        if channel:
            channel.close()
        if client:
            client.close()


def parse_args():
    p = argparse.ArgumentParser(description="RetailPulse synthetic log producer")
    p.add_argument("--profile", default="profile.json", help="Path to Snowpipe Streaming profile JSON")
    p.add_argument("--rps", type=int, default=200, help="Target events per second")
    p.add_argument("--fault", choices=list(FAULTS.keys()), default=None, help="Fault scenario to inject")
    p.add_argument("--fault-after", type=int, default=30, help="Seconds before the fault begins")
    p.add_argument("--dry-run", action="store_true", help="Print events instead of streaming to Snowflake")
    return p.parse_args()


if __name__ == "__main__":
    run(parse_args())
