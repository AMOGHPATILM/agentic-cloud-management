import random


class BreachSimulator:
    """
    Simulates SLA metric changes for research/testing.

    IMPORTANT:
    This does NOT cause any real cloud infrastructure failure.
    It only changes simulated SLA measurements.
    """

    def __init__(self, seed=42):
        self.random = random.Random(seed)

    def simulate_healthy_state(self, agreement):
        """
        Generate measurements that satisfy the current SLA.
        """

        return {
            "availability": round(
                max(
                    float(agreement.get("min_availability", 98.0)) + 0.5,
                    99.0
                ),
                2
            ),
            "latency": round(
                max(
                    1.0,
                    float(agreement.get("max_latency", 100.0)) - 10
                ),
                2
            ),
            "price": float(agreement.get("price", 0.0)),
            "cpu": float(agreement.get("cpu", 0)),
            "memory": float(agreement.get("memory", 0)),
        }

    def simulate_breach(self, agreement, breach_type):
        """
        Inject one simulated SLA violation.

        The returned values are intentionally outside the
        agreed SLA constraint.
        """

        min_availability = float(
            agreement.get("min_availability", 98.0)
        )

        max_latency = float(
            agreement.get("max_latency", 100.0)
        )

        price = float(agreement.get("price", 0.0))
        cpu = float(agreement.get("cpu", 0))
        memory = float(agreement.get("memory", 0))

        measurements = self.simulate_healthy_state(agreement)

        if breach_type == "availability":
            measurements["availability"] = round(
                max(0.0, min_availability - 2.0),
                2
            )

        elif breach_type == "latency":
            measurements["latency"] = round(
                max_latency + 20.0,
                2
            )

        elif breach_type == "budget":
            measurements["price"] = round(
                price * 1.25 if price > 0 else 1.0,
                4
            )

        elif breach_type == "resource":
            measurements["cpu"] = max(
                0.0,
                cpu - 1.0
            )

            measurements["memory"] = max(
                0.0,
                memory - 4.0
            )

        return measurements