class UtilityEngine:
    """
    Fixed-weight utility engine for the simulated SLA negotiation.

    Hard constraints are handled separately.
    Utility is used only to rank feasible provider offers.

    Fixed weights:
        Cost         = 0.40
        Resources    = 0.25
        Latency      = 0.20
        Availability = 0.15
    """

    COST_WEIGHT = 0.40
    RESOURCE_WEIGHT = 0.25
    LATENCY_WEIGHT = 0.20
    AVAILABILITY_WEIGHT = 0.15

    def calculate_utility(
        self,
        offer,
        max_budget,
        max_latency,
        min_availability,
        required_cpu,
        required_memory
    ):
        """
        Calculate utility for a provider offer.

        Returns:
            {
                "utility": float,
                "components": dict,
                "feasible": bool,
                "constraints": dict
            }
        """

        price = float(offer.get("market_price", 0))
        cpu = float(offer.get("cpu", 0))
        memory = float(offer.get("memory", 0))

        # ---------------------------------------------------------
        # Simulated SLA attributes
        # ---------------------------------------------------------
        #
        # Rackspace public pricing provides price/resources.
        # Latency and availability are simulated research values.
        #
        # They are intentionally kept separate from the real
        # Rackspace market-price data.
        # ---------------------------------------------------------

        latency = float(
            offer.get("latency", max_latency)
        )

        availability = float(
            offer.get("availability", min_availability)
        )

        # ---------------------------------------------------------
        # HARD CONSTRAINTS
        # ---------------------------------------------------------

        budget_ok = price <= max_budget
        latency_ok = latency <= max_latency
        availability_ok = availability >= min_availability
        cpu_ok = cpu >= required_cpu
        memory_ok = memory >= required_memory

        feasible = (
            budget_ok
            and latency_ok
            and availability_ok
            and cpu_ok
            and memory_ok
        )

        # ---------------------------------------------------------
        # COST UTILITY
        # Cheaper price = higher utility.
        # ---------------------------------------------------------

        if max_budget <= 0:
            cost_utility = 0.0
        else:
            cost_utility = max(
                0.0,
                min(
                    1.0,
                    1.0 - (price / max_budget)
                )
            )

        # ---------------------------------------------------------
        # RESOURCE UTILITY
        # Prefer offers that satisfy requirements without
        # unnecessarily excessive resources.
        # ---------------------------------------------------------

        cpu_ratio = (
            cpu / required_cpu
            if required_cpu > 0
            else 1.0
        )

        memory_ratio = (
            memory / required_memory
            if required_memory > 0
            else 1.0
        )

        cpu_score = min(cpu_ratio, 2.0) / 2.0
        memory_score = min(memory_ratio, 2.0) / 2.0

        resource_utility = (
            cpu_score + memory_score
        ) / 2.0

        # ---------------------------------------------------------
        # LATENCY UTILITY
        # Lower latency = higher utility.
        # ---------------------------------------------------------

        if max_latency <= 0:
            latency_utility = 0.0
        else:
            latency_utility = max(
                0.0,
                min(
                    1.0,
                    1.0 - (latency / max_latency)
                )
            )

        # ---------------------------------------------------------
        # AVAILABILITY UTILITY
        # Higher availability = higher utility.
        # ---------------------------------------------------------

        availability_utility = max(
            0.0,
            min(
                1.0,
                availability / 100.0
            )
        )

        # ---------------------------------------------------------
        # FINAL WEIGHTED UTILITY
        # ---------------------------------------------------------

        utility = (
            self.COST_WEIGHT * cost_utility
            + self.RESOURCE_WEIGHT * resource_utility
            + self.LATENCY_WEIGHT * latency_utility
            + self.AVAILABILITY_WEIGHT * availability_utility
        )

        return {
            "utility": round(utility, 4),

            "components": {
                "cost": round(cost_utility, 4),
                "resources": round(resource_utility, 4),
                "latency": round(latency_utility, 4),
                "availability": round(availability_utility, 4),
            },

            "feasible": feasible,

            "constraints": {
                "budget": budget_ok,
                "latency": latency_ok,
                "availability": availability_ok,
                "cpu": cpu_ok,
                "memory": memory_ok,
            },

            "values": {
                "price": price,
                "cpu": cpu,
                "memory": memory,
                "latency": latency,
                "availability": availability,
            }
        }


def calculate_utility(
    offer,
    max_budget,
    max_latency,
    min_availability,
    required_cpu,
    required_memory
):
    """
    Convenience function so existing project code can also use:

        calculate_utility(...)
    """

    engine = UtilityEngine()

    return engine.calculate_utility(
        offer=offer,
        max_budget=max_budget,
        max_latency=max_latency,
        min_availability=min_availability,
        required_cpu=required_cpu,
        required_memory=required_memory
    )