import google.auth.transport.requests
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    ".firebase-credentials.json",
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)
request = google.auth.transport.requests.Request()
credentials.refresh(request)
print(credentials.token)
