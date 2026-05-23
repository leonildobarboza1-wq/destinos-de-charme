import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

def get_blogger_service():
    credentials_info = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])

    credentials = Credentials.from_authorized_user_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/blogger"]
    )

    credentials.refresh(Request())

    service = build(
        "blogger",
        "v3",
        credentials=credentials
    )

    return service

service = get_blogger_service()

blogs = service.blogs().listByUser(userId="self").execute()

print("\nBLOGS ENCONTRADOS:\n")
print(json.dumps(blogs, indent=2, ensure_ascii=False))
