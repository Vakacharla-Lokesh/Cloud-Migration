# AWS Migration Agent — File Structure

> Reference for Phase 1 (IaC generation). Phase 2 files (deployment, validation, cleanup) slot in without changing this scaffold.

```
awsmigrate/
│
├── FILE_STRUCTURE.md              ← you are here
│
├── sessions/                      ← auto-created at runtime
│   └── <session_id>.tf            ← generated Terraform output per run
│
├── frontend/                      ← React UI (Phase 1 scaffold — TBD)
│
└── backend/
    ├── .env.example               ← copy to .env, fill in credentials
    ├── requirements.txt           ← pip install -r requirements.txt
    │
    └── app/
        │
        ├── __init__.py
        │
        ├── llm.py                 ★ CONFIGURE THIS — returns the LLM instance
        │                            swap model string here to change provider
        │
        ├── schemas/
        │   ├── __init__.py
        │   └── migration.py       ← Pydantic models: MigrationRequest, AWSResource
        │
        ├── graph/
        │   ├── __init__.py
        │   ├── state.py           ← MigrationGraphState TypedDict (shared state)
        │   ├── edges.py           ← conditional routing functions
        │   └── builder.py         ★ ENTRY POINT — builds + compiles the graph
        │                            import migration_graph from here
        │
        ├── agents/                ← one file per agent node
        │   ├── __init__.py
        │   ├── intent_parser.py   ← Agent 1: parse prompt → MigrationRequest
        │   ├── resource_discovery.py  ← Agent 2: AWS MCP tag lookup → AWSResource list
        │   ├── dependency_mapper.py   ← Agent 3: build DAG + topo sort
        │   ├── iac_generator.py   ← Agent 4: render Jinja2 → write <session_id>.tf
        │   ├── hitl_gate.py       ← Agent 5: interrupt() pause → approve/reject
        │   └── deployment_stub.py ← Phase 2 placeholder (swap out later)
        │
        ├── tools/
        │   ├── __init__.py
        │   └── aws_mcp_client.py  ← loads AWS MCP tools via langchain-mcp-adapters
        │                            SigV4 auth via botocore, certifi CA bundle
        │
        ├── templates/
        │   └── terraform/
        │       ├── provider.tf.j2     ← AWS provider + source alias block
        │       ├── s3.tf.j2           ← S3 bucket + versioning + public access block
        │       ├── cloudfront.tf.j2   ← CloudFront distribution + OAC
        │       └── generic.tf.j2      ← fallback wrapper for LLM-generated blocks
        │
        └── utils/
            └── __init__.py            ← add ARN parser, region validator here later
```

---

## Adding a New Agent

1. Create `backend/app/agents/<name>.py` with a function `run_<name>(state: MigrationGraphState) -> dict`
2. Import it in `graph/builder.py`
3. Add `builder.add_node("<name>", run_<name>)` in `build_graph()`
4. Wire edges with `builder.add_edge(...)` or `builder.add_conditional_edges(...)`

## Adding a New Terraform Resource Template

1. Create `backend/app/templates/terraform/<resource>.tf.j2`
2. Add an entry to `TERRAFORM_TEMPLATE_MAP` in `agents/iac_generator.py`:
   ```python
   "AWS::EC2::Instance": "ec2.tf.j2",
   ```
   The generator picks it up automatically — no other changes needed.

## Adding a New AWS MCP Server

1. Add an entry to `AWS_MCP_SERVERS` in `tools/aws_mcp_client.py`:
   ```python
   "awslabs-cost-explorer": {
       "transport": "stdio",
       "command": "uvx",
       "args": ["awslabs.cost-explorer-mcp-server@latest"],
       "env": {"FASTMCP_LOG_LEVEL": "ERROR"},
   },
   ```
   The tools are automatically available to all agents that call `get_aws_tools()`.

## Running the Graph (without FastAPI)

```python
import asyncio
from app.graph.builder import migration_graph

async def main():
    config = {"configurable": {"thread_id": "test-session-001"}}
    result = await migration_graph.ainvoke(
        {
            "user_prompt": "Migrate all resources tagged app=n8n-csp-host from ap-south-1 to us-east-1 using terraform",
            "session_id": "test-session-001",
        },
        config=config,
    )
    print(result["iac_file_path"])

asyncio.run(main())
```

## HITL Resume (after interrupt)

```python
from langgraph.types import Command

# Resume with approval
await migration_graph.ainvoke(
    Command(resume={"decision": "approve", "feedback": ""}),
    config={"configurable": {"thread_id": "test-session-001"}},
)

# Resume with rejection + feedback
await migration_graph.ainvoke(
    Command(resume={"decision": "reject", "feedback": "Add server-side encryption to S3"}),
    config={"configurable": {"thread_id": "test-session-001"}},
)
```
