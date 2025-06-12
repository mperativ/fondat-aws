"""Configuration for tests."""

import os

# Test Agent IDs
TEST_AGENT_ID = os.environ.get('TEST_AGENT_ID')
if not TEST_AGENT_ID:
    raise ValueError("TEST_AGENT_ID environment variable is required")

# Test Flow IDs
TEST_FLOW_ID = os.environ.get('TEST_FLOW_ID')
if not TEST_FLOW_ID:
    raise ValueError("TEST_FLOW_ID environment variable is required")

# Test Prompt IDs
TEST_PROMPT_ID = os.environ.get('TEST_PROMPT_ID')
if not TEST_PROMPT_ID:
    raise ValueError("TEST_PROMPT_ID environment variable is required")

# Test Agent Alias IDs
TEST_AGENT_ALIAS_ID = os.environ.get('TEST_AGENT_ALIAS_ID')
if not TEST_AGENT_ALIAS_ID:
    raise ValueError("TEST_AGENT_ALIAS_ID environment variable is required")
