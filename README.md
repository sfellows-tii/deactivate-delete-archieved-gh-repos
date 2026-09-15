# Find and Deactivate GitHub Archived Repos in Snyk

This tool helps you identify archived repositories in GitHub (both GitHub.com and GitHub Enterprise) that are also imported into Snyk. It will generate a JSON file with matching projects and provides a command to deactivate or delete them in Snyk.

## Prerequisites

- Python 3.10.14 or higher
- [Typer](https://typer.tiangolo.com/) for command-line interface
- [Requests](https://docs.python-requests.org/en/master/) for HTTP requests

## Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/yourrepository.git
   cd yourrepository
   ```

2. **Install Dependencies**

   It's recommended to use a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Environment Variables**

   Ensure you have the following environment variables set:

   - `GITHUB_TOKEN`: Your GitHub.com personal access token (required for `--provider github`).
     - Required scopes: `repo` (or at minimum `read:org`)
   - `GHE_TOKEN`: Your GitHub Enterprise personal access token (required for `--provider ghe`).
     - Required scopes: `repo` (or at minimum `read:org`)
   - `SNYK_TOKEN`: Your Snyk API token.
     - Required permissions: Read/write access to projects and targets

## Usage

### Generate Archived Repositories JSON

This command generates a JSON file containing Snyk projects that match archived GitHub repositories.

```bash
python index.py generate-archived-repos-json --snyk-org-id <SNYK_ORG_ID> [OPTIONS]
```

#### Required Options

- `--snyk-org-id` or `-s`: The ID of the Snyk organization to search for targets.

#### GitHub Organization Options (choose one)

- `--github-org-name` or `-g`: The name of a specific GitHub organization to search for archived repos.
- `--all-github-orgs` or `-a`: Scan all GitHub organizations accessible by the token.

#### Provider Options

- `--provider` or `-p`: The Git provider. Options: `github` (default) or `ghe`.
- `--github-base-url` or `-gb`: The base URL for GitHub API including `/api/v3` (optional for GHE, defaults to `https://ghe.iparadigms.com/api/v3`).

#### Other Options

- `--output-file` or `-o`: (Optional) The file path to write the JSON data. Defaults to `archived-projects.json`.
- `--snyk-tenant` or `-st`: (Optional) The tenant of the Snyk organization. Defaults to `api.snyk.io`.
- `--log-level` or `-l`: (Optional) Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Defaults to `INFO`.

### Deactivate Projects from JSON

This command reads a JSON file and deactivates the corresponding projects in Snyk.

```bash
python index.py deactivate-from-json --input-file <INPUT_FILE> [--snyk-tenant <SNYK_TENANT>]
```

- `--input-file` or `-i`: The file path to read the JSON data from.
- `--snyk-tenant` or `-st`: (Optional) The tenant of the Snyk organization. Defaults to `api.us.snyk.io`.

### Delete Projects from JSON

This command reads a JSON file and deletes the corresponding projects in Snyk.

```bash
python index.py delete-from-json --input-file <INPUT_FILE> [--snyk-tenant <SNYK_TENANT>]
```

- `--input-file` or `-i`: The file path to read the JSON data from.
- `--snyk-tenant` or `-st`: (Optional) The tenant of the Snyk organization. Defaults to `api.us.snyk.io`.

## Examples

### GitHub.com

**Scan a single organization:**

```bash
python index.py generate-archived-repos-json \
  --github-org-name my-github-org \
  --snyk-org-id abc123-snyk-org-id
```

**Scan all accessible organizations:**

```bash
python index.py generate-archived-repos-json \
  --all-github-orgs \
  --snyk-org-id abc123-snyk-org-id
```

### GitHub Enterprise

**Scan a single organization (using default GHE URL https://ghe.iparadigms.com/api/v3):**

```bash
python index.py generate-archived-repos-json \
  --github-org-name my-ghe-org \
  --snyk-org-id abc123-snyk-org-id \
  --provider ghe
```

**Scan a single organization (with custom GHE URL):**

```bash
python index.py generate-archived-repos-json \
  --github-org-name my-ghe-org \
  --snyk-org-id abc123-snyk-org-id \
  --provider ghe \
  --github-base-url https://ghe.company.com/api/v3
```

**Scan all organizations on default GHE instance:**

```bash
python index.py generate-archived-repos-json \
  --all-github-orgs \
  --snyk-org-id abc123-snyk-org-id \
  --provider ghe
```

**Scan all organizations on custom GHE instance:**

```bash
python index.py generate-archived-repos-json \
  --all-github-orgs \
  --snyk-org-id abc123-snyk-org-id \
  --provider ghe \
  --github-base-url https://ghe.company.com/api/v3
```

**With debug logging:**

```bash
python index.py generate-archived-repos-json \
  --all-github-orgs \
  --snyk-org-id abc123-snyk-org-id \
  --provider ghe \
  --log-level DEBUG
```

### Deactivate or Delete Projects

**Deactivate projects from the generated JSON file:**

```bash
python index.py deactivate-from-json -i archived-projects.json
```

**Delete projects from the generated JSON file:**

```bash
python index.py delete-from-json -i archived-projects.json
```

## How It Works

1. **Fetch Archived Repositories**: The tool queries GitHub (or GHE) for all archived repositories in the specified organization(s).
2. **Fetch Snyk Targets**: Retrieves all import targets from the specified Snyk organization.
3. **Match URLs**: Compares the archived repository URLs with Snyk target URLs to find matches.
4. **Fetch Projects**: For each matching target, retrieves all associated Snyk projects.
5. **Export to JSON**: Writes all matching projects to a JSON file for review.
6. **Deactivate/Delete**: Optionally deactivate or delete the identified projects in Snyk.

## Notes

- When using `--all-github-orgs` with GitHub.com, only organizations that your token has access to will be scanned.
- When using `--all-github-orgs` with GHE, all organizations on the GitHub Enterprise instance will be scanned.
- The tool uses different endpoints for GitHub.com (`/user/orgs`) and GHE (`/organizations`) to fetch organization lists.
- For GHE, if `--github-base-url` is not specified, it defaults to `https://ghe.iparadigms.com/api/v3`.
- Always review the generated JSON file before running deactivate or delete commands.
