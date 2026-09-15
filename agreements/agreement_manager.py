import json
from pathlib import Path
from datetime import datetime


class AgreementManager:
    """
    Manages persistence of simulated SLA agreements.

    IMPORTANT:
    These agreements are research/simulation artifacts only.
    No real Rackspace SLA is created, modified, or accepted.
    """

    def __init__(self, directory="agreements"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    # ============================================================
    # AGREEMENT ID
    # ============================================================

    def get_next_agreement_id(self):
        """
        Generate the next agreement ID.

        Example:
            SLA-001
            SLA-002
            SLA-003
        """

        existing = list(self.directory.glob("SLA-*.json"))

        numbers = []

        for file in existing:
            try:
                number = int(
                    file.stem.replace("SLA-", "")
                )
                numbers.append(number)
            except ValueError:
                continue

        next_number = max(numbers) + 1 if numbers else 1

        return f"SLA-{next_number:03d}"

    # ============================================================
    # CREATE AGREEMENT
    # ============================================================

    def create_agreement(self, agreement, request):
        """
        Convert the negotiated agreement into a
        persistent JSON-compatible dictionary.
        """

        provider = agreement["provider"]

        # provider.offer is a DICTIONARY in the current project
        offer = provider.offer

        agreement_id = self.get_next_agreement_id()

        # --------------------------------------------------------
        # Safely retrieve offer values
        # --------------------------------------------------------

        server_class = offer.get(
            "server_class",
            "Unknown"
        )

        region = offer.get(
            "region",
            "Unknown"
        )

        cpu = float(
            offer.get("cpu", 0)
        )

        memory = float(
            offer.get("memory", 0)
        )

        market_price = float(
            offer.get("market_price", 0)
        )

        latency = float(
            offer.get(
                "latency",
                request.max_latency
            )
        )

        availability = float(
            offer.get(
                "availability",
                request.min_availability
            )
        )

        # --------------------------------------------------------
        # Provider Agent ID
        # --------------------------------------------------------

        provider_agent_id = getattr(
            provider,
            "agent_id",
            "Unknown Provider Agent"
        )

        # --------------------------------------------------------
        # Create agreement data
        # --------------------------------------------------------

        data = {
            "agreement_id": agreement_id,

            "agreement_type": "SIMULATED_SLA",

            "status": "ACTIVE",

            "created_at": datetime.now().isoformat(),

            "version": 1,

            "simulation_notice": (
                "This is a simulated research agreement. "
                "No real Rackspace SLA was created, "
                "modified, or accepted."
            ),

            # ====================================================
            # CUSTOMER
            # ====================================================

            "customer": {
                "name": request.customer_name,

                "application_type": request.application_type,

                "requirements": {
                    "cpu": request.required_cpu,

                    "memory_gb": request.required_memory,

                    "max_budget_per_hour": request.max_budget,

                    "max_latency_ms": request.max_latency,

                    "min_availability_percent":
                        request.min_availability,

                    "priority": request.priority
                }
            },

            # ====================================================
            # PROVIDER
            # ====================================================

            "provider": {
                "agent_id": provider_agent_id,

                "server_class": server_class,

                "region": region,

                "cpu": cpu,

                "memory_gb": memory
            },

            # ====================================================
            # AGREEMENT TERMS
            # ====================================================

            "agreement_terms": {

                "agreed_price_per_hour":
                    float(agreement["price"]),

                "market_reference_price_per_hour":
                    market_price,

                "latency_ms":
                    latency,

                "availability_percent":
                    availability
            },

            # ====================================================
            # NEGOTIATION INFORMATION
            # ====================================================

            "negotiation": {

                "round":
                    agreement["round"],

                "utility":
                    float(agreement["utility"]),

                "status":
                    agreement["status"]
            },

            # ====================================================
            # HISTORY
            # ====================================================

            "history": []
        }

        return data

    # ============================================================
    # SAVE JSON
    # ============================================================

    def save_json(self, data):
        """
        Save agreement as JSON.

        Example:
            agreements/SLA-001.json
        """

        agreement_id = data["agreement_id"]

        path = self.directory / f"{agreement_id}.json"

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4
            )

        return path

    # ============================================================
    # SAVE MARKDOWN
    # ============================================================

    def save_markdown(self, data):
        """
        Save agreement as Markdown.

        Markdown can be opened/imported easily in
        knowledge-management applications such as Anytype.
        """

        agreement_id = data["agreement_id"]

        path = self.directory / f"{agreement_id}.md"

        customer = data["customer"]

        provider = data["provider"]

        terms = data["agreement_terms"]

        negotiation = data["negotiation"]

        content = f"""# {agreement_id}

# Simulated SLA Agreement

> **Research Simulation**
>
> This document represents a simulated SLA agreement generated by the
> Agentic Cloud Management Multi-Agent System.
>
> **No real Rackspace SLA was created, modified, or accepted.**

---

## Agreement Information

- **Agreement ID:** {agreement_id}
- **Agreement Type:** {data["agreement_type"]}
- **Status:** {data["status"]}
- **Version:** {data["version"]}
- **Created:** {data["created_at"]}

---

## Customer

- **Customer Name:** {customer["name"]}
- **Application Type:** {customer["application_type"]}

### Customer Requirements

| Requirement | Value |
|---|---:|
| CPU | {customer["requirements"]["cpu"]} vCPU |
| Memory | {customer["requirements"]["memory_gb"]} GB |
| Maximum Budget | ${customer["requirements"]["max_budget_per_hour"]:.4f}/hour |
| Maximum Latency | {customer["requirements"]["max_latency_ms"]} ms |
| Minimum Availability | {customer["requirements"]["min_availability_percent"]}% |
| Priority | {customer["requirements"]["priority"]} |

---

## Provider

- **Provider Agent:** {provider["agent_id"]}
- **Server Class:** {provider["server_class"]}
- **Region:** {provider["region"]}
- **CPU:** {provider["cpu"]} vCPU
- **Memory:** {provider["memory_gb"]} GB

---

## Agreement Terms

| Term | Agreed Value |
|---|---:|
| Agreed Price | ${terms["agreed_price_per_hour"]:.4f}/hour |
| Market Reference Price | ${terms["market_reference_price_per_hour"]:.4f}/hour |
| Simulated Latency | {terms["latency_ms"]:.2f} ms |
| Simulated Availability | {terms["availability_percent"]:.2f}% |

---

## Negotiation

- **Negotiation Round:** {negotiation["round"]}
- **Utility Score:** {negotiation["utility"]:.4f}
- **Status:** {negotiation["status"]}

---

## BDI-Based Decision

The agreement was produced through the simulated multi-agent negotiation
process.

### Customer Agent

- **Beliefs:** Customer requirements and constraints
- **Desires:** Low cost, sufficient resources, performance and availability
- **Intentions:** Evaluate offers, negotiate and reach agreement

### Provider Agent

- **Beliefs:** Market price, available resources and provider configuration
- **Desires:** Satisfy customer requirements and reach agreement
- **Intentions:** Negotiate, counter-offer and accept feasible proposals

### Negotiation Manager

- Ranked feasible provider offers using the fixed utility model.
- Selected the highest-utility feasible provider.
- Coordinated multi-round negotiation.
- Verified the negotiated agreement.
- Created this simulated SLA artifact.

---

## Utility Model

The project uses fixed utility weights:

| Utility Component | Weight |
|---|---:|
| Cost | 0.40 |
| Resources | 0.25 |
| Latency | 0.20 |
| Availability | 0.15 |

These weights are fixed for all simulated customers.

---

## Agreement History

No SLA breach or renegotiation has occurred yet.

Future simulation stages may append:

1. SLA monitoring event
2. SLA breach event
3. Breach detection
4. Provider response
5. Customer response
6. Renegotiation
7. New SLA version

---

## Simulation Notice

This agreement is a **simulation artifact for academic research**.

It does not represent:

- A real Rackspace contract
- A real Rackspace SLA
- A real cloud-resource reservation
- A real cloud-service purchase
- A real modification to Rackspace infrastructure

---
"""

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(content)

        return path

    # ============================================================
    # SAVE AGREEMENT
    # ============================================================

    def save_agreement(self, agreement, request):
        """
        Create and save both JSON and Markdown versions.
        """

        data = self.create_agreement(
            agreement,
            request
        )

        json_path = self.save_json(
            data
        )

        md_path = self.save_markdown(
            data
        )

        print()

        print("=" * 72)
        print("SIMULATED SLA AGREEMENT SAVED")
        print("=" * 72)

        print(
            f"Agreement ID : {data['agreement_id']}"
        )

        print(
            f"JSON File    : {json_path}"
        )

        print(
            f"Markdown File: {md_path}"
        )

        print(
            f"Status       : {data['status']}"
        )

        print(
            f"Version      : {data['version']}"
        )

        print()

        print(
            "This agreement is a simulation artifact only."
        )

        print("=" * 72)

        return data

    # ============================================================
    # LOAD AGREEMENT
    # ============================================================

    def load_agreement(self, agreement_id):
        """
        Load an existing agreement from JSON.
        """

        path = self.directory / f"{agreement_id}.json"

        if not path.exists():
            return None

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    # ============================================================
    # LIST AGREEMENTS
    # ============================================================

    def list_agreements(self):
        """
        Return all saved SLA agreement JSON files.
        """

        return sorted(
            self.directory.glob("SLA-*.json")
        )

    # ============================================================
    # CHECK AGREEMENT EXISTS
    # ============================================================

    def agreement_exists(self, agreement_id):
        """
        Check whether an agreement exists.
        """

        path = self.directory / f"{agreement_id}.json"

        return path.exists()

    # ============================================================
    # UPDATE AGREEMENT
    # ============================================================

    def update_agreement(self, data):
        """
        Update an existing agreement JSON file.

        Used later for breach detection and renegotiation.
        """

        agreement_id = data["agreement_id"]

        path = self.directory / f"{agreement_id}.json"

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4
            )

        return path

    # ============================================================
    # ADD HISTORY EVENT
    # ============================================================

    def add_history_event(
        self,
        agreement_id,
        event
    ):
        """
        Append a history event to an agreement.

        This will be used later for:
            - monitoring
            - SLA breach
            - detection
            - renegotiation
            - versioning
        """

        data = self.load_agreement(
            agreement_id
        )

        if data is None:
            return None

        if "history" not in data:
            data["history"] = []

        data["history"].append(
            event
        )

        data["updated_at"] = datetime.now().isoformat()

        self.update_agreement(
            data
        )

        return data