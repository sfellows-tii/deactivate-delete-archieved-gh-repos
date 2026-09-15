import typer
import json
import logging
import sys

from utils.githubApi import get_archived_repos_urls, get_user_orgs
from utils.tokenReader import get_github_token, get_ghe_token
from utils.synkApi import get_snyk_targets, get_snyk_projects_by_target_id, deactivate_project, delete_project
from utils.fileReader import write_json_to_file

app = typer.Typer()

def setup_logging(level: str):
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO)
    )

def find_matching_targets(archived_repo_urls, snyk_targets):
    matching_targets = []
    logging.debug(f"Comparing {len(archived_repo_urls)} archived repos against {len(snyk_targets)} Snyk targets")

    for target in snyk_targets:
        try:
            target_url = target.get("attributes", {}).get("url")
            logging.debug(f"Checking Snyk target URL: {target_url}")
            if target_url in archived_repo_urls:
                logging.info(f"Match found: {target_url}")
                matching_targets.append({
                    "snyk_target_id": target.get("id"),
                    "url": target_url
                })
        except Exception as e:
            logging.error(f"Error getting target URL for {target}: {e}")

    logging.info(f"Found {len(matching_targets)} matching targets")
    return matching_targets

def get_all_projects(matching_targets, snyk_tenant, snyk_org_id):
    all_projects = []
    for target in matching_targets:
        projects = get_snyk_projects_by_target_id(snyk_tenant, snyk_org_id, target.get("snyk_target_id"))
        if isinstance(projects, dict) and 'data' in projects:
            all_projects.extend(projects['data'])
        else:
            all_projects.extend(projects)
            
    return all_projects

@app.command()
def generate_archived_repos_json(
    snyk_org_id: str = typer.Option(..., "--snyk-org-id", "-s", help="The ID of the Snyk organization to search for targets"),
    github_org_name: str = typer.Option(None, "--github-org-name", "-g", help="The name of a specific GitHub organization to search for archived repos"),
    all_orgs: bool = typer.Option(False, "--all-orgs", "-a", help="Scan all GitHub organizations accessible by the token"),
    output_file: str = typer.Option("archived-projects.json", "--output-file", "-o", help="The file path to write the JSON data"),
    snyk_tenant: str = typer.Option("api.snyk.io", "--snyk-tenant", "-st", help="The tenant of the Snyk organization"),
    provider: str = typer.Option("github", "--provider", "-p", help="The Git provider (github or ghe)"),
    github_base_url: str = typer.Option(None, "--github-base-url", "-gb", help="The base URL for GitHub API including /api/v3 (required for GHE, e.g., https://ghe.iparadigms.com/api/v3)"),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
):
    setup_logging(log_level)
    logging.info("Starting to generate archived repos JSON")

    # Validate that either github_org_name or all_orgs is specified
    if not github_org_name and not all_orgs:
        logging.error("Either --github-org-name or --all-orgs must be specified")
        raise typer.BadParameter("Either --github-org-name or --all-orgs must be specified")

    if github_org_name and all_orgs:
        logging.error("Cannot specify both --github-org-name and --all-orgs")
        raise typer.BadParameter("Cannot specify both --github-org-name and --all-orgs")

    # Determine the base URL and token based on provider
    is_ghe = provider.lower() == "ghe"
    if is_ghe:
        if not github_base_url:
            logging.error("--github-base-url is required when using 'ghe' provider")
            raise typer.BadParameter("--github-base-url is required when using 'ghe' provider")
        base_url = github_base_url
        github_token = get_ghe_token()
    else:
        base_url = "https://api.github.com"
        github_token = get_github_token()

    logging.info(f"Using GitHub API base URL: {base_url}")

    # Determine which orgs to scan
    if all_orgs:
        logging.info("Fetching all accessible GitHub organizations...")
        org_names = get_user_orgs(github_token, base_url, is_ghe)
        if not org_names:
            logging.error("No organizations found")
            return
        logging.info(f"Will scan {len(org_names)} organizations: {', '.join(org_names)}")
    else:
        org_names = [github_org_name]
        logging.info(f"Scanning single organization: {github_org_name}")

    # Collect archived repos from all specified orgs
    archived_repo_urls = []
    for org in org_names:
        logging.info(f"Fetching archived repos from organization: {org}")
        org_archived_repos = get_archived_repos_urls(org, github_token, base_url, is_ghe)
        archived_repo_urls.extend(org_archived_repos)

    logging.info(f"Found {len(archived_repo_urls)} total archived repos across all organizations")

    snyk_targets = get_snyk_targets(snyk_tenant, snyk_org_id)
    all_projects = []

    logging.debug(f"Archived repo URLs: {json.dumps(archived_repo_urls, indent=4)}")
    logging.debug(f"Snyk targets: {json.dumps(snyk_targets, indent=4)}")
    
    # Check if 'data' exists in snyk_targets and set snyk_targets to it
    if 'data' in snyk_targets:
        snyk_targets = snyk_targets['data']

    logging.info("Finding matching targets for archived repos in Snyk...")
    matching_targets = find_matching_targets(archived_repo_urls, snyk_targets)
    logging.debug(f"Matching targets findings: {json.dumps(matching_targets, indent=4)}")
    
    logging.info("Finding projects by target id...")
    all_projects = get_all_projects(matching_targets, snyk_tenant, snyk_org_id)
    logging.debug(f"All projects findings: {json.dumps(all_projects, indent=4)}")

    logging.info("Writing matching targets to a JSON file")
    write_json_to_file(all_projects, output_file)

@app.command()
def deactivate_from_json(
    input_file: str = typer.Option(..., "--input-file", "-i", help="The file path to read the JSON data from"),
    snyk_tenant: str = typer.Option("api.snyk.io", "--snyk-tenant", "-st", help="The tenant of the Snyk organization"),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
):
    setup_logging(log_level)
    logging.info("Starting deactivation from JSON")

    try:
        with open(input_file, 'r') as json_file:
            project_data = json.load(json_file)
            for project in project_data:
                logging.info(f"Deactivating target: {project['id']} with URL: {project['attributes']['name']}")
                deactivate_project(snyk_tenant, project['relationships']['organization']['data']['id'], project['id'])
    except IOError as e:
        logging.error(f"An error occurred while reading the file: {e}")
    except json.JSONDecodeError as e:
        logging.error(f"An error occurred while decoding JSON: {e}")

@app.command()
def delete_from_json(
    input_file: str = typer.Option(..., "--input-file", "-i", help="The file path to read the JSON data from"),
    snyk_tenant: str = typer.Option("api.snyk.io", "--snyk-tenant", "-st", help="The tenant of the Snyk organization"),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
):
    setup_logging(log_level)
    logging.info("Starting deletion from JSON")

    try:
        with open(input_file, 'r') as json_file:
            project_data = json.load(json_file)
            for project in project_data:
                logging.info(f"Deleting target: {project['id']} with URL: {project['attributes']['name']}")
                delete_project(snyk_tenant, project['relationships']['organization']['data']['id'], project['id'])
    except IOError as e:
        logging.error(f"An error occurred while reading the file: {e}")
    except json.JSONDecodeError as e:
        logging.error(f"An error occurred while decoding JSON: {e}")

if __name__ == "__main__":
    app()
