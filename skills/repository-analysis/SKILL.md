---
name: repository-analysis
description: Use this skill when a task requires inspecting, inventorying, or analyzing a software repository.
---

SKILL TEST:
When this skill is loaded, you MUST mention:
"I am using the repository-analysis skill."

# repository-analysis

## Overview

This skill provides instructions for efficiently inspecting software repositories and
collecting the relevant evidence needed to answer repository-related tasks.

## Instructions

### 1. Access the repository

When the task requires repository access:

1. Use the repository URL provided in the messages.
2. Clone the repository into the sandbox under `/workspace/` 
3. Verify that the repository was cloned successfully.
4. Work with the repository through the sandbox/backend filesystem.

### 2. Inspect the repository structure

Before inspecting individual files:

1. Inspect the top-level directory.
2. Build a lightweight file-level inventory.
3. Exclude `.git` and generated/vendor directories unless the task explicitly requires them.
4. Identify files and directories relevant to the assigned task.

### 3. Identify relevant artifacts

Depending on the task, relevant artifacts may include:

- Source code
- Package/dependency manifests
- Lock files
- Build configuration
- Test configuration
- CI/CD configuration
- Docker/container files
- Deployment manifests
- Infrastructure/IaC files
- Runtime configuration
- Environment configuration
- Documentation
- Security configuration

Do not assume that a particular file exists.

For example, dependency information may be represented by different files depending on
the technology used by the repository.

If the required artifact cannot be found after reasonable targeted inspection, report it
as missing rather than repeatedly searching.

### 4. Inspect files selectively

1. Read only files necessary for the assigned task.
2. Prefer filenames, paths, metadata, and concise relevant excerpts over full file contents.
3. Do not read every source file.
4. Do not recursively read the entire repository.
5. Do not read a file again if it has already been inspected and contains sufficient information.
6. Do not repeat the same filesystem search unless new information provides a specific reason.

### 5. Handle large amounts of data

When repository inspection produces a large amount of data:

1. Save raw or intermediate data to the backend filesystem when useful.
2. Process and analyze the stored data.
3. Return only the information necessary for the main agent to continue the task.
4. Do not return raw data, intermediate search results, or detailed tool outputs unless explicitly requested.

### 6. Stop when sufficient evidence is obtained

Once the requested information has been sufficiently established:

1. Stop filesystem exploration.
2. Do not continue exploring merely to increase confidence.
3. Produce the requested result based on the evidence collected.

### 7. Respect task boundaries

Do not inspect or analyze the following unless explicitly required:

- Git history
- `.git` internals
- Generated files
- Caches
- Virtual environments
- Dependencies/vendor directories
- Binaries

Do not perform security, architecture, code-quality, or dependency analysis unless that
analysis is explicitly part of the assigned task.


  