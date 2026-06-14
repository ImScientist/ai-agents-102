"""
main.py
Entry point for the Gmail AI Agent.
"""

import asyncio
from dotenv import load_dotenv

load_dotenv()  # must happen before importing agent (which imports openai)

from agent import run

if __name__ == "__main__":
    summary = asyncio.run(run())
    print(f"\n📋  Agent summary:\n{summary}")
