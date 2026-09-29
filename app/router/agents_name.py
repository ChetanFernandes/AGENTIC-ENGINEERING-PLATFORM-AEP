SPECIALIST_AGENTS = {
    "repository": 
    """
        Repository discovery and access.
        Retrieves source code, project structure, dependencies,
        configuration, CI/CD, deployment manifests, IaC and
        prepares the environment required for downstream analysis.
    """,

    "architecture": 
    """
        Architecture and system-design analysis.
        Reviews components, data flows, trust boundaries,
        integrations, scalability, reliability and design-level risks.
    """,

    "security": 
    """
        Security analysis.
        Performs threat modeling, SAST, SCA/dependency analysis,
        secret detection, configuration security and vulnerability assessment.
    """,

    "performance": 
    """
        Performance analysis.
        Identifies CPU, memory, I/O, database, network and
        concurrency bottlenecks and recommends performance improvements.
    """,

    "code_engineering": """
        Code remediation and implementation.
        Implements concrete fixes, patches, dependency upgrades,
        secure code changes and produces testable code/PRs.
    """,

    "code_review": """
        Manual code review.
        Examines code quality, correctness, maintainability,
        security-sensitive logic and engineering best practices.
    """,

    "testing": """
        Testing and validation.
        Executes appropriate automated, integration, regression,
        dynamic, security or other tests required by the task.
    """,

    "Jira": """
        Engineering workflow and Jira management.
        Creates Jira issues based on
        validated findings and remediation work.
    """,

    "optimization": """
        Code/system optimization.
        Identifies opportunities to improve efficiency,
        resource utilization, algorithms, queries and implementation.
    """,

    "refactoring": """
        Refactoring.
        Proposes or implements structural improvements that
        improve maintainability, modularity, readability and code quality
        without changing intended behavior.
    """
}