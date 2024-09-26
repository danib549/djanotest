import requests
from requests.auth import HTTPBasicAuth

# Replace with your Jira instance URL, credentials, and endpoint
jira_url = "https://danibarma1.atlassian.net/rest/raven/1.0/api/test/ATATT3xFfGF0QweXafyDUO2odK9vsXGMgM8nIeewsYwx1Q9y-Py_Hugvm-iqQc1PNd4zzl7h0mE77lGGwIQGuoyNwwe0OXhmGZsVEf3B3R065lB5SnwHXheztv9x8baMsdlgN4BC89GDYQK7Pqi_LiZxsCS9L8yTfrFN8eeo0fLU2hpEBzLM25U=A7705387/step"

# Replace with your Jira username and API token
username = "admin"
api_token = "admin"

# Set verify to False if you want to skip SSL verification (NOT recommended for production)
verify_ssl = False  # Set to True in production

def test_xray_api():
    try:
        # Perform the GET request
        response = requests.get(jira_url, auth=HTTPBasicAuth(username, api_token), verify=verify_ssl)

        # Check for HTTP errors
        if response.status_code == 200:
            print("Connection successful!")
            print("Response JSON:", response.json())
        else:
            print(f"Failed to connect. Status Code: {response.status_code}")
            print("Response:", response.text)

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")

if __name__ == "__main__":
    test_xray_api()
