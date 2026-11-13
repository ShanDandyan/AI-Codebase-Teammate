import base64
import os
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP

# 1. Load environment variables
load_dotenv()
token = os.getenv("GITHUB_TOKEN")

# 2. Create FastMCP server
mcp = FastMCP("Codebase_Teammate")


# --- HELPER: GITHUB API REQUESTS ---
def github_get(path: str, params: dict = None) -> requests.Response:
    """Helper to build GitHub API URLs, handle headers/auth, and manage error responses."""
    url = f"https://api.github.com{path}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(url, headers=headers, params=params, timeout=10)

    if response.status_code != 200:
        try:
            error_msg = response.json().get("message", response.text)
        except Exception:
            error_msg = response.text
        raise RuntimeError(
            f"GitHub API Error [{response.status_code}]: {error_msg}"
        )

    return response
# --- TOOL 1: LIST FILES ---
@mcp.tool()
def list_files(repo_owner: str, repo_name: str) -> list[str]:
    """Returns a list of top-level file names in the repository given a repo_owner and repo_name (excludes directories)."""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/"

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        contents = response.json()
        return [
            item["name"]
            for item in contents
            if isinstance(item, dict) and item.get("type") == "file"
        ]
    else:
        error_msg = response.json().get("message", "Unknown GitHub API error")
        raise RuntimeError(
            f"GitHub API Error [{response.status_code}]: {error_msg}"
        )


# --- TOOL 2: READ FILE ---
@mcp.tool()
def read_file(repo_owner: str, repo_name: str, file_path: str) -> str:
    """Fetches and decodes the raw text content of a specific file from a GitHub repository."""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data.get("type") != "file":
            raise ValueError(f"Path '{file_path}' is a directory, not a file.")

        encoded_content = data.get("content", "")
        decoded_bytes = base64.b64decode(encoded_content)
        return decoded_bytes.decode("utf-8")
    else:
        error_msg = response.json().get("message", "Could not read file.")
        raise RuntimeError(
            f"GitHub API Error [{response.status_code}]: {error_msg}"
        )


# --- TOOL 3: GET COMMIT HISTORY ---
@mcp.tool()
def get_commit_history(
    repo_owner: str, repo_name: str, max_commits: int = 10
) -> list[str]:
    """Fetches recent commit history for a repository.

    Returns a compact list of formatted strings: '[short_sha] author - date:
    message'.
    """
    response = github_get(
        f"/repos/{repo_owner}/{repo_name}/commits",
        params={"per_page": min(max_commits, 30)},
    )
    commits = response.json()

    formatted_commits = []
    for item in commits:
        sha = item.get("sha", "")[:7]
        commit_data = item.get("commit", {})
        author_data = commit_data.get("author", {})

        author = author_data.get("name", "Unknown")
        date = author_data.get("date", "")[:10]  # Format as YYYY-MM-DD
        message = commit_data.get("message", "").split("\n")[0]  # First line only

        formatted_commits.append(f"[{sha}] {author} - {date}: {message}")

    return formatted_commits

# IMPORTANT: mcp.run() MUST be inside if __name__ == "__main__":
if __name__ == "__main__":
    mcp.run()