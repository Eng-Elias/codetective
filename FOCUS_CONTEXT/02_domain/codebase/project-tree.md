# Project Tree

```
codetective/
├── FOCUS_CONTEXT
│   ├── 01_system
│   │   └── assistant-personna.md
│   ├── 02_domain
│   │   ├── architecture
│   │   │   ├── data-models.md
│   │   │   └── system-architecture.md
│   │   ├── codebase
│   │   │   ├── dependency-graph.md
│   │   │   └── project-tree.md
│   │   ├── project-overview.md
│   │   └── standards
│   │       └── coding-standards.md
│   ├── 03_tasks
│   │   ├── acceptance-criteria
│   │   │   └── multi-agent-workflow.md
│   │   ├── current-objectives.md
│   │   └── feature-specs
│   │       ├── cli-interface.md
│   │       ├── gui-interface.md
│   │       ├── mcp-interface.md
│   │       └── multi-agent-architecture.md
│   ├── 04_sessions
│   │   └── context-cache
│   └── 05_outputs
├── codetective-core
│   ├── Dockerfile
│   ├── README.md
│   ├── pyproject.toml
│   └── src
│       └── codetective
│           ├── __init__.py
│           ├── agents
│           │   ├── __init__.py
│           │   ├── ai_review_agent.py
│           │   ├── base.py
│           │   ├── output_comment_agent.py
│           │   ├── output_update_agent.py
│           │   ├── semgrep_agent.py
│           │   └── trivy_agent.py
│           ├── interfaces
│           │   ├── __init__.py
│           │   ├── cli.py
│           │   └── gui.py
│           ├── main.py
│           ├── models
│           │   ├── __init__.py
│           │   ├── agent_result.py
│           │   ├── agent_results.py
│           │   ├── configuration.py
│           │   ├── interface_models.py
│           │   └── workflow_state.py
│           ├── utils
│           │   ├── __init__.py
│           │   ├── configuration_manager.py
│           │   ├── file_processor.py
│           │   ├── git_repository_manager.py
│           │   ├── logger.py
│           │   └── result_aggregator.py
│           └── workflow
│               ├── __init__.py
│               ├── graph_builder.py
│               └── orchestrator.py
└── codetective-launcher
    ├── README.md
    ├── codetective
    ├── pyproject.toml
    └── src
        └── codetective_launcher
            ├── __init__.py
            ├── docker_manager.py
            ├── main.py
            └── utils
                ├── __init__.py
                └── docker_api_client.py
```
