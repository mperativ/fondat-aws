"""Configuration for tests."""

import os

# Test Agent IDs
TEST_AGENT_ID = os.environ.get("TEST_AGENT_ID")
if not TEST_AGENT_ID:
    raise ValueError("TEST_AGENT_ID environment variable is required")

# Test Agent Version
TEST_AGENT_VERSION = os.environ.get("TEST_AGENT_VERSION", "DRAFT")

# Test Flow IDs
TEST_FLOW_ID = os.environ.get("TEST_FLOW_ID")
if not TEST_FLOW_ID:
    raise ValueError("TEST_FLOW_ID environment variable is required")

# Test Prompt IDs
TEST_PROMPT_ID = os.environ.get("TEST_PROMPT_ID")
if not TEST_PROMPT_ID:
    raise ValueError("TEST_PROMPT_ID environment variable is required")

# Test Agent Alias IDs
TEST_AGENT_ALIAS_ID = os.environ.get("TEST_AGENT_ALIAS_ID")
if not TEST_AGENT_ALIAS_ID:
    raise ValueError("TEST_AGENT_ALIAS_ID environment variable is required")

# Test Action Group IDs
TEST_ACTION_GROUP_ID = os.environ.get("TEST_ACTION_GROUP_ID")
if not TEST_ACTION_GROUP_ID:
    raise ValueError("TEST_ACTION_GROUP_ID environment variable is required")

# Test Session ID
TEST_SESSION_ID = os.environ.get("TEST_SESSION_ID")
if not TEST_SESSION_ID:
    raise ValueError("TEST_SESSION_ID environment variable is required")
