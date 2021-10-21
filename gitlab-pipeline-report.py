import requests as r
from decouple import config


if not config("GITLAB_TOKEN"):
    raise Exception("GITLAB_TOKEN env var is required")

gitlab_token = config("GITLAB_TOKEN")

if not config("PROJECT_ID"):
    raise Exception("PROJECT_ID env var is required")

project_id = config("PROJECT_ID")

auth_header = {"Authorization": f"Bearer {gitlab_token}"}


def get_pipelines():
    resp = r.get(
        f"https://gitlab.com/api/v4/projects/{project_id}/pipelines",
        headers=auth_header,
    )
    return resp.json()


def get_recent_pipeline():
    pipelines = get_pipelines()
    if len(pipelines) > 0:
        return pipelines[0]
    raise Exception("This will only work if a pipeline has previously been run")


def get_pipeline_id(data) -> str:
    if not "id" in data:
        raise Exception("No 'id' field found in pipeline response")
    return data["id"]


def get_pipeline_url():
    pipeline = get_recent_pipeline()
    if "web_url" not in pipeline:
        raise Exception("There is no 'web_url' field on recent pipeline")
    return pipeline["web_url"]


def get_jobs_from_pipeline(pipeline_id: str):
    resp = r.get(
        f"https://gitlab.com/api/v4/projects/{project_id}/pipelines/{pipeline_id}/jobs",
        headers=auth_header,
    )
    return resp.json()


def get_trace_from_job_id(job_id):
    resp = r.get(
        f"https://gitlab.com/api/v4/projects/{project_id}/jobs/{job_id}/trace",
        headers=auth_header,
    )
    return resp.content.decode("utf-8").replace("\n", "<br />")


def generate_jobs_array(data):
    if not len(data) > 0:
        raise Exception("There is no job data :(")
    jobs_array = []
    for job in data:
        try:
            job_dict = {}
            id = job["id"]
            job_dict["status"] = job["status"]
            job_dict["name"] = f"{job['name']} - {id}"
            job_dict["url"] = job["web_url"]
            job_dict["logs"] = get_trace_from_job_id(id)
            jobs_array.append(job_dict)
        except Exception as e:
            print(e)
    return jobs_array


results = generate_jobs_array(
    get_jobs_from_pipeline(get_pipeline_id(get_recent_pipeline()))
)


title = f"GitLab results - <a href='{get_pipeline_url()}'>Pipeline #{get_pipeline_id(get_recent_pipeline())}</a>"


TOP = """
<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/style.css">

  <title>GitLab Results</title>
</head>

<body>

  <h1>REPLACE_TITLE</h1>
  <table>
    <tr>
      <th>Job</th>
      <th>Status</th>
      <th>Logs</th>
    </tr>
    <tbody>
"""

BOTTOM = """
    </tbody>
  </table>

</body>

</html>
"""


def generate_html():
    NEW_TOP = TOP.replace("REPLACE_TITLE", title)
    TABLE_DATA: str = ""

    for result in results:
        TABLE_DATA += f"""<tr>
      <td><a href="{result['url']}">{result['name']}</a></td>
      <td>{result['status']}</td>
      <td>{result['logs']}</td></tr>"""

    return NEW_TOP + TABLE_DATA + BOTTOM


with open("index.html", "w") as file:
    file.write(generate_html())
