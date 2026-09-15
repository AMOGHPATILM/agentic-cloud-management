import time


class ProviderAgent:
    """
    Simulated Provider Agent.

    The agent represents a provider offer derived from
    live Rackspace Spot market pricing.

    BDI model:
        Beliefs    -> current SLA request, market price, resources
        Desires    -> satisfy requirements and maximize agreement
        Intentions -> make/counter/accept an offer

    IMPORTANT:
    This agent does NOT negotiate with Rackspace.
    Negotiation is entirely simulated for research purposes.
    """

    def __init__(self, agent_id, offer):

        self.agent_id = agent_id
        self.offer = offer

        # -----------------------------
        # BDI: BELIEFS
        # -----------------------------
        self.beliefs = {
            "market_price": float(
                offer.get("market_price", 0)
            ),
            "cpu": float(
                offer.get("cpu", 0)
            ),
            "memory": float(
                offer.get("memory", 0)
            ),
            "region": offer.get("region", "Unknown"),
            "server_class": offer.get(
                "server_class",
                "Unknown"
            ),
        }

        # -----------------------------
        # BDI: DESIRES
        # -----------------------------
        self.desires = {
            "satisfy_customer": True,
            "reach_agreement": True,
            "protect_market_value": True,
        }

        # -----------------------------
        # BDI: INTENTIONS
        # -----------------------------
        self.intentions = {
            "negotiate": True,
            "counter_offer": True,
            "accept_feasible_offer": True,
        }

        self.round_history = []

    def get_initial_offer(self):
        """
        Return the initial simulated provider offer.
        """

        price = self.beliefs["market_price"]

        return {
            "price": round(price, 4),
            "cpu": self.beliefs["cpu"],
            "memory": self.beliefs["memory"],
            "region": self.beliefs["region"],
            "server_class": self.beliefs["server_class"],
        }

    def calculate_counter_offer(
        self,
        customer_price,
        round_number,
        max_rounds=5
    ):
        """
        Generate a simulated provider counter-offer.

        The provider gradually moves toward the customer's
        requested price while protecting its market price.

        This is a simulated negotiation strategy.
        """

        market_price = self.beliefs["market_price"]

        # Provider's minimum acceptable simulated price.
        #
        # We allow the provider to negotiate down to 90%
        # of the live market price.
        minimum_price = market_price * 0.90

        # Progress increases with each round.
        progress = round_number / max_rounds

        # Move gradually from market price toward
        # customer's requested price.
        target_price = (
            market_price
            - (
                (market_price - customer_price)
                * progress
            )
        )

        counter_price = max(
            minimum_price,
            target_price
        )

        counter_price = round(
            counter_price,
            4
        )

        self.round_history.append({
            "round": round_number,
            "customer_price": round(
                customer_price,
                4
            ),
            "provider_price": counter_price,
        })

        return {
            "price": counter_price,
            "round": round_number,
            "agent_id": self.agent_id,
        }

    def evaluate_customer_offer(
        self,
        customer_price,
        round_number,
        max_rounds=5
    ):
        """
        Evaluate a customer's simulated price proposal.

        Returns:
            ACCEPT or COUNTER
        """

        market_price = self.beliefs["market_price"]

        minimum_price = market_price * 0.90

        if customer_price >= minimum_price:

            return {
                "decision": "ACCEPT",
                "price": round(
                    customer_price,
                    4
                ),
                "round": round_number,
            }

        counter = self.calculate_counter_offer(
            customer_price,
            round_number,
            max_rounds
        )

        return {
            "decision": "COUNTER",
            "price": counter["price"],
            "round": round_number,
        }

    def display_bdi(self):

        print()
        print(
            f"[{self.agent_id}] BDI STATE"
        )

        print(
            f"  Beliefs    : "
            f"market=${self.beliefs['market_price']:.4f}/hr, "
            f"CPU={self.beliefs['cpu']:.0f}, "
            f"Memory={self.beliefs['memory']:.0f} GB"
        )

        print(
            f"  Desires    : "
            f"satisfy customer + reach agreement"
        )

        print(
            f"  Intentions : "
            f"negotiate + counter-offer + accept"
        )

    def display_offer(self, offer, label="OFFER"):

        print(
            f"[{self.agent_id}] {label}: "
            f"${offer['price']:.4f}/hr"
        )

        time.sleep(0.2)