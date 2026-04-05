## Azure DevOps Integration

Azure DevOps MCP is active for this project. You have access to ADO tools via the MCP server.

BEFORE ANY ADO OPERATION: Read {{WORKSPACE_PATH}}/ado-config.md for the organization,
project name, repo name, wiki name, and iteration paths.

### Your ADO responsibilities by role — read only the section relevant to you:

**po-ba**: Create and update Work Items (User Stories, Tasks) from specs. Set iteration
paths. Link work items to specs in the wiki. After creating a work item, record its ADO ID
in the local ticket frontmatter as `ado_work_item_id`.

**uiux**: Create wiki pages at `/design/<screen-name>` mirroring your spec files.
Link design wiki pages to relevant work items.

**architect**: Create wiki pages at `/architecture/decisions/<adr-name>` for every ADR.
Maintain `/architecture/overview` as a mirror of docs/architecture/README.md.

**frontend**: Push code to the ADO repo. Create PRs from your feature branch to main.
Name PRs: "T-XXX: <description>". Link PRs to their work item.

**backend**: Same as frontend for repo/PRs. Also update `/docs/api` wiki page after
every endpoint change.

**dba**: Update `/docs/database` wiki page after every schema change or migration.
Review DB-related PRs by reading the diff before signing off.

**security**: Update `/docs/security` wiki page after every review. Post your review
findings as PR comments in ADO in addition to the local outbox message.

**reviewer**: Read PR diffs via ADO. Post all review comments to the PR as well as
locally. Approve or request changes via ADO when complete.

**qa**: Create a Test Plan per feature in ADO. Create Test Suites and Test Cases linked
to the relevant Work Items. Record test results. Create Bug work items for failures.

### General rules
- Never commit secrets, .env files, or credentials to the ADO repo
- Always work on a feature branch — never push directly to main
- PR descriptions must reference the ticket ID (T-XXX) and link to the spec
- Wiki pages must be kept in sync with local docs/ — update both together
