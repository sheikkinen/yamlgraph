#!/usr/bin/env python
"""Standalone Resend email test."""

import os

import resend


def main():
    api_key = os.environ.get("RESEND_API_KEY")
    print(f"API Key present: {bool(api_key)}")
    if api_key:
        print(f"API Key prefix: {api_key[:8]}...")
    else:
        print("ERROR: RESEND_API_KEY not set!")
        return

    resend.api_key = api_key

    try:
        result = resend.Emails.send(
            {
                "from": "YAMLGraph <yamlgraph-no-reply@resend.dev>",
                "to": ["sami.j.p.heikkinen@gmail.com"],
                "subject": "YAMLGraph Test Email",
                "html": "<h1>Test</h1><p>If you see this, Resend is working!</p>",
            }
        )
        print(f"Result: {result}")
        print(f"Email ID: {result.get('id', 'unknown')}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
