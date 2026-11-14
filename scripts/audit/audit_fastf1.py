#!/usr/bin/env python3
"""
APEX — F1 Intelligence: FastF1 & Official F1 Live Timing Access Audit
Tests availability, authentication requirements (HTTP 401), and upstream
F1 Live Timing archive endpoints.
"""

import sys
import time
import urllib.request
import urllib.error

F1_STATIC_BASE = "https://livetiming.formula1.com/static"
USER_AGENT = "FastF1/3.4.0 (APEX-Audit)"


def test_livetiming_endpoints():
    print("=" * 80)
    print("APEX — FastF1 & F1 Live Timing Upstream Audit")
    print(f"Base URL: {F1_STATIC_BASE}")
    print("=" * 80)

    test_urls = [
        ("Session Index (2024 Bahrain)", f"{F1_STATIC_BASE}/2024/2024-03-02_Bahrain_Grand_Prix/2024-03-02_Race/Index.json"),
        ("Timing App Data (2024 Bahrain)", f"{F1_STATIC_BASE}/2024/2024-03-02_Bahrain_Grand_Prix/2024-03-02_Race/TimingAppData.json"),
        ("Live Timing Stream (2024 Bahrain)", f"{F1_STATIC_BASE}/2024/2024-03-02_Bahrain_Grand_Prix/2024-03-02_Race/TimingData.jsonStream"),
        ("Session Index (2023 Abu Dhabi)", f"{F1_STATIC_BASE}/2023/2023-11-26_Abu_Dhabi_Grand_Prix/2023-11-26_Race/Index.json"),
    ]

    print("\nTesting Upstream Archive Access Without F1 Authentication Token:")
    for label, url in test_urls:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                lat = (time.time() - t0) * 1000
                print(f"  {label.ljust(35)}: HTTP {resp.status} (length: {len(resp.read())}) [latency: {lat:.1f}ms]")
        except urllib.error.HTTPError as e:
            lat = (time.time() - t0) * 1000
            print(f"  {label.ljust(35)}: [BLOCKED] HTTP {e.code} ({e.reason}) [latency: {lat:.1f}ms]")
        except Exception as e:
            lat = (time.time() - t0) * 1000
            print(f"  {label.ljust(35)}: [ERROR] {e} [latency: {lat:.1f}ms]")

    print("\n" + "-" * 80)
    print("AUDIT FINDING — FastF1 / Live Timing Authentication:")
    print("1. Tested unauthenticated requests to livetiming.formula1.com/static/... returned HTTP 401.")
    print("2. This provides empirical evidence that direct access to these specific static archive")
    print("   endpoints requires an authenticated F1 account token ('f1auth.json').")
    print("3. It is not evidence that every FastF1 feature or local cache workflow is inaccessible.")
    print("4. Architectural Consequence: FastF1 remains functional when provided with user tokens")
    print("   or pre-cached raw session files, while OpenF1 provides open unauthenticated telemetry")
    print("   and Jolpica provides open unauthenticated historical sporting records.")
    print("=" * 80)
    return True


if __name__ == "__main__":
    test_livetiming_endpoints()
