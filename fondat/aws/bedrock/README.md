# AWS Bedrock Module

A high-level, resource-oriented wrapper around Amazon Bedrock control-plane (`bedrock-agent`) and runtime (`bedrock-agent-runtime`) APIs, providing a Pythonic interface to interact with Amazon Bedrock services.

## Features

- Resource-oriented API design
- Support for Agents, Prompts, and Flows
- Type-safe, idempotent operations
- Built-in caching mechanism
- VCR-backed test suite for reproducibility
- Async-first design

## Prerequisites

- AWS CLI v2 installed and configured  
- AWS SSO or equivalent IAM-based access  
- IAM role with `AmazonBedrockFullAccess` and proper trust policy  
- Python 3.11.5  
- Poetry for dependency management  

## Environment Setup

### 1. Create IAM Execution Role

1. Open **IAM → Roles → Create role**  
2. Select **AWS service** → **Lambda** or **Bedrock (if available)**  
3. Attach the `AmazonBedrockFullAccess` managed policy  
4. Create the role and note its ARN (used by your Bedrock agent, flow, etc.)

### 2. Log in with AWS SSO and set your profile

```bash
aws sso login --profile <YOUR_PROFILE>
export AWS_PROFILE=<YOUR_PROFILE>
```

### 3. Create Required Bedrock Resources

You’ll need to create the following resources manually via AWS Console:

- **Agent:**  
  - Console → Bedrock → Agents → Create agent  
  - Use existing role (from step 1)  
  - Copy Agent ARN → `TEST_AGENT_ID`

- **Flow:**  
  - Console → Bedrock → Flows → Create flow  
  - Use existing role  
  - Copy Flow ARN → `TEST_FLOW_ID`

- **Prompt:**  
  - Console → Bedrock → Prompts → Create prompt  
  - Create at least one version  
  - Copy Prompt ARN → `TEST_PROMPT_ID`

- **Agent Alias:**  
  - Console → Bedrock → Agents → Select agent → Aliases → Create alias  
  - Copy Alias ARN → `TEST_AGENT_ALIAS_ID`

- **Action Group:**  
  - Console → Bedrock → Agents → Select agent → Action groups → Create  
  - Copy Action Group ARN → `TEST_ACTION_GROUP_ID`


### 4. Create `.env` file

```env
AWS_PROFILE=your-profile-name
TEST_AGENT_ID=...
TEST_FLOW_ID=...
TEST_PROMPT_ID=...
TEST_AGENT_ALIAS_ID=...
TEST_ACTION_GROUP_ID=...
```

### 5. Install dependencies

```bash
poetry install
```

## Resource Graph

### Agents Resource

```
AgentsResource
├── .get()
└── [agent_id] → AgentResource
    ├── .get()
    ├── .invoke()
    ├── versions → VersionsResource
    ├── aliases → AliasesResource
    ├── action_groups → ActionGroupsResource
    ├── collaborators → CollaboratorsResource
    ├── memory → MemoryResource
    └── sessions → SessionsResource
```

### Prompts Resource

```
PromptsResource
├── .get()
└── [id] → PromptResource
    └── .get()
```

### Flows Resource

```
FlowsResource
├── .get()
└── [id] → FlowResource
    ├── .get()
    ├── .invoke()
    ├── versions → VersionsResource
    └── aliases → AliasesResource
```

## Usage

### Initialization

```python
from fondat.aws.bedrock import agents_resource, prompts_resource, flows_resource
from fondat.aws.client import Config

config = Config(region_name="us-west-2")

agents = agents_resource(config_agent=config, config_runtime=config)
prompts = prompts_resource(config_agent=config)
flows = flows_resource(config_agent=config, config_runtime=config)
```

### Using Agents

```python
agents_page = await agents.get(max_results=5)
agent = await agents[agent_id].get()
versions = await agents[agent_id].versions.get()
aliases = await agents[agent_id].aliases.get()
action_groups = await agents[agent_id].action_groups.get(agentVersion="DRAFT")
collaborators = await agents[agent_id].collaborators.get(agentVersion="DRAFT")
```

### Sessions and Invocations

```python
session = await agents[agent_id].sessions.create()

try:
    invocation = await agents[agent_id].sessions[session.session_id].invocations.create()
    steps = await agents[agent_id].sessions[session.session_id].invocations[invocation.invocation_id].get_steps()
finally:
    await agents[agent_id].sessions[session.session_id].delete()
```

### Flows

```python
flows_page = await flows.get()
flow = flows_page.items[0]
aliases = await flows[flow.flow_id].aliases.get()
alias_id = aliases.items[0].alias_id
session = await agents[agent_id].sessions.create()

try:
    response = await flows[flow.flow_id].invoke(
        input_content="Hello world!",
        flowAliasIdentifier=alias_id,
        nodeName="FlowInputNode",
        nodeOutputName="document"
    )
finally:
    await agents[agent_id].sessions[session.session_id].delete()
```

### Prompts

```python
prompts_page = await prompts.get()
prompt = await prompts[prompt_id].get()
```

## Testing

### Run All Tests

```bash
AWS_PROFILE=<YOUR_PROFILE> poetry run coverage run -m pytest tests/bedrock/
poetry run coverage report -m
```

### Run Unit Tests

```bash
AWS_PROFILE=<YOUR_PROFILE> poetry run coverage run -m pytest tests/bedrock/unit/
```

### Run Integration Tests

```bash
AWS_PROFILE=<YOUR_PROFILE> poetry run coverage run -m pytest tests/bedrock/integration/
```

> First run will save VCR cassettes in:
> - `tests/bedrock/unit/cassettes/bedrock/`
> - `tests/bedrock/integration/cassettes/bedrock/`

## Configuration

- `config_agent`: Control-plane config
- `config_runtime`: Runtime config
- `cache_size`: Max cached objects (default: 100)
- `cache_expire`: TTL in seconds (default: 300)

## Dependencies

- Python 3.11+
- fondat-core
- botocore
- aiobotocore
- boto3
- poetry
- pytest
- vcrpy
