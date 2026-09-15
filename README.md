# Agentic Cloud Management - Live Rackspace Spot Pricing

This implementation adds visible agent-to-agent conversation and live Rackspace Spot pricing. Rackspace Spot documents `/percentiles.json`, `/comparable_prices.json`, and `/history/{server_class}` as unauthenticated public pricing APIs. The negotiation remains simulated: the agents do not submit or change any Rackspace contract.

Run on Windows:

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py

No API key is needed for the public pricing endpoint used by this demo. Keep any real credentials out of source control.
