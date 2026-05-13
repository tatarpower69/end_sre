#!/usr/bin/env python3
import asyncio
import aiohttp
import time
import json
from datetime import datetime
import sys

BASE_URL = "http://localhost"
SERVICES = {
    "auth": "http://localhost/api/auth",
    "user": "http://localhost/api/user",
    "product": "http://localhost/api/product",
    "order": "http://localhost/api/order",
    "chat": "http://localhost/api/chat",
    "payment": "http://localhost/api/payment",
    "notification": "http://localhost/api/notification",
}

results = {
    "total_requests": 0,
    "success": 0,
    "errors": 0,
    "latencies": [],
    "per_service": {}
}

for svc in SERVICES:
    results["per_service"][svc] = {"success": 0, "errors": 0, "latencies": []}

async def send_request(session, service_name, url, endpoint="/health"):
    start = time.time()
    try:
        async with session.get(f"{url}{endpoint}", timeout=aiohttp.ClientTimeout(total=5)) as resp:
            latency = time.time() - start
            results["latencies"].append(latency)
            results["per_service"][service_name]["latencies"].append(latency)
            results["total_requests"] += 1
            if resp.status < 400:
                results["success"] += 1
                results["per_service"][service_name]["success"] += 1
            else:
                results["errors"] += 1
                results["per_service"][service_name]["errors"] += 1
            return resp.status, latency
    except Exception as e:
        results["errors"] += 1
        results["total_requests"] += 1
        results["per_service"][service_name]["errors"] += 1
        return 0, time.time() - start

async def load_test(concurrent_users=10, duration_seconds=30):
    print(f"{'='*60}")
    print(f"  SRE Load Test — {len(SERVICES)} Services")
    print(f"  Concurrent Users: {concurrent_users}")
    print(f"  Duration: {duration_seconds}s")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            tasks = []
            for name, url in SERVICES.items():
                tasks.append(send_request(session, name, url))
            await asyncio.gather(*tasks)
            await asyncio.sleep(1 / concurrent_users)

    # Summary
    print(f"\n{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")

    avg_lat = sum(results["latencies"])/len(results["latencies"]) if results["latencies"] else 0
    sorted_lat = sorted(results["latencies"])
    p95_idx = int(len(sorted_lat) * 0.95) if sorted_lat else 0
    p99_idx = int(len(sorted_lat) * 0.99) if sorted_lat else 0
    p95_lat = sorted_lat[p95_idx] if sorted_lat else 0
    p99_lat = sorted_lat[p99_idx] if sorted_lat else 0
    error_rate = (results["errors"] / results["total_requests"] * 100) if results["total_requests"] else 0
    rps = results["total_requests"] / duration_seconds

    print(f"\n  Total Requests:  {results['total_requests']}")
    print(f"  Successful:      {results['success']}")
    print(f"  Errors:          {results['errors']}")
    print(f"  Error Rate:      {error_rate:.2f}%")
    print(f"  RPS:             {rps:.1f}")
    print(f"  Avg Latency:     {avg_lat*1000:.1f} ms")
    print(f"  P95 Latency:     {p95_lat*1000:.1f} ms")
    print(f"  P99 Latency:     {p99_lat*1000:.1f} ms")

    # SLO check
    print(f"\n  --- SLO Compliance ---")
    availability = (results["success"] / results["total_requests"] * 100) if results["total_requests"] else 0
    print(f"  Availability:    {availability:.2f}%  {'✅ PASS' if availability >= 99.0 else '❌ FAIL'} (target ≥ 99%)")
    print(f"  P95 Latency:     {p95_lat*1000:.1f} ms  {'✅ PASS' if p95_lat <= 0.2 else '❌ FAIL'} (target ≤ 200ms)")
    print(f"  Error Rate:      {error_rate:.2f}%  {'✅ PASS' if error_rate <= 1.0 else '❌ FAIL'} (target ≤ 1%)")

    # Per-service breakdown
    print(f"\n  --- Per-Service Breakdown ---")
    print(f"  {'Service':<20} {'Success':>8} {'Errors':>8} {'Avg Latency':>12}")
    print(f"  {'-'*50}")
    for svc, data in results["per_service"].items():
        svc_avg = sum(data["latencies"])/len(data["latencies"])*1000 if data["latencies"] else 0
        print(f"  {svc:<20} {data['success']:>8} {data['errors']:>8} {svc_avg:>9.1f} ms")

    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "concurrent_users": concurrent_users,
        "duration_seconds": duration_seconds,
        "total_requests": results["total_requests"],
        "success": results["success"],
        "errors": results["errors"],
        "error_rate_pct": round(error_rate, 2),
        "avg_latency_ms": round(avg_lat * 1000, 2),
        "p95_latency_ms": round(p95_lat * 1000, 2),
        "p99_latency_ms": round(p99_lat * 1000, 2),
        "rps": round(rps, 1),
        "slo_compliance": {
            "availability": availability >= 99.0,
            "latency_p95": p95_lat <= 0.2,
            "error_rate": error_rate <= 1.0
        }
    }
    with open("load_test_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to load_test_results.json")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    users = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    asyncio.run(load_test(users, duration))
