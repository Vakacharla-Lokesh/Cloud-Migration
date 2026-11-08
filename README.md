# AWS Migration Agent

An AI-assisted workflow for turning an AWS migration request into region-aware Terraform infrastructure. The agent uses LangGraph to coordinate intent parsing, AWS resource discovery, dependency mapping, infrastructure-as-code generation, and a human approval gate before the deployment phase.

## What this project does

The current implementation is focused on Phase 1: infrastructure-as-code generation.

Given a request such as:

> Migrate resources tagged `app` from `ap-south-1` to `us-east-1` using Terraform.

the workflow:

1. Parses the request into a validated migration model.
2. Discovers matching AWS resources through AWS MCP tools.
3. Maps resource relationships and calculates a safe dependency order.
4. Generates Terraform for each resource.
5. Pauses for human approval or feedback.
6. Passes approved work to the deployment placeholder for future Phase 2 implementation.

The generator uses Jinja2 templates for supported resource types and an LLM fallback for resource types without a dedicated template. Generated files are written to `sessions/<session_id>.tf`.

## Architecture

```text
User request
    |
    v
Intent parser
    |
    v
AWS resource discovery
    |
    v
Dependency mapper
    |
    v
Terraform IaC generator
    |
    v
Human approval gate
    |
    v
Deployment stub
```

The workflow is implemented as a compiled LangGraph state graph. Shared migration state is represented with a typed state model, and graph checkpoints allow the human-in-the-loop step to pause and resume across requests.

## Implemented capabilities

- Structured migration intent parsing with Pydantic validation.
- Tag-based AWS resource discovery through MCP integrations.
- Dependency graph construction and topological ordering.
- Terraform provider configuration for source and target regions.
- Dedicated Terraform templates for:
  - `AWS::S3::Bucket`
  - `AWS::CloudFront::Distribution`
- LLM-generated Terraform fallback for unknown resource types.
- Migration metadata tags, including the source region and migration tool.
- Human approval and rejection flow with feedback support.
- In-memory graph checkpointing for local or single-process usage.
- Configurable Google Gemini model through `backend/app/llm.py`.

## Repository layout

```text
cloud-migration/
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   └── app/
│       ├── agents/          # Workflow nodes
│       ├── graph/           # State, routing, and graph assembly
│       ├── schemas/         # Pydantic migration models
│       ├── templates/       # Terraform Jinja2 templates
│       ├── tools/           # AWS MCP client integration
│       └── llm.py           # LLM configuration
├── frontend/                # Reserved for the future UI
├── FILE_STRUCTURE.md        # Detailed extension guide
└── README.md
```

## Prerequisites

- Python 3.10 or later
- AWS credentials with permission to inspect the resources being migrated
- Google Application Default Credentials for Gemini
- `uvx` for launching the AWS MCP servers

The exact permissions depend on the AWS MCP servers and resource types used. Use least-privilege IAM policies in real environments.

## Setup

From the project root:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Install the AWS MCP servers used by the project as needed:

```powershell
uvx awslabs.core-mcp-server@latest
uvx awslabs.aws-documentation-mcp-server@latest
```

Copy the environment template and update the values for your environment:

```powershell
Copy-Item .env.example .env
```

Do not commit `.env` or any credential files.

## Configuration

### Google Gemini

The default model is `gemini-2.5-flash-lite`, configured in [`backend/app/llm.py`](backend/app/llm.py). Authenticate with Google Application Default Credentials:

```powershell
gcloud auth application-default login
```

Set `GOOGLE_CLOUD_PROJECT` in `backend/.env` when your ADC setup requires an explicit project.

### AWS

The AWS MCP client supports the standard AWS credential chain, including IAM roles and named profiles. Typical local settings are:

```dotenv
AWS_PROFILE=default
AWS_DEFAULT_REGION=ap-south-1
```

Prefer IAM roles or named profiles over storing access keys in local files.

## Running the graph

The graph can be invoked directly from Python:

```python
import asyncio

from app.graph.builder import migration_graph


async def main() -> None:
    session_id = "test-session-001"
    result = await migration_graph.ainvoke(
        {
            "user_prompt": (
                "Migrate all resources tagged app=n8n-csp-host "
                "from ap-south-1 to us-east-1 using Terraform"
            ),
            "session_id": session_id,
        },
        config={"configurable": {"thread_id": session_id}},
    )
    print(result.get("iac_file_path"))


asyncio.run(main())
```

Run this from the `backend` directory so that the `app` package is importable:

```powershell
python run_migration.py
```

The project currently provides the graph components rather than a checked-in `run_migration.py` entrypoint or production API server. The example above can be placed in a local script for experimentation.

## Human approval flow

After IaC generation, the graph can pause at the human approval gate. Resume an approved migration with:

```python
from langgraph.types import Command

await migration_graph.ainvoke(
    Command(resume={"decision": "approve", "feedback": ""}),
    config={"configurable": {"thread_id": "test-session-001"}},
)
```

To reject the generated plan and provide feedback:

```python
await migration_graph.ainvoke(
    Command(
        resume={
            "decision": "reject",
            "feedback": "Add server-side encryption to the S3 bucket",
        }
    ),
    config={"configurable": {"thread_id": "test-session-001"}},
)
```

## Adding support

### Add a Terraform resource template

1. Add a Jinja2 template under `backend/app/templates/terraform/`.
2. Add the AWS resource type and template filename to `TERRAFORM_TEMPLATE_MAP` in `backend/app/agents/iac_generator.py`.
3. Reuse the existing resource and migration models when adding template inputs.

### Add an agent

1. Create `backend/app/agents/<name>.py` with a LangGraph node function.
2. Import it in `backend/app/graph/builder.py`.
3. Register the node and connect its routing edges.
4. Update the shared state model when the node introduces new state.

See [`FILE_STRUCTURE.md`](FILE_STRUCTURE.md) for the detailed extension guide.

## Current status and limitations

- Phase 1 generates Terraform; it does not execute Terraform or perform a live migration.
- `deployment_stub.py` is a placeholder for the future deployment, validation, and cleanup phases.
- The `frontend/` directory is reserved for a future user interface.
- The default checkpointer is in-memory and is not suitable for multi-worker production deployments. Replace it with a persistent checkpointer such as SQLite or Redis for production use.
- Generated IaC must be reviewed and tested before it is applied to an AWS account.

## License

No license has been specified yet.
