SPECIALIST_AGENTS = {

    "repository": """
        Repository discovery, access, and repository-level operations.

        Owns:
        - repository discovery and access
        - project structure and repository metadata
        - source-code retrieval
        - dependencies and configuration discovery
        - CI/CD, deployment manifests, and IaC discovery
        - repository-level documentation
        - repository-level configuration and setup

        May create or modify repository-level files when that is
        the requested outcome.

        Examples:
        - inspect repository structure
        - check whether README.md exists
        - create or update README.md
        - inspect CI/CD configuration
        - inspect deployment manifests
        - prepare repository context for downstream agents
    """,

    "architecture": """
        Architecture and system-design analysis.

        Owns:
        - component architecture
        - system design
        - data flows
        - trust boundaries
        - integrations
        - scalability
        - reliability
        - architecture-level risks
    """,

    "security": """
        Security analysis.

        Owns:
        - threat modeling
        - SAST
        - SCA/dependency analysis
        - secret detection
        - configuration security
        - vulnerability identification
        - security risk assessment
    """,

    "performance": """
        Performance analysis.

        Owns:
        - CPU bottlenecks
        - memory bottlenecks
        - I/O bottlenecks
        - database bottlenecks
        - network bottlenecks
        - concurrency bottlenecks
        - performance analysis and recommendations
    """,

    "code_engineering": """
        Code implementation and remediation.

        Owns:
        - application/source-code changes
        - bug fixes
        - concrete remediation
        - dependency upgrades
        - secure code changes
        - implementation of validated findings
        - code changes required to satisfy the user's request
        - producing testable code or PRs

        Do not select this specialist merely because a repository file
        must be created, modified, committed, or pushed.

        Repository-level documentation, setup, or configuration belongs
        to the repository specialist when that is the requested outcome.
    """,

    "code_review": """
        Code review and code-quality analysis.

        Owns:
        - correctness review
        - maintainability review
        - code quality
        - engineering best practices
        - security-sensitive logic review

    """,

    "testing": """
        Testing and validation.

        Owns:
        - unit testing
        - integration testing
        - regression testing
        - dynamic testing
        - security testing
        - validation of implemented changes

    """,

    "Jira": """
        Engineering workflow and Jira management.

        Owns:
        - creating Jira issues
        - updating Jira issues
        - managing engineering workflow based on validated findings
          and explicitly requested remediation work

    """,

    "optimization": """
        Code and system optimization.

       Owns:
        - algorithm optimization
        - query optimization
        - resource utilization improvements
        - implementation efficiency
        - system efficiency improvements
        - performance-oriented optimization
        """,

    "refactoring": """
        Structural code refactoring.

        Owns:
        - improving modularity
        - improving readability
        - improving maintainability
        - restructuring code
        - reducing unnecessary complexity

      Primary goal is structural improvement while preserving intended behavior.
    """
}