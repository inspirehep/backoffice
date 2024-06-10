import requests
from os import environ
from django.http import JsonResponse
from requests.exceptions import HTTPError, RequestException

AIRFLOW_BASE_URL = environ.get('AIRFLOW_BASE_URL')

AIRFLOW_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {environ.get('AIRFLOW_TOKEN')}"
}

def trigger_airflow_dag(dag_id,workflow_id, extra_data = None):
    """ triggers an airflow dag
    :param dag_id: name of the dag to run
    :param workflow_id: id of the workflow being triggered
    :return request response"""

    data = {
        "dag_run_id": workflow_id,
        "conf":
            {
                "workflow_id": workflow_id
            }
        }

    if extra_data is not None:
        data["conf"].update(extra_data)

    url = f'{AIRFLOW_BASE_URL}/api/v1/dags/{dag_id}/dagRuns'

    try:
        response = requests.post(url, json=data, headers=AIRFLOW_HEADERS, timeout=300)
        response.raise_for_status()
        return JsonResponse(response.json())
    except HTTPError as http_err:
        return JsonResponse({'error': f'HTTP error occurred: {http_err}'}, status=response.status_code)
    except RequestException as req_err:
        return JsonResponse({'error': f'Request error occurred: {req_err}'}, status=500)