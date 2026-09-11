import requests
import logging


def get_archived_repos_urls(org_name, token, base_url="https://api.github.com", is_ghe=False):
    # Strip any whitespace from token
    token = token.strip() if token else token

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/json" if is_ghe else "application/vnd.github.v3+json"
    }
    URL = f"{base_url}/orgs/{org_name}/repos"

    logging.info(f"Fetching repos from: {URL}")
    logging.info(f"Using GHE mode: {is_ghe}")
    logging.info(f"Accept header: {headers['Accept']}")
    logging.debug(f"Token (first 10 chars): {token[:10]}...")

    archived_repos = []

    page = 1

    while True:
        params = {"per_page": 100, "page": page, "type": "all"}
        logging.debug(f"Requesting page {page} with params: {params}")
        response = requests.get(URL, headers=headers, params=params)
        if response.status_code != 200:
            logging.error(f"Error: {response.status_code} - {response.text}")
            logging.error(f"Request URL: {response.url}")
            print(f"Error: {response.status_code} - {response.text}")
            break

        repos = response.json()
        if not repos:
            break

        archived_in_page = [repo["html_url"] for repo in repos if repo.get("archived")]
        if archived_in_page:
            logging.info(f"Found {len(archived_in_page)} archived repos in page {page}")
            for url in archived_in_page:
                logging.debug(f"  Archived: {url}")
        archived_repos.extend(archived_in_page)
        page += 1

    logging.info(f"Total Archived Repositories: {len(archived_repos)}")
    print(f"Total Archived Repositories: {len(archived_repos)}")
    return archived_repos
