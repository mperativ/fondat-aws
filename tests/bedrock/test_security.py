"""Tests for bedrock security policies."""

import asyncio
import pytest
from fondat.aws.bedrock.resources.agents import AgentsResource
from fondat.security import Policy
from fondat.error import UnauthorizedError, ForbiddenError

# Helper policy functions
async def check_aws_auth():
    ctx = asyncio.current_task().operation.context
    if not ctx or "aws:PrincipalArn" not in ctx:
        raise UnauthorizedError("AWS credentials required")

async def check_admin_access():
    ctx = asyncio.current_task().operation.context
    if not ctx or "aws:PrincipalArn" not in ctx:
        raise UnauthorizedError("AWS credentials required")
    if "admin" not in ctx["aws:PrincipalArn"]:
        raise ForbiddenError("Admin access required")

# Utility to set the operation context for the test
def set_operation_context(ctx: dict | None):
    task = asyncio.current_task()
    task.operation = type("Operation", (), {"context": ctx})()

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "policies, context, expected_exc",
    [
        ([Policy(schemes=[])], None, None),
        ([Policy(rules=[check_aws_auth])], {"aws:PrincipalArn": "arn:aws:iam::123:user"}, None),
        ([Policy(rules=[check_aws_auth])], None, UnauthorizedError),
        ([Policy(rules=[check_admin_access])], {"aws:PrincipalArn": "arn:aws:iam::123:admin"}, None),
        ([Policy(rules=[check_admin_access])], {"aws:PrincipalArn": "arn:aws:iam::123:user"}, ForbiddenError),
        (None, None, None),
    ],
)
async def test_security_policies(policies, context, expected_exc, mock_clients, config):
    """Parametrized test for security policy enforcement."""
    agent_client, _ = mock_clients
    agent_client.list_agents.return_value = {"agentSummaries": []}

    resource = AgentsResource(
        config_agent=config,
        config_runtime=config,
        policies=policies,
    )

    # Set up the operation context for this scenario
    set_operation_context(context)

    if expected_exc:
        with pytest.raises(expected_exc):
            await resource.get()
    else:
        result = await resource.get()
        # Should return a non-error response and call the underlying client
        assert result is not None
        agent_client.list_agents.assert_called_once_with()
