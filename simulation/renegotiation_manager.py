from datetime import datetime
from pathlib import Path
import json


class RenegotiationManager:
    """
    Controls the simulated SLA renegotiation lifecycle.

    IMPORTANT:
    This does not modify a real cloud provider SLA.

    It creates a new simulated agreement version while preserving
    the original agreement.
    """

    def __init__(self, agreements_directory="agreements"):
        self.directory = Path(
            agreements_directory
        )

        self.directory.mkdir(
            parents=True,
            exist_ok=True
        )

    # ============================================================
    # FIND NEXT VERSION
    # ============================================================

    def get_next_version(
        self,
        agreement_id
    ):
        """
        Determine the next version number.

        Example:

            SLA-001.json
            version = 1

            after renegotiation:

            SLA-002.json
            version = 2
        """

        files = list(
            self.directory.glob("SLA-*.json")
        )

        highest = 1

        for file in files:

            try:

                with open(
                    file,
                    "r",
                    encoding="utf-8"
                ) as f:

                    data = json.load(f)

                version = int(
                    data.get(
                        "version",
                        1
                    )
                )

                highest = max(
                    highest,
                    version
                )

            except (
                OSError,
                ValueError,
                json.JSONDecodeError
            ):

                continue

        return highest + 1

    # ============================================================
    # DISPLAY BREACH
    # ============================================================

    def display_breach_notification(
        self,
        agreement,
        breach_result
    ):

        print()
        print("=" * 72)
        print("AGENTIC SLA BREACH RESPONSE")
        print("=" * 72)

        print(
            f"Agreement : "
            f"{agreement['agreement_id']}"
        )

        print(
            f"Breach    : "
            f"{breach_result['breach_type']}"
        )

        print(
            f"Severity  : "
            f"{breach_result['severity']}"
        )

        print("=" * 72)

        print()

        print(
            "[SLA MONITOR] "
            "Breach detected."
        )

        print(
            "[SLA MONITOR] "
            "Notifying Customer Agent."
        )

        print(
            "[Customer Agent] "
            "SLA violation received."
        )

        print(
            "[Customer Agent] "
            "Requesting Negotiation Manager intervention."
        )

        print(
            "[Negotiation Manager] "
            "Initiating simulated renegotiation."
        )

        print(
            "[Negotiation Manager] "
            "Contacting Provider Agent."
        )

        print(
            "[Provider Agent] "
            "Breach acknowledged in simulation."
        )

    # ============================================================
    # CREATE RENEGOTIATED AGREEMENT
    # ============================================================

    def create_renegotiated_agreement(
        self,
        agreement,
        breach_result
    ):
        """
        Create a new simulated SLA agreement version.

        The original agreement is never overwritten.
        """

        old_id = agreement[
            "agreement_id"
        ]

        old_version = int(
            agreement.get(
                "version",
                1
            )
        )

        new_version = old_version + 1

        # --------------------------------------------------------
        # New agreement ID
        # --------------------------------------------------------

        number = old_id.replace(
            "SLA-",
            ""
        )

        try:
            numeric_id = int(number)

        except ValueError:
            numeric_id = 1

        new_id = f"SLA-{numeric_id + 1:03d}"

        # --------------------------------------------------------
        # Deep copy using JSON
        # --------------------------------------------------------

        new_agreement = json.loads(
            json.dumps(agreement)
        )

        # --------------------------------------------------------
        # Update metadata
        # --------------------------------------------------------

        new_agreement[
            "agreement_id"
        ] = new_id

        new_agreement[
            "version"
        ] = new_version

        new_agreement[
            "status"
        ] = "ACTIVE"

        new_agreement[
            "created_at"
        ] = datetime.now().isoformat()

        new_agreement[
            "previous_agreement_id"
        ] = old_id

        new_agreement[
            "renegotiation"
        ] = {
            "trigger": "SLA_BREACH",

            "breach_type":
                breach_result[
                    "breach_type"
                ],

            "severity":
                breach_result[
                    "severity"
                ],

            "timestamp":
                datetime.now().isoformat(),

            "previous_version":
                old_version,

            "new_version":
                new_version,

            "reason":
                "Automatic simulated SLA renegotiation"
        }

        # --------------------------------------------------------
        # Adapt terms after breach
        # --------------------------------------------------------

        terms = new_agreement[
            "agreement_terms"
        ]

        breach_type = (
            breach_result[
                "breach_type"
            ]
            or ""
        ).upper()

        if breach_type == "AVAILABILITY":

            old_availability = float(
                terms[
                    "availability_percent"
                ]
            )

            terms[
                "availability_percent"
            ] = min(
                99.99,
                old_availability + 1.0
            )

        elif breach_type == "LATENCY":

            old_latency = float(
                terms["latency_ms"]
            )

            terms[
                "latency_ms"
            ] = max(
                1.0,
                old_latency - 5.0
            )

        elif breach_type == "PRICE":

            old_price = float(
                terms[
                    "agreed_price_per_hour"
                ]
            )

            terms[
                "agreed_price_per_hour"
            ] = round(
                old_price,
                4
            )

        elif breach_type == "CPU":

            provider = new_agreement[
                "provider"
            ]

            provider[
                "cpu"
            ] = max(
                provider["cpu"],
                new_agreement[
                    "customer"
                ][
                    "requirements"
                ][
                    "cpu"
                ]
            )

        elif breach_type == "MEMORY":

            provider = new_agreement[
                "provider"
            ]

            provider[
                "memory_gb"
            ] = max(
                provider["memory_gb"],
                new_agreement[
                    "customer"
                ][
                    "requirements"
                ][
                    "memory_gb"
                ]
            )

        # --------------------------------------------------------
        # Update negotiation information
        # --------------------------------------------------------

        old_utility = float(
            new_agreement[
                "negotiation"
            ].get(
                "utility",
                0
            )
        )

        new_agreement[
            "negotiation"
        ] = {
            "round":
                new_agreement[
                    "negotiation"
                ].get(
                    "round",
                    0
                ),

            "utility":
                old_utility,

            "status":
                "RENEGOTIATED",

            "trigger":
                "SLA_BREACH"
        }

        # --------------------------------------------------------
        # Add history
        # --------------------------------------------------------

        if "history" not in new_agreement:

            new_agreement[
                "history"
            ] = []

        new_agreement[
            "history"
        ].append({
            "timestamp":
                datetime.now().isoformat(),

            "event":
                "SLA_BREACH_DETECTED",

            "breach_type":
                breach_result[
                    "breach_type"
                ],

            "severity":
                breach_result[
                    "severity"
                ],

            "previous_agreement":
                old_id
        })

        new_agreement[
            "history"
        ].append({
            "timestamp":
                datetime.now().isoformat(),

            "event":
                "RENEGOTIATION_COMPLETED",

            "previous_version":
                old_version,

            "new_version":
                new_version,

            "status":
                "RENEGOTIATED"
        })

        return new_agreement

    # ============================================================
    # SAVE JSON
    # ============================================================

    def save_json(
        self,
        agreement
    ):

        path = (
            self.directory
            / f"{agreement['agreement_id']}.json"
        )

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                agreement,
                file,
                indent=4
            )

        return path

    # ============================================================
    # SAVE MARKDOWN
    # ============================================================

    def save_markdown(
        self,
        agreement
    ):

        agreement_id = agreement[
            "agreement_id"
        ]

        path = (
            self.directory
            / f"{agreement_id}.md"
        )

        customer = agreement[
            "customer"
        ]

        provider = agreement[
            "provider"
        ]

        terms = agreement[
            "agreement_terms"
        ]

        negotiation = agreement[
            "negotiation"
        ]

        renegotiation = agreement.get(
            "renegotiation",
            {}
        )

        history = agreement.get(
            "history",
            []
        )

        content = f"""# {agreement_id}

# Simulated SLA Agreement

> **Research Simulation**
>
> This agreement is generated by the Agentic Cloud Management
> Multi-Agent System.
>
> No real cloud SLA was created or modified.

---

## Agreement Information

- **Agreement ID:** {agreement_id}
- **Agreement Type:** {agreement.get("agreement_type", "SIMULATED_SLA")}
- **Status:** {agreement.get("status", "ACTIVE")}
- **Version:** {agreement.get("version", 1)}
- **Previous Agreement:** {agreement.get("previous_agreement_id", "None")}
- **Created:** {agreement.get("created_at", "")}

---

## Customer

- **Name:** {customer["name"]}
- **Application:** {customer["application_type"]}

### Requirements

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

| Term | Value |
|---|---:|
| Agreed Price | ${terms["agreed_price_per_hour"]:.4f}/hour |
| Market Reference Price | ${terms["market_reference_price_per_hour"]:.4f}/hour |
| Simulated Latency | {terms["latency_ms"]:.2f} ms |
| Simulated Availability | {terms["availability_percent"]:.2f}% |

---

## Negotiation

- **Negotiation Round:** {negotiation.get("round", "-")}
- **Utility:** {negotiation.get("utility", 0):.4f}
- **Status:** {negotiation.get("status", "-")}
- **Trigger:** {negotiation.get("trigger", "Initial negotiation")}

---

## Renegotiation

- **Trigger:** {renegotiation.get("trigger", "N/A")}
- **Breach Type:** {renegotiation.get("breach_type", "N/A")}
- **Severity:** {renegotiation.get("severity", "N/A")}
- **Previous Version:** {renegotiation.get("previous_version", "N/A")}
- **New Version:** {renegotiation.get("new_version", "N/A")}

---

## SLA Lifecycle History

"""

        if history:

            for index, event in enumerate(
                history,
                start=1
            ):

                content += f"""
### Event {index}

- **Time:** {event.get("timestamp", "")}
- **Event:** {event.get("event", "")}
"""

                if "breach_type" in event:

                    content += (
                        f"- **Breach Type:** "
                        f"{event['breach_type']}\n"
                    )

                if "severity" in event:

                    content += (
                        f"- **Severity:** "
                        f"{event['severity']}\n"
                    )

                if "previous_version" in event:

                    content += (
                        f"- **Previous Version:** "
                        f"{event['previous_version']}\n"
                    )

                if "new_version" in event:

                    content += (
                        f"- **New Version:** "
                        f"{event['new_version']}\n"
                    )

        else:

            content += (
                "No breach or renegotiation events recorded yet.\n"
            )

        content += """
---

## Simulation Notice

This is a simulated research artifact.

It does not represent a real cloud contract,
real cloud reservation, or real Rackspace SLA.
"""

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                content
            )

        return path

    # ============================================================
    # SAVE RENEGOTIATED AGREEMENT
    # ============================================================

    def save_renegotiated_agreement(
        self,
        agreement
    ):

        json_path = self.save_json(
            agreement
        )

        md_path = self.save_markdown(
            agreement
        )

        print()
        print("=" * 72)
        print("RENEGOTIATED SLA AGREEMENT SAVED")
        print("=" * 72)

        print(
            f"New Agreement ID : "
            f"{agreement['agreement_id']}"
        )

        print(
            f"Version          : "
            f"{agreement['version']}"
        )

        print(
            f"Previous         : "
            f"{agreement.get('previous_agreement_id', '-')}"
        )

        print(
            f"JSON File        : "
            f"{json_path}"
        )

        print(
            f"Markdown File    : "
            f"{md_path}"
        )

        print(
            "Status            : ACTIVE"
        )

        print(
            "Simulation only  : YES"
        )

        print("=" * 72)

        return agreement