import requests
import re


class RackspaceSpotClient:
    """
    Fetches public Rackspace Spot market pricing.

    IMPORTANT:
    This client only reads publicly available market pricing.
    It does NOT create, modify, or manage a real Rackspace SLA.
    """

    PRICING_URL = (
        "https://ngpc-prod-public-data.s3.us-east-2.amazonaws.com/"
        "percentiles.json"
    )

    def __init__(self):
        self.offers = []

    def fetch_pricing(self):
        """
        Fetch and parse the complete Rackspace public pricing dataset.
        """

        print()
        print("=" * 72)
        print("FETCHING LIVE RACKSPACE SPOT PRICING")
        print("=" * 72)
        print("Source: Rackspace Spot public market pricing")
        print()
        print(f"Connecting to: {self.PRICING_URL}")
        print()

        try:
            response = requests.get(
                self.PRICING_URL,
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

        except requests.RequestException as e:
            print(f"ERROR: Could not retrieve Rackspace pricing: {e}")
            return []

        except ValueError as e:
            print(f"ERROR: Rackspace response is not valid JSON: {e}")
            return []

        regions = data.get("regions", {})

        if not isinstance(regions, dict):
            print("ERROR: 'regions' field has unexpected format.")
            return []

        parsed_offers = []

        for region_name, region_data in regions.items():

            if not isinstance(region_data, dict):
                continue

            serverclasses = region_data.get("serverclasses", {})

            if not isinstance(serverclasses, dict):
                continue

            for server_class, details in serverclasses.items():

                if not isinstance(details, dict):
                    continue

                try:
                    cpu = float(details.get("cpu", 0))

                    memory_raw = str(
                        details.get("memory", "0")
                    )

                    memory_match = re.search(
                        r"[\d.]+",
                        memory_raw
                    )

                    if not memory_match:
                        continue

                    memory = float(memory_match.group())

                    market_price = float(
                        details.get("market_price", 0)
                    )

                    ondemand_price = float(
                        details.get("ondemand_price", 0)
                    )

                except (TypeError, ValueError):
                    continue

                if cpu <= 0 or memory <= 0:
                    continue

                if market_price < 0:
                    continue

                offer = {
                    "server_class": server_class,
                    "region": region_name,
                    "cpu": cpu,
                    "memory": memory,
                    "market_price": market_price,
                    "ondemand_price": ondemand_price,
                    "display_name": details.get(
                        "display_name",
                        server_class
                    ),
                    "category": details.get(
                        "category",
                        "Unknown"
                    ),
                    "description": details.get(
                        "description",
                        ""
                    ),
                    "generation": region_data.get(
                        "generation",
                        ""
                    ),
                }

                parsed_offers.append(offer)

        self.offers = parsed_offers

        print(
            f"Successfully retrieved "
            f"{len(parsed_offers)} live pricing records."
        )

        return parsed_offers

    def get_offers(self, required_cpu, required_memory):
        """
        Return live offers that satisfy the minimum CPU
        and memory requirements.
        """

        all_offers = self.fetch_pricing()

        feasible_offers = []

        for offer in all_offers:

            if offer["cpu"] >= required_cpu and \
               offer["memory"] >= required_memory:

                feasible_offers.append(offer)

        return feasible_offers

    def get_all_offers(self):
        """
        Return every parsed live Rackspace Spot offer.
        """

        if not self.offers:
            return self.fetch_pricing()

        return self.offers