# Azure DevOps MCP — Setup & Agent Reference

This reference covers everything agents need to interact with Azure DevOps via the
local MCP server (`@azure-devops/mcp`). Read this file when setting up ADO integration
or when an agent asks "how do I push to ADO / create a work item / update the wiki".

---

## Setup (Orchestrator runs this once)

### Prerequisites
- Node.js 20+
- Azure CLI installed: `brew install azure-cli`
- Active Azure DevOps organization (must be backed by Microsoft Entra / AAD)
- Basic license or higher in ADO (free plan has tool permission limitations)

### Authentication
```bash
az login
# Follow browser prompt to authenticate with your Microsoft account
```

### MCP config — place in project root at `.claude/mcp.json`

```json
{
  "servers": {
    "azure-devops": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@azure-devops/mcp",
        "<YOUR_ORG>",
        "-d",
        "core",
        "work",
        "work-items",
        "repositories",
        "wiki",
        "builds",
        "test-plans"
      ]
    }
  }
}
```

**Domain reference** — only load what you need to stay within tool limits:

| Domain | What it unlocks |
|---|---|
| `core` | Projects, teams, iterations — always include this |
| `work` | Sprint boards, backlogs, capacity |
| `work-items` | Create/read/update/delete work items |
| `repositories` | Repos, branches, commits, pull requests |
| `wiki` | Wiki pages: create, read, update |
| `builds` | Pipelines, build definitions, queue builds |
| `test-plans` | Test plans, suites, test cases, results |

### Verify connection
Start Claude Code in the project directory and ask:
```
List the projects in my Azure DevOps organization
```
If it returns your projects, the MCP server is working correctly.

---

## ADO Context File

The orchestrator writes `./project/ado-config.md` at setup time. Every agent reads
this before any ADO operation. Format:

```markdown
# Azure DevOps Config

- Organization: contoso
- Project: MyProject
- Repo: my-repo
- Default branch: main
- Wiki: MyProject.wiki
- Work item type (features): User Story
- Work item type (bugs): Bug
- Work item type (tasks): Task
- Iteration path: MyProject\Sprint 1
- Area path: MyProject\Backend
```

---

## Per-Agent ADO Instructions

### 📋 PO / Business Analyst

**Responsibility:** Manage the backlog. Create and maintain Work Items from specs.

Key operations:
```
# Create a User Story from a spec
"Create a work item of type 'User Story' in project MyProject titled '[title]'
 with description '[description]' and acceptance criteria '[criteria]'
 in iteration MyProject\Sprint 1"

# Bulk-create tasks from a feature breakdown
"Create the following Task work items linked as children of User Story #42: ..."

# Update sprint assignments
"Move work items #42, #43, #44 to iteration MyProject\Sprint 2"

# Query the backlog
"List all open User Stories in MyProject assigned to the current iteration"
```

After creating each Work Item, record the ADO ID in the local ticket:
```markdown
ado_work_item_id: 42
```

---

### 🎨 UI/UX Designer

**Responsibility:** Document design specs in the ADO Wiki.

Key operations:
```
# Create a wiki page for a design spec
"Create a wiki page at '/design/login-screen' in the MyProject.wiki wiki
 with content: [markdown content of the design spec]"

# Update a design token page
"Update the wiki page '/design/tokens' with the following content: ..."

# Link a design page to a work item
"Update work item #42 description to include a link to the wiki page '/design/login-screen'"
```

Name wiki pages to match spec filenames: `specs/login-screen.md` → wiki `/design/login-screen`.

---

### 🏗️ Architect

**Responsibility:** Maintain architecture decisions in the ADO Wiki.

Key operations:
```
# Create an ADR page in the wiki
"Create a wiki page at '/architecture/decisions/adr-001-tech-stack' in MyProject.wiki
 with content: [ADR markdown]"

# Maintain the architecture map
"Update the wiki page '/architecture/overview' with the current module map: ..."

# Create sprint iterations
"Create an iteration named 'Sprint 1' under MyProject with start date X and end date Y"
```

Mirror every `./project/decisions/<topic>.md` to ADO Wiki at `/architecture/decisions/<topic>`.

---

### ⚛️ Frontend Developer

**Responsibility:** Push code to ADO repo, open Pull Requests, link PRs to Work Items.

Key operations:
```bash
# Push to ADO repo (standard git — ADO repo is the remote)
git remote add origin https://dev.azure.com/<org>/<project>/_git/<repo>
git push -u origin main

# Create a feature branch and push
git checkout -b feature/T-001-login-screen
git push -u origin feature/T-001-login-screen
```

```
# Create a Pull Request via MCP
"Create a pull request in repository my-repo from branch feature/T-001-login-screen
 to main with title 'T-001: Login screen' and description:
 'Implements the login screen per spec. Closes #42 (work item).
  Design spec: /design/login-screen'"

# Link PR to Work Item
"Link work item #42 to pull request #7 in repository my-repo"
```

PR naming convention: `T-XXX: <short description>` — always include ticket ID.

---

### ⚙️ Backend Developer

**Responsibility:** Push backend code, open PRs, maintain API docs in Wiki.

Key operations — same as Frontend for repo/PR operations, plus:

```
# Update API wiki page after adding endpoints
"Update the wiki page '/docs/api' in MyProject.wiki with: [updated API reference]"

# Query pipeline status
"List the latest build results for pipeline 'Backend CI' in project MyProject"

# Queue a build
"Queue a build for pipeline definition 'Backend CI' in project MyProject
 on branch feature/T-002-auth-api"
```

Always update `/docs/api` wiki page immediately after any endpoint change.

---

### 🗄️ DBA

**Responsibility:** Document database schema in ADO Wiki, review DB-related PRs.

Key operations:
```
# Create/update DB schema wiki page
"Update the wiki page '/docs/database' in MyProject.wiki with: [schema markdown]"

# Create a migration log entry
"Append to the wiki page '/docs/database/migrations' the following entry: ..."

# Review a PR for DB changes
"Get the details of pull request #7 in repository my-repo including file changes"
"Get the diff for pull request #7 in repository my-repo"
```

Mirror `./project/docs/database/README.md` to ADO Wiki `/docs/database` after every schema change.

---

### 🔐 Security Expert

**Responsibility:** Document security policies in Wiki, review PRs for vulnerabilities.

Key operations:
```
# Maintain security wiki
"Update the wiki page '/docs/security' in MyProject.wiki with: [threat model]"

# Review a PR
"Get the file changes for pull request #7 in repository my-repo"

# Create a security bug work item when a vulnerability is found
"Create a work item of type 'Bug' titled '[SECURITY] Hardcoded API key in config.ts'
 with severity 1 - Critical, description: [details], assigned to: backend developer"
```

Security bugs go directly to priority 1 — do not wait for sprint assignment.

---

### 🔍 Code Reviewer

**Responsibility:** Review PRs via ADO, add comments, approve or request changes.

Key operations:
```
# List PRs awaiting review
"List all active pull requests in repository my-repo in project MyProject
 where I am a required reviewer"

# Get PR details and diff
"Get the details and file changes for pull request #7 in repository my-repo"

# Add a review comment
"Add a comment to pull request #7 in repository my-repo:
 'File src/auth/login.tsx line 42: This logic is duplicated from src/auth/register.tsx.
  Please extract to a shared hook.'"

# Approve or request changes
"Approve pull request #7 in repository my-repo"
# or
"Request changes on pull request #7 in repository my-repo with comment: ..."
```

Every local code review finding should also be posted as a PR comment in ADO so the
history is preserved in the repository.

---

### 🧪 QA Engineer

**Responsibility:** Create Test Plans and Test Cases in ADO, link to Work Items.

Key operations:
```
# Create a Test Plan for a feature
"Create a test plan named 'T-001 Login Screen Tests' in project MyProject
 for iteration MyProject\Sprint 1"

# Create a Test Suite within the plan
"Create a test suite named 'Happy Path' in test plan 'T-001 Login Screen Tests'"

# Create Test Cases
"Create a test case titled 'User can log in with valid credentials'
 in test suite 'Happy Path' of test plan 'T-001 Login Screen Tests'
 with steps:
 1. Navigate to /login
 2. Enter valid email and password
 3. Click 'Sign In'
 Expected: User is redirected to dashboard"

# Record test results
"Update test case #101 result to 'Passed' in test run for test plan 'T-001 Login Screen Tests'"

# Create a Bug from a failed test
"Create a work item of type 'Bug' titled '[BUG] Login fails with valid credentials'
 linked to work item #42 and test case #101 with description: [steps to reproduce]"
```

Always link Test Cases to their parent Work Items and Test Plans to the sprint iteration.

---

## Wiki Structure Convention

Maintain this structure in ADO Wiki:

```
MyProject.wiki/
├── architecture/
│   ├── overview.md          ← mirrors docs/architecture/README.md
│   └── decisions/
│       ├── adr-001-*.md     ← mirrors decisions/*.md
│       └── ...
├── design/
│   └── <screen-name>.md     ← mirrors specs/<feature>-design.md
├── docs/
│   ├── api.md               ← mirrors docs/api/README.md
│   ├── database.md          ← mirrors docs/database/README.md
│   └── security.md          ← mirrors docs/security/README.md
└── business-logic/
    └── overview.md          ← mirrors docs/business-logic/README.md
```

The orchestrator is responsible for reminding agents to mirror local docs to the wiki
after significant changes.

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `az login` not found | Install Azure CLI: `brew install azure-cli` |
| "Permission denied" on tool call | Check ADO license — Basic or higher required |
| MCP server not starting | Run `npx @azure-devops/mcp <org>` manually to see errors |
| Auth token expired | Run `az login` again; tokens expire after ~1 hour |
| Organization not found | Verify org name in `ado-config.md` — no trailing slashes |
| Personal MSA account | ADO MCP requires Entra-backed org; personal accounts not supported |

For Claude Code specifically: the **local** MCP server (`npx @azure-devops/mcp`) is
required. The remote hosted server (`https://mcp.dev.azure.com`) does not yet support
Claude Code authentication.
