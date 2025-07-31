import os
import requests
import yaml
from jinja2 import Environment, FileSystemLoader

COMPOSE_PATH = "compose.yaml"
DEFAULT_PROJECT_KEY = "marcus"
DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASS = "P@ssw0rd$123"


def extract_compose_info(compose_path=COMPOSE_PATH):
    with open(compose_path, "r", encoding="utf-8") as f:
        compose = yaml.safe_load(f)

    info = {}
    sonar_db_env = compose["services"]["sonar-db"]["environment"]
    for env_var in sonar_db_env:
        k, v = env_var.split("=", 1)
        info[f"sonar_db_{k.lower().replace('postgres_', '')}"] = v
    app_db_env = compose["services"]["app-db"]["environment"]
    for env_var in app_db_env:
        k, v = env_var.split("=", 1)
        info[f"app_db_{k.lower().replace('postgres_', '')}"] = v
    sonar_env = compose["services"]["sonar"]["environment"]
    for env_var in sonar_env:
        k, v = env_var.split("=", 1)
        info[k.lower()] = v
    info["sonar_url"] = (
        f"http://localhost:{compose['services']['sonar']['ports'][0].split(':')[0]}"
    )
    info["sonar_project_key"] = os.environ.get("SONAR_PROJECT_KEY", DEFAULT_PROJECT_KEY)
    info["sonar_admin_user"] = os.environ.get("SONAR_ADMIN_USER", DEFAULT_ADMIN_USER)
    info["sonar_admin_pass"] = os.environ.get("SONAR_ADMIN_PASS", DEFAULT_ADMIN_PASS)
    info["app_db_host"] = "app-db"
    info["app_db_port"] = "5432"
    info["app_db_name"] = info.get("app_db_db", "marcus_db")

    print(info)
    return info


def project_exists(sonar_url, sonar_project_key, admin_user, admin_pass):
    url = f"{sonar_url}/api/projects/search?projects={sonar_project_key}"
    resp = requests.get(url, auth=(admin_user, admin_pass), timeout=10)
    if not resp.ok:
        print(f"SonarQube API error: {resp.status_code} {resp.reason}\n{resp.text}")
        return False
    try:
        data = resp.json()
    except Exception as e:
        print(
            f"Failed to parse SonarQube response as JSON: {e}\nResponse text: {resp.text}"
        )
        return False
    return data.get("components") and any(
        p["key"] == sonar_project_key for p in data["components"]
    )


def create_project(sonar_url, sonar_project_key, admin_user, admin_pass):
    url = f"{sonar_url}/api/projects/create"
    resp = requests.post(
        url,
        data={"name": sonar_project_key, "project": sonar_project_key},
        auth=(admin_user, admin_pass),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    return resp.status_code == 200


def generate_token(sonar_url, admin_user, admin_pass, project_key):
    url = f"{sonar_url}/api/user_tokens/generate"
    resp = requests.post(
        url,
        data={
            "name": "automation-token",
            "type": "PROJECT_ANALYSIS_TOKEN",
            "projectKey": project_key,
            "projectName": project_key,
        },
        auth=(admin_user, admin_pass),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    if resp.status_code == 200:
        return resp.json().get("token", "")
    return ""


info = extract_compose_info(COMPOSE_PATH)

if not project_exists(
    info["sonar_url"],
    info["sonar_project_key"],
    info["sonar_admin_user"],
    info["sonar_admin_pass"],
):
    print(f"Creating SonarQube project '{info['sonar_project_key']}'...")
    create_project(
        info["sonar_url"],
        info["sonar_project_key"],
        info["sonar_admin_user"],
        info["sonar_admin_pass"],
    )

sonar_token = generate_token(
    info["sonar_url"],
    info["sonar_admin_user"],
    info["sonar_admin_pass"],
    info["sonar_project_key"],
)

env = Environment(loader=FileSystemLoader("."))
template = env.get_template("env.j2")

context = {
    "sonar_token": sonar_token,
    "sonar_url": info["sonar_url"],
    "sonar_project_key": info["sonar_project_key"],
    "sonar_db_url": info.get("sonar_jdbc_url", ""),
    "sonar_db_user": info.get("sonar_jdbc_username", ""),
    "sonar_db_password": info.get("sonar_jdbc_password", ""),
    "app_db_host": info.get("app_db_host", "app-db"),
    "app_db_port": info.get("app_db_port", "5432"),
    "app_db_user": info.get("app_db_user", ""),
    "app_db_password": info.get("app_db_password", ""),
    "app_db_name": info.get("app_db_name", "marcus_db"),
}

with open(".env", "w", encoding="utf-8") as f:
    f.write(template.render(context))
