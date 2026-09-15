import time


class CustomerAgent:
    """
    Customer Agent for the simulated MAS SLA negotiation.

    BDI model:
        Beliefs    -> customer's SLA requirements
        Desires    -> low cost, good performance, availability,
                      sufficient resources, agreement
        Intentions -> evaluate, negotiate, and accept/reject offers

    IMPORTANT:
    This agent participates only in the simulated negotiation.
    No real SLA is created with Rackspace.
    """

    def __init__(self, sla_request):

        self.request = sla_request

        # -------------------------------------------------
        # BDI: BELIEFS
        # -------------------------------------------------
        self.beliefs = {
            "max_budget": sla_request.max_budget,
            "max_latency": sla_request.max_latency,
            "min_availability": sla_request.min_availability,
            "required_cpu": sla_request.required_cpu,
            "required_memory": sla_request.required_memory,
        }

        # -------------------------------------------------
        # BDI: DESIRES
        # -------------------------------------------------
        self.desires = {
            "low_cost": True,
            "good_performance": True,
            "high_availability": True,
            "sufficient_resources": True,
            "reach_agreement": True,
        }

        # -------------------------------------------------
        # BDI: INTENTIONS
        # -------------------------------------------------
        self.intentions = [
            "evaluate_offers",
            "minimize_cost",
            "satisfy_SLA",
            "negotiate",
        ]

        self.history = []

    # =====================================================
    # COMMUNICATION
    # =====================================================

    def log(self, receiver, message):

        timestamp = time.strftime("%H:%M:%S")

        print(
            f"[{timestamp}] "
            f"{'Customer Agent':<24} -> "
            f"{receiver:<24} | {message}"
        )

    # =====================================================
    # DISPLAY CUSTOMER REQUEST
    # =====================================================

    def show_request(self):

        print()
        print("=" * 72)
        print("CUSTOMER SLA REQUEST")
        print("=" * 72)

        print(
            f"Customer          : "
            f"{self.request.customer_name}"
        )

        print(
            f"Application       : "
            f"{self.request.application_type}"
        )

        print(
            f"CPU               : "
            f"{self.request.required_cpu} vCPU"
        )

        print(
            f"Memory            : "
            f"{self.request.required_memory} GB"
        )

        print(
            f"Max Budget        : "
            f"${self.request.max_budget:.4f}/hour"
        )

        print(
            f"Max Latency       : "
            f"{self.request.max_latency} ms"
        )

        print(
            f"Min Availability  : "
            f"{self.request.min_availability}%"
        )

        print(
            f"Priority          : "
            f"{self.request.priority}"
        )

        print("=" * 72)

    # =====================================================
    # BDI STATE
    # =====================================================

    def display_bdi(self):

        print()
        print("[Customer Agent] BDI STATE")

        print(
            "  Beliefs    : "
            f"budget <= ${self.request.max_budget:.4f}/hr, "
            f"latency <= {self.request.max_latency} ms, "
            f"availability >= {self.request.min_availability}%"
        )

        print(
            "  Desires    : "
            "low cost + performance + availability"
        )

        print(
            "  Intentions : "
            "evaluate + negotiate + reach agreement"
        )

    # =====================================================
    # HARD CONSTRAINT CHECK
    # =====================================================

    def check_constraints(
        self,
        price,
        latency,
        availability,
        cpu,
        memory,
    ):
        """
        Check whether an offer satisfies all mandatory
        customer requirements.

        These are HARD constraints.

        No utility threshold is used here.
        """

        budget_ok = (
            price <= self.request.max_budget
        )

        latency_ok = (
            latency <= self.request.max_latency
        )

        availability_ok = (
            availability >=
            self.request.min_availability
        )

        cpu_ok = (
            cpu >= self.request.required_cpu
        )

        memory_ok = (
            memory >= self.request.required_memory
        )

        feasible = (
            budget_ok
            and latency_ok
            and availability_ok
            and cpu_ok
            and memory_ok
        )

        return {
            "feasible": feasible,
            "budget": budget_ok,
            "latency": latency_ok,
            "availability": availability_ok,
            "cpu": cpu_ok,
            "memory": memory_ok,
        }

    # =====================================================
    # OFFER EVALUATION
    # =====================================================

    def evaluate_offer(
        self,
        offer,
        quoted_price=None
    ):
        """
        Evaluate an offer.

        Utility calculation is delegated to the project's
        central UtilityEngine so that every agent uses the
        same fixed experimental weights.

        This method is kept compatible with the existing
        offer structure used by the project.
        """

        if quoted_price is None:
            quoted_price = offer.price_per_hour

        constraints = self.check_constraints(
            price=quoted_price,
            latency=offer.latency_estimate_ms,
            availability=offer.availability_estimate,
            cpu=offer.cpu,
            memory=offer.memory_gb,
        )

        # Import here to avoid unnecessary circular imports.
        from negotiation.utility import UtilityEngine

        engine = UtilityEngine()

        utility_result = engine.calculate_utility(
            offer={
                "market_price": quoted_price,
                "cpu": offer.cpu,
                "memory": offer.memory_gb,
                "latency": offer.latency_estimate_ms,
                "availability": offer.availability_estimate,
            },
            max_budget=self.request.max_budget,
            max_latency=self.request.max_latency,
            min_availability=self.request.min_availability,
            required_cpu=self.request.required_cpu,
            required_memory=self.request.required_memory,
        )

        self.history.append({
            "price": quoted_price,
            "utility": utility_result["utility"],
            "feasible": constraints["feasible"],
            "constraints": constraints,
        })

        return (
            utility_result["utility"],
            utility_result["components"],
            constraints,
        )

    # =====================================================
    # DECISION
    # =====================================================

    def decide(
        self,
        utility,
        quoted_price,
        feasible=True,
        final_round=False
    ):
        """
        Decide what the Customer Agent should do.

        IMPORTANT:
        There is NO hard-coded utility >= 0.92 acceptance
        threshold anymore.

        Feasibility comes first.

        If the offer is feasible:
            - accept if final/negotiation conditions are met
            - otherwise continue negotiating

        If infeasible:
            - counter or reject depending on negotiation state
        """

        if not feasible:

            if final_round:
                return "REJECT"

            return "COUNTER"

        # A feasible offer can be accepted.
        if final_round:
            return "ACCEPT"

        # During negotiation, continue if there is room
        # for improvement.
        if quoted_price > (
            self.request.max_budget * 0.90
        ):
            return "COUNTER"

        return "ACCEPT"

    # =====================================================
    # CUSTOMER COUNTER OFFER
    # =====================================================

    def counter_price(
        self,
        current_price,
        market_price,
        round_number,
        provider_reservation=None,
    ):
        """
        Generate a customer counter-offer.

        The customer gradually moves toward the provider's
        market price while never intentionally exceeding the
        customer's maximum budget.
        """

        max_budget = self.request.max_budget

        # Customer's target moves toward market price.
        target_price = max(
            market_price,
            max_budget * 0.25
        )

        target_price = min(
            target_price,
            max_budget
        )

        # Progressive concession.
        concession = min(
            0.80,
            0.20 * round_number
        )

        new_price = (
            current_price * (1 - concession)
            +
            target_price * concession
        )

        # Prevent an accidental increase.
        if new_price >= current_price:
            new_price = current_price * 0.95

        # Never exceed budget.
        new_price = min(
            new_price,
            max_budget
        )

        # Do not go below market price.
        new_price = max(
            market_price,
            new_price
        )

        return round(new_price, 4)

    # =====================================================
    # NEGOTIATION MESSAGE
    # =====================================================

    def send_offer(
        self,
        receiver,
        price,
        round_number
    ):

        self.log(
            receiver,
            f"Round {round_number}: "
            f"Customer proposes ${price:.4f}/hr"
        )