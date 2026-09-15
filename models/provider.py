from dataclasses import dataclass
@dataclass
class ProviderOffer:

    def __init__(
        self,
        offer_id,
        agent_name,
        server_class,
        region,
        cpu,
        memory_gb,
        price_per_hour,
        availability_estimate,
        latency_estimate_ms,
    ):

        self.offer_id = offer_id
        self.agent_name = agent_name
        self.server_class = server_class
        self.region = region
        self.cpu = cpu
        self.memory_gb = memory_gb
        self.price_per_hour = price_per_hour
        self.availability_estimate = availability_estimate
        self.latency_estimate_ms = latency_estimate_ms