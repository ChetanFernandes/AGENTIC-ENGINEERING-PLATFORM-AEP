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

        May create or modify repository-level files when that is the requested outcome.

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
        Security analysis and vulnerability identification.

        Owns:
        - Threat modeling
        - Static application security testing (SAST)
        - Software composition and dependency vulnerability analysis (SCA)
        - Secret detection
        - Security configuration analysis
        - Vulnerability identification and severity assessment
        - Security risk assessment and remediation recommendations

        Primary goal:
        Identify security weaknesses, explain their impact, and
        recommend remediation.

        Does not own implementation of security fixes.
        Code remediation belongs to code_engineering when requested.
        Security testing and validation belong to testing when explicitly
        required by the user's request or workflow.
    """,


    
    "performance": """
        Performance analysis and bottleneck identification.

        Owns:
        - CPU, memory, and I/O bottleneck analysis
        - Database query and network latency analysis
        - Concurrency and throughput analysis
        - Identification of performance regressions
        - Performance measurements and profiling
        - Recommendations for improving latency, throughput,
        scalability, and resource utilization

        Primary goal:
        Diagnose performance problems and recommend improvements.
        Does not own implementation of optimization changes.
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
        - Correctness and logic review
        - Maintainability and readability assessment
        - Engineering best-practice compliance
        - Identification of code smells and potential defects
        - Review of implementation quality
        - Assessment of testability and error handling
        - General review of security-sensitive logic as part of
        broader code quality, when relevant

        Primary goal:
        Evaluate implementation quality and identify code-level
        issues without implementing fixes.

        Does not own dedicated vulnerability assessment, threat modeling,
        or comprehensive security analysis. Those belong to security.
        Does not implement remediation; that belongs to code_engineering
        when requested.
    """,


    "testing": """
        Testing and validation of software behavior and changes.

        Owns:
        - Unit testing
        - Integration testing
        - Regression testing
        - Dynamic testing
        - Security testing and validation
        - Validation of implemented changes
        - Verification that requested acceptance criteria are satisfied

        Primary goal:
        Execute or design the required tests and report the results.

        Does not replace security analysis when the user requests
        vulnerability discovery or security risk assessment.
        Do not select testing automatically for every implementation task.
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
        Performance and efficiency optimization.

        Owns:
        - Algorithm optimization
        - Database query optimization
        - Resource utilization improvements
        - Implementation efficiency improvements
        - Latency and throughput optimization
        - System efficiency improvements

        Primary goal:
        Implement or direct concrete changes that improve performance
        or efficiency when optimization work is requested.

        Does not own general performance diagnosis when the user
        only requests analysis and recommendations.
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
    """,

    
    "general": """
        General-purpose assistance and fallback routing.

        Owns:
        - Answering general informational questions
        - Explaining concepts and terminology
        - General reasoning and brainstorming
        - Summarizing user-provided information
        - Helping with requests that do not require a
        domain-specific specialist
        - Handling general conversational requests

        Primary goal:
        Fulfill requests that do not require a specialized
        engineering or workflow capability.

        Do not use this agent as a substitute for an available
        specialist when the user's request clearly requires that
        specialist's capabilities.

        Do not use this agent to bypass required specialist
        workflows, repository operations, security analysis,
        implementation, testing, or Jira operations.
    """
    ,

}