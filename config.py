import os
from dotenv import load_dotenv
load_dotenv()
RACKSPACE_SPOT_BASE_URL = (
    "https://ngpc-prod-public-data.s3.us-east-2.amazonaws.com"
)

PRICE_CACHE_SECONDS = 60

REQUEST_TIMEOUT_SECONDS = 15

NEGOTIATION_ROUNDS = 4
