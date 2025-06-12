from datetime import datetime, timezone
from fondat.aws.bedrock.domain import (
    Agent,
    AgentSummary,
    AgentVersion,
    AgentAlias,
    AgentCollaborator,
    AgentCollaboratorSummary,
    Flow,
    FlowSummary,
    Prompt,
    PromptSummary,
    Session,
    SessionSummary,
    MemorySession,
    Invocation,
    InvocationSummary,
    InvocationStep,
    InvocationStepSummary,
    ActionGroup,
    ActionGroupSummary,
    ActionGroupExecutor,
    ContentBlock,
    Payload,
    VersionSummary,
    AliasSummary,
)


def test_agent():
    # Test Agent creation
    agent = Agent(
        agent_id="test-agent",
        agent_arn="arn:aws:bedrock:us-east-1:123456789012:agent/test-agent",
        agent_name="Test Agent",
        agent_status="ACTIVE",
        created_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
        updated_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
    )

    assert agent.agent_id == "test-agent"
    assert agent.agent_name == "Test Agent"
    assert agent.agent_status == "ACTIVE"
    assert isinstance(agent.created_at, datetime)
    assert isinstance(agent.updated_at, datetime)


def test_agent_summary():
    # Test AgentSummary creation
    summary = AgentSummary(
        agent_id="test-agent",
        agent_name="Test Agent",
        status="ACTIVE",
        last_updated_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
    )

    assert summary.agent_id == "test-agent"
    assert summary.agent_name == "Test Agent"
    assert summary.status == "ACTIVE"
    assert isinstance(summary.last_updated_at, datetime)


def test_agent_version():
    # Test AgentVersion creation
    version = AgentVersion(
        version_arn="arn:aws:bedrock:us-east-1:123456789012:agent/test-agent/version/1",
        version_id="1",
        version="1",
        status="ACTIVE",
        created_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
        updated_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
        agent_id="test-agent",
        agent_name="Test Agent",
        agent_status="ACTIVE",
        agent_version="1",
    )

    assert version.version_id == "1"
    assert version.agent_id == "test-agent"
    assert version.status == "ACTIVE"


def test_agent_alias():
    # Test AgentAlias creation
    alias = AgentAlias(
        agent_alias_arn="arn:aws:bedrock:us-east-1:123456789012:agent/test-agent/alias/test",
        agent_alias_id="test",
        agent_alias_name="Test Alias",
        agent_alias_status="ACTIVE",
        agent_id="test-agent",
        created_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
        updated_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
    )

    assert alias.agent_alias_id == "test"
    assert alias.agent_alias_name == "Test Alias"
    assert alias.agent_id == "test-agent"


def test_agent_collaborator():
    # Test AgentCollaborator creation
    collaborator = AgentCollaborator(
        agent_id="test-agent",
        agent_version="1",
        collaborator_id="test-collab",
        collaborator_name="Test Collaborator",
        created_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
        last_updated_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
        agent_descriptor={"type": "test"},
    )

    assert collaborator.agent_id == "test-agent"
    assert collaborator.collaborator_id == "test-collab"
    assert collaborator.collaborator_name == "Test Collaborator"


def test_agent_collaborator_summary():
    # Test AgentCollaboratorSummary creation
    summary = AgentCollaboratorSummary(
        agent_id="test-agent",
        collaborator_id="test-collab",
        collaborator_type="test",
        created_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
    )

    assert summary.agent_id == "test-agent"
    assert summary.collaborator_id == "test-collab"
    assert summary.collaborator_type == "test"


def test_flow():
    # Test Flow creation
    flow = Flow(
        flow_arn="arn:aws:bedrock:us-east-1:123456789012:flow/test-flow",
        flow_id="test-flow",
        flow_name="Test Flow",
        status="ACTIVE",
        created_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
        updated_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
        definition={"type": "test"},
        version="1",
    )

    assert flow.flow_id == "test-flow"
    assert flow.flow_name == "Test Flow"
    assert flow.status == "ACTIVE"
    assert flow.version == "1"


def test_flow_summary():
    # Test FlowSummary creation
    summary = FlowSummary(
        flow_id="test-flow",
        flow_name="Test Flow",
        status="ACTIVE",
        created_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
    )

    assert summary.flow_id == "test-flow"
    assert summary.flow_name == "Test Flow"
    assert summary.status == "ACTIVE"


def test_prompt():
    # Test Prompt creation
    prompt = Prompt(
        arn="arn:aws:bedrock:us-east-1:123456789012:prompt/test-prompt",
        id="test-prompt",
        name="Test Prompt",
        version="1",
        variants=[{"type": "test"}],
        created_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
    )

    assert prompt.id == "test-prompt"
    assert prompt.name == "Test Prompt"
    assert prompt.version == "1"
    assert len(prompt.variants) == 1


def test_prompt_summary():
    # Test PromptSummary creation
    summary = PromptSummary(
        id="test-prompt",
        name="Test Prompt",
        created_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
    )

    assert summary.id == "test-prompt"
    assert summary.name == "Test Prompt"


def test_session():
    # Test Session creation
    session = Session(
        session_id="test-session",
        session_arn="arn:aws:bedrock:us-east-1:123456789012:session/test-session",
        session_status="ACTIVE",
        created_at="2024-03-20T10:30:00Z",
        session_metadata={"type": "test"},
    )

    assert session.session_id == "test-session"
    assert session.session_status == "ACTIVE"
    assert session.session_metadata == {"type": "test"}


def test_session_summary():
    # Test SessionSummary creation
    summary = SessionSummary(
        memory_id="test-memory",
        session_expiry_time=datetime(2024, 3, 20, 11, 30, 0, tzinfo=timezone.utc),
        session_id="test-session",
        session_start_time=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
        summary_text="Test summary",
    )

    assert summary.memory_id == "test-memory"
    assert summary.session_id == "test-session"
    assert summary.summary_text == "Test summary"


def test_memory_session():
    # Test MemorySession creation
    session = MemorySession(
        memory_id="test-memory",
        memory_arn="arn:aws:bedrock:us-east-1:123456789012:memory/test-memory",
        memory_name="Test Memory",
        created_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
    )

    assert session.memory_id == "test-memory"
    assert session.memory_name == "Test Memory"


def test_invocation():
    # Test Invocation creation
    invocation = Invocation(
        session_id="test-session",
        invocation_id="test-invocation",
        created_at="2024-03-20T10:30:00Z",
    )

    assert invocation.session_id == "test-session"
    assert invocation.invocation_id == "test-invocation"


def test_invocation_summary():
    # Test InvocationSummary creation
    summary = InvocationSummary(
        created_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
        invocation_id="test-invocation",
        session_id="test-session",
        status="COMPLETED",
    )

    assert summary.invocation_id == "test-invocation"
    assert summary.session_id == "test-session"
    assert summary.status == "COMPLETED"


def test_invocation_step():
    # Test InvocationStep creation
    payload = Payload(contentBlocks=[ContentBlock(text="Test")])
    step = InvocationStep(
        invocation_id="test-invocation",
        invocation_step_id="test-step",
        invocation_step_time="2024-03-20T10:30:00Z",
        payload=payload,
        session_id="test-session",
    )

    assert step.invocation_id == "test-invocation"
    assert step.invocation_step_id == "test-step"
    assert step.session_id == "test-session"


def test_invocation_step_summary():
    # Test InvocationStepSummary creation
    summary = InvocationStepSummary(
        invocation_step_id="test-step",
        session_id="test-session",
        invocation_id="test-invocation",
        status="COMPLETED",
        created_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
    )

    assert summary.invocation_step_id == "test-step"
    assert summary.session_id == "test-session"
    assert summary.status == "COMPLETED"


def test_action_group():
    # Test ActionGroup creation
    executor = ActionGroupExecutor(custom_control="RETURN_CONTROL", lambda_="test-lambda")
    group = ActionGroup(
        action_group_id="test-group",
        action_group_name="Test Group",
        action_group_state="ENABLED",
        agent_id="test-agent",
        agent_version="1",
        created_at="2024-03-20T10:30:00Z",
        updated_at="2024-03-20T10:30:00Z",
        action_group_executor=executor,
    )

    assert group.action_group_id == "test-group"
    assert group.action_group_name == "Test Group"
    assert group.action_group_state == "ENABLED"
    assert group.action_group_executor == executor


def test_action_group_summary():
    # Test ActionGroupSummary creation
    summary = ActionGroupSummary(action_group_id="test-group", action_group_name="Test Group")

    assert summary.action_group_id == "test-group"
    assert summary.action_group_name == "Test Group"


def test_version_summary():
    # Test VersionSummary creation
    summary = VersionSummary(
        version_id="1",
        version_name="v1",
        created_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
    )

    assert summary.version_id == "1"
    assert summary.version_name == "v1"


def test_alias_summary():
    # Test AliasSummary creation
    summary = AliasSummary(
        alias_id="test",
        alias_name="Test Alias",
        created_at=datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
    )

    assert summary.alias_id == "test"
    assert summary.alias_name == "Test Alias"
