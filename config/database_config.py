import os
from dotenv import load_dotenv
from urllib.parse import quote
load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB", "aep")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_SSLMODE = os.getenv("POSTGRES_SSLMODE", "disable")



if not POSTGRES_USER or not POSTGRES_PASSWORD:
    raise ValueError(
        "POSTGRES_USER and POSTGRES_PASSWORD must be configured."
    )

# Encode credentials to handle special characters safely.
encoded_user = quote(POSTGRES_USER, safe="")
encoded_password = quote(POSTGRES_PASSWORD, safe="")

DB_URI = (
    f"postgresql://{encoded_user}:{encoded_password}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    f"?sslmode={POSTGRES_SSLMODE}"
)