#!/usr/bin/env python3
"""Example: Using Splunk API integration with ATHF.

This script demonstrates how to programmatically execute Splunk queries
for threat hunting workflows.

Setup:
    export SPLUNK_HOST="splunk.example.com"
    export SPLUNK_TOKEN="your-token-here"

Usage:
    python splunk_example.py
"""

import json
from athf.core.splunk_client import create_client_from_env


def main():
    """Execute example threat hunting queries."""
    print("🔍 ATHF Splunk Integration Example\n")

    # Create client from environment variables
    try:
        client = create_client_from_env()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\nPlease set SPLUNK_HOST and SPLUNK_TOKEN environment variables:")
        print("  export SPLUNK_HOST='splunk.example.com'")
        print("  export SPLUNK_TOKEN='your-token-here'")
        return

    # Test connection
    print("Testing connection...")
    try:
        info = client.test_connection()
        if "entry" in info and info["entry"]:
            content = info["entry"][0].get("content", {})
            print(f"✅ Connected to Splunk {content.get('version', 'N/A')}\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}\n")
        return

    # List available indexes
    print("Available indexes:")
    try:
        indexes = client.get_indexes()
        for idx in sorted(indexes)[:10]:  # Show first 10
            print(f"  • {idx}")
        if len(indexes) > 10:
            print(f"  ... and {len(indexes) - 10} more")
        print()
    except Exception as e:
        print(f"❌ Error listing indexes: {e}\n")

    # Example Hunt Query 1: Windows Authentication Failures
    print("=" * 60)
    print("🎯 Hunt Example 1: Windows Authentication Failures")
    print("=" * 60)

    query1 = '''
    index=thrunt sourcetype="XmlWinEventLog" EventCode=4625
    | stats count by Account_Name, src_ip
    | where count > 5
    | sort -count
    '''

    print(f"\nQuery: {query1.strip()}")
    print("\nExecuting (all time)...")

    try:
        results = client.search(
            query=query1,
            earliest_time="0",
            latest_time="now",
            max_count=20
        )

        if results:
            print(f"⚠️  Found {len(results)} suspicious patterns:\n")
            for i, event in enumerate(results[:5], 1):
                src_ip = event.get("src_ip", "N/A")
                account = event.get("Account_Name", "N/A")
                count = event.get("count", 0)
                print(f"{i}. IP: {src_ip}, Account: {account}, Failures: {count}")
        else:
            print("✅ No suspicious activity detected")
    except Exception as e:
        print(f"❌ Query failed: {e}")

    print()

    # Example Hunt Query 2: Data Source Inventory
    print("=" * 60)
    print("🎯 Hunt Example 2: Data Source Inventory (thrunt index)")
    print("=" * 60)

    query2 = '''
    index=thrunt
    | stats count by sourcetype
    | sort -count
    '''

    print(f"\nQuery: {query2.strip()}")
    print("\nExecuting (all time)...")

    try:
        results = client.search(
            query=query2,
            earliest_time="0",
            latest_time="now",
            max_count=10
        )

        if results:
            print(f"\n📊 Top data sources in thrunt index:\n")
            for i, event in enumerate(results, 1):
                sourcetype = event.get("sourcetype", "N/A")
                count = event.get("count", 0)
                print(f"{i}. {sourcetype}: {count:,} events")
        else:
            print("No data found")
    except Exception as e:
        print(f"❌ Query failed: {e}")

    print()

    # Example Hunt Query 3: Network Traffic Analysis
    print("=" * 60)
    print("🎯 Hunt Example 3: Network Traffic Analysis (Async)")
    print("=" * 60)

    query3 = '''
    index=thrunt sourcetype="stream:*"
    | stats count by sourcetype
    | sort -count
    '''

    print(f"\nQuery: {query3.strip()}")
    print("\nExecuting async search (all time)...")

    try:
        results = client.search_async(
            query=query3,
            earliest_time="0",
            latest_time="now",
            max_results=10,
            max_wait=60  # Wait up to 1 minute
        )

        if results:
            print(f"\n📈 Network traffic distribution:\n")
            for i, event in enumerate(results, 1):
                sourcetype = event.get("sourcetype", "N/A")
                count = event.get("count", 0)
                print(f"{i}. {sourcetype}: {count:,} events")
        else:
            print("No data found")
    except TimeoutError:
        print("⏱️  Query timed out - try reducing time range")
    except Exception as e:
        print(f"❌ Query failed: {e}")

    print("\n" + "=" * 60)
    print("✅ Example complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  • Modify queries for your environment")
    print("  • Add to hunt files in hunts/ directory")
    print("  • Use 'athf splunk search' for CLI execution")
    print("  • See integrations/quickstart/splunk-api.md for more examples")


if __name__ == "__main__":
    main()
