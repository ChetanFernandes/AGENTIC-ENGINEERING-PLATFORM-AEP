# ADR-001: AEP Router Architecture

**Project:** AEP — Agentic Engineering Platform  
**Decision:** Router-based multi-agent dispatch  
**Status:** Accepted  
**Date:** 2026-08-26  
**Scope:** Initial request classification and specialist-agent dispatch

---

# 1. Decision Summary

AEP will use a dedicated **Router** as the entry point for user requests.

The Router will:

1. Understand the user's request.
2. Identify the capabilities required to satisfy the request.
3. Select one or more specialized agents/workflows.
4. Decompose a broad request into targeted specialist tasks.
5. Identify dependencies between tasks.
6. Recommend whether independent tasks can execute in parallel.
7. Produce a structured `RouteDecision`.
8. Provide routing confidence and rationale for observability and evaluation.

The Router will NOT be responsible for:

- Performing the actual domain analysis.
- Modifying code.
- Running tests.
- Creating Jira tickets.
- Approving changes.
- Executing arbitrary code.
- Making security/policy decisions.
- Managing model infrastructure.

Those responsibilities belong to other AEP components.

---

# 2. Business Context

AEP is an enterprise-grade Agentic Engineering Platform intended to analyze software repositories and assist engineers with activities such as:

- Repository understanding
- Architecture analysis
- Code review
- Performance analysis
- Security analysis
- Code optimization
- Refactoring
- Test generation
- Test execution
- Verification
- Human approval
- Jira creation and workflow management

A single general-purpose agent should not be responsible for every engineering capability.

Different tasks require different:

- prompts
- tools
- context
- knowledge
- skills
- security policies
- execution environments
- evaluation criteria

Therefore AEP requires an intelligent dispatch mechanism.

---

# 3. Problem Statement

Without routing, the architecture could become:

User
  ↓
One Large Agent
  ↓
Many Tools
  ↓
Many Responsibilities

This creates several problems:

- Large and complex prompts
- Excessive context
- Higher token usage
- Higher latency
- Higher cost
- Increased tool-selection complexity
- Poor separation of responsibilities
- Increased risk of incorrect tool usage
- Difficult evaluation
- Difficult debugging
- Difficult scaling
- Difficult security enforcement

AEP therefore requires a dedicated routing layer.

---

# 4. Architectural Principle

The Router follows the principle:

> Route only to the capabilities required by the user's request.

The Router should not mechanically invoke every available agent.

For example:

### Request

"Analyze my repository for security and performance issues."

Required capabilities:

- Security
- Performance

The Router should not automatically invoke:

- Jira
- Forecasting
- RAG
- Testing
- Architecture

unless those capabilities are actually required.

This minimizes:

- unnecessary execution
- latency
- token usage
- cost
- noise

---

# 5. Router Responsibilities

The Router is responsible for:

## 5.1 Intent Understanding

Understand the user's overall objective.

Examples:

- Explain repository
- Review code
- Find security vulnerabilities
- Find performance bottlenecks
- Optimize code
- Generate tests
- Review architecture
- Create Jira ticket

---

## 5.2 Capability Identification

Determine which specialist capabilities are required.

Example:

User:

"Find security vulnerabilities and performance bottlenecks."

Router:

- Security
- Performance

---

## 5.3 Multi-Route Decisions

A request may require multiple specialists.

Example:

"Review this repository for security, performance and architecture issues."

Router:

- Security Agent
- Performance Agent
- Architecture Agent

---

## 5.4 Task Decomposition

The Router should create targeted tasks rather than sending the same broad user request to every agent.

Example:

### Security Agent

"Identify authentication weaknesses, injection vulnerabilities, exposed secrets and insecure dependencies."

### Performance Agent

"Identify computational, database, API and I/O performance bottlenecks."

### Architecture Agent

"Explain the repository architecture, components, dependencies and architectural weaknesses."

This improves context quality and reduces unnecessary information passed to each agent.

---

## 5.5 Dependency Identification

The Router may identify dependencies between tasks.

Example:

Performance Analysis
        ↓
Optimization Plan
        ↓
Code Change
        ↓
Testing
        ↓
Verification

The later task depends on the earlier task.

In contrast:

Security Analysis
Performance Analysis
Architecture Analysis

may be independent and can execute concurrently.

---

## 5.6 Execution Recommendation

The Router may recommend:

- `parallel`
- `sequential`

However, the Router does not directly execute the workflow.

The execution/orchestration layer is responsible for enforcing the workflow.

---

## 5.7 Confidence

The Router should provide a routing confidence value.

Example:

```text
confidence = 0.94

Important:

LLM-generated confidence is NOT automatically treated as a reliable probability.It must be evaluated against actual routing accuracy.

Confidence may later be used for:

    evaluation
    fallback
    clarification
    additional validation
    human review
    observability

Important:

LLM-generated confidence is NOT automatically treated as a reliable probability.

It must be evaluated against actual routing accuracy.

---


## 5.8 Routing Rationale

The Router should provide a concise reason for its decision.

Example:

"The request explicitly requires independent security and performance analysis."

This supports:

debugging
observability
evaluation
trace analysis
human review

6. RouteDecision Contract

The Router will produce a structured RouteDecision.

Conceptually:

RouteDecision
│
├── routes[]
│   ├── agent
│   ├── task
│   ├── priority
│   └── dependencies[]
│
├── execution_mode
├── confidence
└── routing_reason

7. Route Object

        Each route contains:

        1. agent

        Identifies the specialist responsible for the task.

        Initial planned specialist types include:

        repository
        architecture
        security
        performance
        code_engineering
        code_review
        testing
        knowledge/RAG
        Jira/workflow

        The exact agent registry will evolve as AEP is implemented.

        The Router should not be allowed to invent arbitrary agent identifiers.

        Agent identifiers should eventually be validated against an approved agent registry.

        This validation will form part of the platform's guardrail strategy.

        2. task

        A focused task description for the specialist.

        Example:

        Identify SQL injection, authentication,
        authorization, secret exposure and
        dependency vulnerabilities.

        3. priority
        Priority is used by the orchestrator/scheduler to order or select among routes that are currently eligible to execute. It does not override dependencies.

        Represents execution priority, NOT business severity.

        Example:

        1 = highest
        2 = medium
        3 = lower

        Security finding severity is a separate concept and should not be confused with routing priority.

        4. dependencies

        Identifies tasks that must complete before another task can execute.

        Example:

        optimization_plan
        depends_on:
        performance_analysis

        Independent tasks have:

        dependencies: []


8. Execution Mode

The initial execution modes are:

parallel
sequential

1. Parallel

Used when tasks are independent.

Example:

                Router
                  │
       ┌──────────┼──────────┐
       ↓          ↓          ↓
   Security   Performance Architecture
       │          │          │
       └──────────┼──────────┘
                  ↓
              Synthesis
2. Sequential

Used when later work depends on earlier work.

Example:

Analyze
   ↓
Plan
   ↓
Act
   ↓
Test
   ↓
Verify

The Router provides routing/execution metadata, but LangGraph is responsible for actual workflow orchestration.

9. Example RouteDecision

For:

"Review my Python FastAPI repository. Find security vulnerabilities and performance bottlenecks, explain the architecture, and recommend which issues I should fix first."

Conceptual output:

{
  "routes": [
    {
      "agent": "security",
      "task": "Identify security vulnerabilities including authentication, authorization, injection, secret exposure and dependency risks.",
      "priority": 1,
      "dependencies": []
    },
    {
      "agent": "performance",
      "task": "Identify API, database, I/O and computational performance bottlenecks.",
      "priority": 1,
      "dependencies": []
    },
    {
      "agent": "architecture",
      "task": "Explain the repository architecture, components, dependencies and architectural weaknesses.",
      "priority": 2,
      "dependencies": []
    }
  ],
  "execution_mode": "parallel",
  "confidence": 0.94,
  "routing_reason": "The request contains independent security, performance and architecture analysis requirements."
}

10. Router vs Supervisor

A critical architectural distinction:

1. Router

Answers:

"Which capability/capabilities should handle this request?"

Typical flow:

User
 ↓
Router
 ↓
Specialist Agent(s)


2. Supervisor

Answers:

"What should happen next as the task evolves?"

Typical flow:

User
 ↓
Supervisor
 ↓
Agent A
 ↓
Analyze result
 ↓
Agent B
 ↓
Analyze result
 ↓
Agent C
 ↓
Final result

A Router is primarily a dispatch/classification mechanism.

A Supervisor is an orchestration agent capable of dynamically deciding subsequent actions.

AEP may use both patterns where appropriate.

11. Router vs Single General-Purpose Agent

    Alternative A — One large agent
    User
    ↓
    General Agent
    ↓
    All tools

Rejected as the primary architecture because it creates:

excessive tool surface
large context
complex prompts
higher cost
higher latency
poor separation of concerns
difficult evaluation
increased security complexity
Decision

Use specialized capabilities behind a Router.

12. Router vs Hard-Coded Rules

A simple implementation could use:

if "security" in query:
    route = "security"

This is useful for deterministic cases but is insufficient as the primary routing mechanism.

Natural language requests may express intent without explicit keywords.

Example:

"Can you check whether this authentication implementation can be exploited?"

The word "security" may not appear.

Therefore AEP will evaluate LLM-based structured routing.

A hybrid approach may eventually be used:

Request
   ↓
Deterministic checks
   ↓
Obvious?
 ┌─┴─┐
Yes  No
 ↓    ↓
Route LLM Router

This can improve:

latency
cost
determinism

The hybrid approach will be evaluated during implementation rather than assumed to be optimal.

13. Structured Output

The Router will use structured output rather than relying on free-form LLM responses.

Bad:

"I think this is mainly a security issue..."

Preferred:

{
  "routes": [
    {
      "agent": "security",
      "task": "...",
      "priority": 1,
      "dependencies": []
    }
  ],
  "execution_mode": "parallel",
  "confidence": 0.94,
  "routing_reason": "..."
}

The implementation will use:

Pydantic schemas
LangChain structured output
validation

This creates a stable contract between the LLM and the orchestration layer.

14. Router and LangGraph

The Router will eventually integrate with LangGraph.

Relevant LangGraph concepts include:

State
Typed state
Nodes
Edges
Conditional routing
Command
Send
Parallel execution
Reducers
Dependency-aware execution
Graph execution

Conceptually:

Router
   ↓
RouteDecision
   ↓
LangGraph State
   ↓
Conditional routing
   ↓
Specialist nodes

For parallel fan-out, LangGraph mechanisms such as Send will be evaluated.

For single/directed routing, mechanisms such as Command may be appropriate.

15. Context Engineering

    The Router should transform broad user requests into focused specialist tasks.

    Instead of:

    Same giant prompt
            ↓
    Security
    Performance
    Architecture

    Use:

    Broad request
        ↓
    Router
        ↓
    Focused task
    ┌───┼────┐
    ↓   ↓    ↓
    Sec Perf Arch

    Each specialist should receive only the context required for its responsibility wherever practical.

    This reduces:

    context size
    token consumption
    irrelevant information
    cognitive complexity
    potential data exposure

    Context engineering will be expanded as the agent architecture evolves.

16. Risk and Security Separation

The Router will NOT make final security or policy decisions.

Risk assessment and policy enforcement will be handled by a separate Risk/Policy/Guardrail layer.

Architecture:

User
 ↓
Router
 ↓
RouteDecision
 ↓
Risk / Policy / Guardrails
 ↓
LangGraph Execution

Reason:

The Router's responsibility is routing.

Security policy is a separate cross-cutting concern.

This separation allows security policies to be applied consistently regardless of which agent is selected.

17. Guardrails

Guardrails are not implemented inside the Router itself.

They will eventually cover areas such as:

allowed agents
allowed tools
input validation
output validation
prompt injection defense
authorization
sensitive-data handling
tool permissions
high-risk action detection
policy enforcement

Example:

Router
 ↓
RouteDecision
 ↓
Guardrails
 ↓
Approved?
 ├── No → Block / Escalate
 └── Yes
       ↓
    Execute

Guardrails will be implemented at the appropriate platform milestone.

18. AI Sandbox

The Router does not execute code.

AEP will use an isolated AI Sandbox before AI-generated or AI-modified code is executed.

Conceptual flow:

Code Agent
    ↓
Generated Code
    ↓
AI Sandbox
    ↓
Tests / Execution
    ↓
Results
    ↓
Verification

The sandbox will eventually address:

filesystem isolation
process isolation
CPU limits
memory limits
execution timeouts
network restrictions
dependency controls
secrets isolation
malicious code
sandbox lifecycle

This is a critical security boundary for AEP because agents may generate or modify executable code.

19. AI Harness

AEP will eventually include an Agent Harness/runtime layer around agent execution.

The harness is responsible for controlling agent execution rather than performing the domain work itself.

Potential responsibilities include:

planning
context management
tool execution
retries
state management
execution limits
observability hooks
safety policies
evaluation hooks
long-running execution
subagent management

The relationship is:

Agent
  ↓
AI Harness
  ↓
Tools / Models / State / Sandbox

The Deep Agents architecture and documentation will be studied as part of this milestone.

20. LLM Gateway

The Router should not be tightly coupled to a single model provider.

AEP will eventually introduce an LLM Gateway abstraction.

Conceptually:

AEP
 ↓
LLM Gateway
 ├── Model A
 ├── Model B
 ├── Model C
 └── Fallback Model

Potential gateway responsibilities:

model selection
provider abstraction
fallback
retry
rate limiting
token management
cost controls
model policies
logging
routing to appropriate model tiers
21. Scaling AI Models

Model selection should not assume that the most powerful model is required for every task.

Potential strategy:

Simple classification
    ↓
Fast / low-cost model

Complex architecture reasoning
    ↓
Powerful reasoning model

Specialized task
    ↓
Approved specialized model

Future production architecture may include:

load balancing
concurrency management
rate limiting
queues
worker pools
horizontal scaling
backpressure
model fallback
caching
cost optimization

Model scaling is a platform concern, not a Router responsibility.

22. Observability

Router decisions must eventually be observable.

We should capture:

user request
route selected
agents selected
tasks generated
execution mode
confidence
routing rationale
model used
latency
tokens
cost
errors
downstream agent results

LangSmith will eventually be evaluated for tracing and observability.

23. Router Evaluation

Routing quality must be measurable.

We will create an evaluation dataset containing:

User Request
Expected Route(s)
Expected Execution Mode
Expected Task Type

Example:

Request	Expected Route
Explain repository	repository
Find SQL injection	security
Improve API latency	performance
Review authentication	security
Explain architecture	architecture
Security + performance review	security + performance

Metrics may include:

routing accuracy
multi-route accuracy
false routing rate
unnecessary agent invocation
missed capability rate
latency
cost

LLM-generated confidence will be compared against actual routing performance rather than being treated as ground truth.

24. Failure Handling

Router failure scenarios include:

Unknown request
Router
 ↓
No valid route
 ↓
Clarification / fallback
Low-confidence route
Low confidence
 ↓
Additional validation
or
Human clarification
Invalid agent
Invalid agent
 ↓
Schema validation fails
 ↓
Reject / retry / fallback
Agent unavailable
Selected Agent
 ↓
Unavailable
 ↓
Fallback / retry / escalation

These mechanisms will be implemented progressively.

25. Human-in-the-Loop

The Router itself should not automatically request human approval for every request.

Human approval becomes important for high-risk actions such as:

modifying production-sensitive code
executing dangerous operations
creating/closing Jira issues based on consequential changes
deploying changes
handling sensitive credentials
executing actions with external impact

Conceptually:

Router
 ↓
Guardrails
 ↓
Agent
 ↓
Proposed Action
 ↓
Human Approval
 ↓
Sandbox / Execution

The exact approval points will be determined during workflow design.

26. Relationship With AEP Agent Workflow

The Router is only the beginning of the AEP workflow.

The target engineering workflow is:

Analyze
   ↓
Plan
   ↓
Act
   ↓
Test
   ↓
Verify
   ↓
Human Approval
   ↓
Jira

The Router determines which capabilities are required to enter and execute this workflow.

27. Relationship With Multi-Agent Patterns

AEP will explicitly study the following LangChain multi-agent patterns:

Router
Subagents
Handoffs
Skills
Supervisor/orchestration

The Router is being implemented now.

Other patterns will be evaluated later based on where they naturally fit.

If a pattern does not provide meaningful value to AEP, we will:

Understand the concept theoretically.
Understand when it should and should not be used.
Document the trade-offs.
Create a minimal example or placeholder if appropriate.
Avoid forcing it into production architecture unnecessarily.
28. Alternatives Considered
Single General Agent

Rejected as the primary architecture because of excessive complexity and poor separation of responsibilities.

Hard-Coded Keyword Router

Useful as a deterministic optimization but insufficient as the primary routing strategy.

Supervisor-Only Architecture

Not selected as the initial routing mechanism because simple request dispatch does not require a full supervisory agent.

Supervisor/orchestration may be introduced later for long-running dynamic workflows.

Routing Every Request to Every Agent

Rejected because it increases:

latency
cost
token usage
noise
unnecessary tool access
security exposure
29. Trade-offs
Benefits
Separation of concerns
Specialized agents
Better context management
Parallel execution
Lower unnecessary model usage
Easier evaluation
Easier observability
Easier scaling
Better security boundaries
Easier maintenance
Better interview demonstration of multi-agent architecture
Costs
Additional orchestration complexity
Additional LLM calls
Routing errors
Need for evaluation
More components to observe
More complex state management
Potential latency from routing
30. Initial Implementation Scope

The first Router implementation will focus on:

Pydantic route schema
LangChain structured output
Basic route classification
Multiple route support
Targeted task generation
Dependency representation
Execution mode
Confidence
Routing rationale
Validation
Unit tests
Basic evaluation dataset

The Router will initially NOT implement:

full security guardrails
AI Sandbox
AI Harness
LLM Gateway
production-scale model routing
Jira workflow
human approval

Those will be introduced at their appropriate architectural milestones.

31. Future Evolution

The Router is expected to evolve from:

LLM
 ↓
Route

toward:

User Request
      ↓
Deterministic / Fast Path
      ↓
Router
      ↓
Structured RouteDecision
      ↓
Risk / Policy / Guardrails
      ↓
AI Harness
      ↓
LangGraph Orchestration
      ↓
Specialist Agents
      ↓
Tools / RAG / Sandbox
      ↓
Testing / Verification
      ↓
Human Approval
      ↓
Jira / External Actions

Supporting platform capabilities:

LLM Gateway
Model Routing
Model Scaling
Observability
Evaluation
Security
Cost Management
32. Decision

AEP will use a structured Router + specialized agents + LangGraph orchestration architecture.

The Router will:

Determine the minimum set of capabilities required for a request, generate focused tasks, identify dependencies, and provide structured routing metadata.

LangGraph will control execution.

Guardrails will control safety and policy.

AI Harness will control agent execution.

AI Sandbox will isolate code execution.

LLM Gateway will control model access.

Observability will provide operational visibility.

Evaluation will measure system quality.

Human approval will control high-risk actions.

This separation of responsibilities is the foundational architectural principle for AEP.

33. Status

Decision: Accepted

Implementation: Pending

Next implementation step:

Implement RouteDecision using Pydantic and LangChain Structured Output.

After implementation, validate the Router with unit tests and a routing evaluation dataset before proceeding to the Subagents milestone.





Phase 0.2 — Router
│
├── Concept/design              ✅
├── ADR-001                     ✅
│
├── Implementation
│   ├── 1. Project structure - Done
│   ├── 2. Route Pydantic model  - Done
│   ├── 3. RouteDecision model - Done
│   ├── 4. Validation - Done
│   ├── 5. LangChain Structured Output - Done
│   ├── 6. LLM Router 
│   ├── 7. LangGraph integration
│   ├── 8. Parallel routing
│   ├── 9. Tests
│   └── 10. Router evaluation
│
└── Router milestone review
        ↓
   Curriculum gap check
        ↓
   Only then → Subagents















