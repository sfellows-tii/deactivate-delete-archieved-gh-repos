import requests
import logging


def get_user_orgs(token, base_url="https://api.github.com", is_ghe=False):
    """Get all organizations accessible to the authenticated user or from the GHE instance."""
    headers = {
        "Authorization": f"token {token.strip()}",
        "Accept": "application/json"
    }

    if is_ghe:
        # For GHE, use /organizations endpoint with 'since' pagination
        URL = f"{base_url}/organizations"
        logging.info(f"Fetching all organizations from GHE: {URL}")

        orgs = []
        since = 0

        while True:
            params = {"per_page": 100, "since": since}
            response = requests.get(URL, headers=headers, params=params)

            if response.status_code != 200:
                logging.error(f"Error fetching orgs: {response.status_code} - {response.text}")
                print(f"Error fetching orgs: {response.status_code} - {response.text}")
                break

            page_orgs = response.json()
            if not page_orgs:
                break

            org_logins = [org["login"] for org in page_orgs]
            logging.info(f"Found {len(org_logins)} orgs (since={since}): {', '.join(org_logins)}")
            orgs.extend(org_logins)

            # Update 'since' to the last org's id for pagination
            since = page_orgs[-1]["id"]

    else:
        # For GitHub.com, use /user/orgs endpoint with page pagination
        URL = f"{base_url}/user/orgs"
        logging.info(f"Fetching user organizations from GitHub.com: {URL}")

        orgs = []
        page = 1

        while True:
            params = {"per_page": 100, "page": page}
            response = requests.get(URL, headers=headers, params=params)

            if response.status_code != 200:
                logging.error(f"Error fetching orgs: {response.status_code} - {response.text}")
                print(f"Error fetching orgs: {response.status_code} - {response.text}")
                break

            page_orgs = response.json()
            if not page_orgs:
                break

            org_logins = [org["login"] for org in page_orgs]
            logging.info(f"Found {len(org_logins)} orgs in page {page}: {', '.join(org_logins)}")
            orgs.extend(org_logins)
            page += 1

    logging.info(f"Total organizations found: {len(orgs)}")
    return orgs


def get_archived_repos_urls(org_name, token, base_url="https://api.github.com", is_ghe=False):
    # Strip any whitespace from token
    token = token.strip() if token else token

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/json" if is_ghe else "application/vnd.github.v3+json"
    }
    URL = f"{base_url}/orgs/{org_name}/repos"

    logging.info(f"Fetching repos from: {URL}")
    logging.debug(f"Using GHE mode: {is_ghe}")
    logging.debug(f"Accept header: {headers['Accept']}")
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
