import requests as r
from decouple import config
from jinja2 import Environment, select_autoescape, FileSystemLoader

if not config("ORGANIZATION"):
    raise Exception("ORGANIZATION env var is required")

organization = config("ORGANIZATION")

if not config("REPO"):
    raise Exception("REPO env var is required")

repo = config("REPO")

resp = r.get(f"https://api.github.com/repos/{organization}/{repo}/commits/main")
json_resp = resp.json()

env = Environment(
    loader=FileSystemLoader("./github/changelog/"),
    autoescape=select_autoescape()
)

template = env.get_template("github-changelog.html")

files = []

for file in json_resp["files"]:
    files.append({
        "filename": file["filename"],
        "status": file["status"],
        "patch": file["patch"]
    })

rendered = template.render(author=f"{json_resp['commit']['author']['name']} <{json_resp['commit']['author']['email']}>",
                           sha=json_resp["sha"], organization=organization, repo=repo,
                           date=json_resp['commit']['author']['date'], message=json_resp['commit']['message'],
                           files=files)


with open("./github/changelog/output.html", "w") as f:
    f.write(rendered)
