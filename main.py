import time

from models.sla_request import SLARequest

from negotiation.rackspace_spot_client import RackspaceSpotClient
from negotiation.negotiation_algorithm import NegotiationManager

from agents.customer_agent import CustomerAgent
from agents.provider_agent import ProviderAgent

from agreements.agreement_manager import AgreementManager

from simulation.breach_simulator import BreachSimulator
from simulation.sla_monitor import SLAMonitor
from simulation.renegotiation_manager import RenegotiationManager


# ============================================================
# DISPLAY HELPERS
# ============================================================

def line(char="=", length=72):
    print(char * length)


def title(text):
    print()
    line("=")
    print(text)
    line("=")


def pause(seconds=0.3):
    time.sleep(seconds)


# ============================================================
# INPUT HELPERS
# ============================================================

def get_int(prompt, minimum=1):
    while True:
        try:
            value = int(input(prompt).strip())

            if value < minimum:
                print(f"Value must be at least {minimum}.")
                continue

            return value

        except ValueError:
            print("Please enter a valid integer.")


def get_float(prompt, minimum=0.0):
    while True:
        try:
            value = float(input(prompt).strip())

            if value < minimum:
                print(f"Value must be at least {minimum}.")
                continue

            return value

        except ValueError:
            print("Please enter a valid number.")


def get_priority():
    print()
    print("Priority:")
    print("1. Low")
    print("2. Balanced")
    print("3. High")

    while True:
        choice = input("Enter priority: ").strip()

        if choice == "1":
            return "Low"

        if choice == "2":
            return "Balanced"

        if choice == "3":
            return "High"

        print("Please enter 1, 2, or 3.")


# ============================================================
# CUSTOMER REQUEST
# ============================================================

def get_customer_request():

    title("CUSTOMER REQUIREMENTS")

    customer_name = input(
        "Customer name: "
    ).strip()

    while not customer_name:
        print("Customer name cannot be empty.")
        customer_name = input(
            "Customer name: "
        ).strip()

    application_type = input(
        "Application type: "
    ).strip()

    while not application_type:
        print("Application type cannot be empty.")
        application_type = input(
            "Application type: "
        ).strip()

    required_cpu = get_int(
        "Required CPU (vCPU): ",
        minimum=1
    )

    required_memory = get_float(
        "Required memory (GB): ",
        minimum=1
    )

    max_budget = get_float(
        "Maximum budget ($/hour): ",
        minimum=0
    )

    max_latency = get_float(
        "Maximum latency (ms): ",
        minimum=0
    )

    min_availability = get_float(
        "Minimum availability (%): ",
        minimum=0
    )

    if min_availability > 100:
        print(
            "Availability cannot be greater than 100%."
        )
        min_availability = 100.0

    priority = get_priority()

    return SLARequest(
        customer_name=customer_name,
        application_type=application_type,
        required_cpu=required_cpu,
        required_memory=required_memory,
        max_budget=max_budget,
        max_latency=max_latency,
        min_availability=min_availability,
        priority=priority
    )


def display_customer_request(request):

    title("CUSTOMER SLA REQUEST")

    print(
        f"Customer          : "
        f"{request.customer_name}"
    )

    print(
        f"Application       : "
        f"{request.application_type}"
    )

    print(
        f"CPU               : "
        f"{request.required_cpu} vCPU"
    )

    print(
        f"Memory            : "
        f"{request.required_memory} GB"
    )

    print(
        f"Max Budget        : "
        f"${request.max_budget:.4f}/hour"
    )

    print(
        f"Max Latency       : "
        f"{request.max_latency} ms"
    )

    print(
        f"Min Availability  : "
        f"{request.min_availability}%"
    )

    print(
        f"Priority          : "
        f"{request.priority}"
    )

    line()


# ============================================================
# RACKSPACE LIVE PRICING
# ============================================================

def fetch_live_offers():

    title("LIVE RACKSPACE SPOT PRICING")

    client = RackspaceSpotClient()

    print(
        "Fetching public Rackspace Spot market pricing..."
    )

    offers = client.fetch_pricing()

    if not offers:
        print()
        print(
            "ERROR: No pricing records were retrieved."
        )
        return []

    print()
    print(
        f"Successfully retrieved "
        f"{len(offers)} pricing records."
    )

    return offers


# ============================================================
# OFFER NORMALIZATION
# ============================================================

def normalize_offer(offer):

    normalized = dict(offer)

    try:
        normalized["cpu"] = float(
            normalized.get("cpu", 0)
        )
    except (TypeError, ValueError):
        normalized["cpu"] = 0.0

    try:
        normalized["memory"] = float(
            normalized.get("memory", 0)
        )
    except (TypeError, ValueError):
        normalized["memory"] = 0.0

    try:
        normalized["market_price"] = float(
            normalized.get("market_price", 0)
        )
    except (TypeError, ValueError):
        normalized["market_price"] = 0.0

    try:
        normalized["ondemand_price"] = float(
            normalized.get("ondemand_price", 0)
        )
    except (TypeError, ValueError):
        normalized["ondemand_price"] = 0.0

    return normalized


# ============================================================
# SIMULATED LATENCY
# ============================================================

def simulated_latency(offer):

    """
    Latency is simulated locally.

    Rackspace public market pricing is used only as
    external market-price/resource input.
    """

    region = str(
        offer.get("region", "")
    ).lower()

    if "iad" in region:
        return 35.0

    if "dfw" in region:
        return 45.0

    if "sjc" in region:
        return 55.0

    if "ord" in region:
        return 50.0

    if "lon" in region:
        return 80.0

    if "ams" in region:
        return 85.0

    if "hkg" in region:
        return 90.0

    if "syd" in region:
        return 95.0

    return 60.0


# ============================================================
# SIMULATED AVAILABILITY
# ============================================================

def simulated_availability(offer):

    """
    Availability is simulated locally for the research model.
    """

    category = str(
        offer.get("category", "")
    ).lower()

    if "memory" in category:
        return 99.2

    if "compute" in category:
        return 99.1

    if "general" in category:
        return 99.0

    return 99.0


# ============================================================
# ENRICH OFFER
# ============================================================

def enrich_offer(offer):

    offer = normalize_offer(
        offer
    )

    offer["latency"] = (
        simulated_latency(offer)
    )

    offer["availability"] = (
        simulated_availability(offer)
    )

    return offer


# ============================================================
# FIND FEASIBLE OFFERS
# ============================================================

def find_feasible_offers(
    offers,
    request
):

    feasible = []

    for raw_offer in offers:

        offer = enrich_offer(
            raw_offer
        )

        cpu_ok = (
            offer["cpu"]
            >= request.required_cpu
        )

        memory_ok = (
            offer["memory"]
            >= request.required_memory
        )

        price_ok = (
            offer["market_price"]
            <= request.max_budget
        )

        latency_ok = (
            offer["latency"]
            <= request.max_latency
        )

        availability_ok = (
            offer["availability"]
            >= request.min_availability
        )

        if (
            cpu_ok
            and memory_ok
            and price_ok
            and latency_ok
            and availability_ok
        ):
            feasible.append(
                offer
            )

    return feasible


# ============================================================
# DISPLAY MARKET OFFERS
# ============================================================

def display_market_offers(
    offers,
    limit=10
):

    title("FEASIBLE LIVE MARKET OFFERS")

    if not offers:
        print(
            "No feasible offers found."
        )
        return

    print(
        f"{'No.':<5}"
        f"{'Server Class':<25}"
        f"{'Region':<22}"
        f"{'CPU':<8}"
        f"{'Memory':<10}"
        f"{'Price':<12}"
    )

    line("-")

    for index, offer in enumerate(
        offers[:limit],
        start=1
    ):

        print(
            f"{index:<5}"
            f"{offer.get('server_class', 'Unknown'):<25}"
            f"{offer.get('region', 'Unknown'):<22}"
            f"{offer.get('cpu', 0):<8.0f}"
            f"{offer.get('memory', 0):<10.0f}"
            f"${offer.get('market_price', 0):<11.4f}"
        )

    line("-")


# ============================================================
# CREATE PROVIDER AGENTS
# ============================================================

def create_provider_agents(
    feasible_offers,
    request
):

    """
    Provider selection is performed by NegotiationManager.

    The manager expects:

        rank_providers(
            customer_agent,
            provider_agents
        )

    Therefore provider agents are created first.
    """

    provider_agents = []

    for index, offer in enumerate(
        feasible_offers,
        start=1
    ):

        provider = ProviderAgent(
            agent_id=f"Provider Agent {index}",
            offer=offer
        )

        provider_agents.append(
            provider
        )

    return provider_agents


# ============================================================
# LIMIT PROVIDERS FOR DEMO
# ============================================================

def select_provider_agents(
    provider_agents,
    limit=10
):

    return provider_agents[:limit]


# ============================================================
# MAS DISPLAY
# ============================================================

def display_mas(
    customer_agent,
    provider_agents
):

    title("MULTI-AGENT SYSTEM")

    print(
        "Customer Agent"
    )

    print(
        "Negotiation Manager"
    )

    for provider in provider_agents:

        print(
            provider.agent_id
        )

    line()


# ============================================================
# BDI DISPLAY
# ============================================================

def display_bdi_states(
    customer_agent,
    provider_agents
):

    title("BDI REASONING")

    customer_agent.display_bdi()

    for provider in provider_agents[:5]:

        provider.display_bdi()


# ============================================================
# INITIAL AGENT COMMUNICATION
# ============================================================

def display_initial_communication(
    customer_agent,
    provider_agents
):

    title("AGENT COMMUNICATION")

    customer_agent.log(
        "Negotiation Manager",
        "SLA request submitted; "
        "evaluating provider offers."
    )

    pause()

    print(
        "[Negotiation Manager] -> Provider Agents | "
        "Requesting feasible cloud offers."
    )

    pause()

    for provider in provider_agents[:5]:

        print(
            f"[{provider.agent_id}] -> "
            f"Negotiation Manager | "
            f"Market price = "
            f"${provider.beliefs['market_price']:.4f}/hr"
        )

        pause(0.15)


# ============================================================
# FINAL AGREEMENT DISPLAY
# ============================================================

def display_final_result(
    agreement
):

    title("FINAL SIMULATED SLA AGREEMENT")

    if not agreement:

        print(
            "No agreement was reached."
        )

        return

    print(
        f"Agreement ID      : "
        f"{agreement.get('agreement_id', 'N/A')}"
    )

    print(
        f"Provider Agent    : "
        f"{agreement.get('provider_agent', 'N/A')}"
    )

    print(
        f"Server Class      : "
        f"{agreement.get('server_class', 'N/A')}"
    )

    print(
        f"Region            : "
        f"{agreement.get('region', 'N/A')}"
    )

    print(
        f"CPU               : "
        f"{agreement.get('cpu', 'N/A')} vCPU"
    )

    print(
        f"Memory            : "
        f"{agreement.get('memory', 'N/A')} GB"
    )

    try:
        price = float(
            agreement.get("price", 0)
        )
    except (TypeError, ValueError):
        price = 0.0

    print(
        f"Agreed Price      : "
        f"${price:.4f}/hour"
    )

    print(
        f"Utility Score     : "
        f"{agreement.get('utility', 'N/A')}"
    )

    print(
        f"Negotiation Round : "
        f"{agreement.get('round', 'N/A')}"
    )

    print(
        f"Status            : "
        f"{agreement.get('status', 'N/A')}"
    )

    line()

    print(
        "This is a simulated research SLA."
    )

    print(
        "No real Rackspace SLA was created."
    )

    line()


# ============================================================
# INTERACTIVE SLA MONITORING
# ============================================================

def run_sla_monitoring_phase(
    saved_agreement
):

    """
    Interactive SLA lifecycle simulation.

    Commands:

        STATUS
            System checks the current agreement.

        BREACH
            User asks the simulator to inject a fault.

        EXIT
            End monitoring.

    IMPORTANT:

    The user does NOT declare that an SLA breach exists.

    The user only instructs the simulation to inject a fault.

    SLAMonitor independently determines whether the
    resulting measurement violates the SLA.
    """

    breach_simulator = (
        BreachSimulator(
            seed=42
        )
    )

    monitor = SLAMonitor()

    renegotiation_manager = (
        RenegotiationManager()
    )

    title(
        "INTERACTIVE SLA MONITORING"
    )

    print(
        "The simulated SLA agreement is now active."
    )

    print()
    print(
        "The system is waiting for a monitoring command."
    )

    print()
    print(
        "Available commands:"
    )

    print(
        "  STATUS  - Check current SLA status"
    )

    print(
        "  BREACH  - Inject a simulated SLA failure"
    )

    print(
        "  EXIT    - End monitoring"
    )

    line()

    while True:

        command = input(
            "\nEnter command: "
        ).strip().upper()

        # ====================================================
        # STATUS
        # ====================================================

        if command == "STATUS":

            print()
            print(
                "[SLA Monitor] "
                "Checking current SLA conditions..."
            )

            pause()

            measurements = (
                breach_simulator
                .simulate_healthy_state(
                    saved_agreement
                )
            )

            monitor.display_measurements(
                measurements
            )

            result = monitor.check_sla(
                saved_agreement,
                measurements
            )

            monitor.display_result(
                result
            )

        # ====================================================
        # BREACH
        # ====================================================

        elif command == "BREACH":

            print()
            line()
            print(
                "SIMULATED BREACH INJECTION"
            )
            line()

            print(
                "Select the condition to simulate:"
            )

            print()
            print(
                "1. Availability"
            )

            print(
                "2. Latency"
            )

            print(
                "3. Budget"
            )

            print(
                "4. Resource Capacity"
            )

            print(
                "5. Cancel"
            )

            choice = input(
                "\nEnter choice: "
            ).strip()

            breach_map = {
                "1": "availability",
                "2": "latency",
                "3": "budget",
                "4": "resource"
            }

            if choice == "5":

                print(
                    "Breach simulation cancelled."
                )

                continue

            if choice not in breach_map:

                print(
                    "Invalid choice. "
                    "Please select 1-5."
                )

                continue

            breach_type = (
                breach_map[choice]
            )

            print()
            print(
                "[Simulation] "
                f"Injecting {breach_type.upper()} breach..."
            )

            pause()

            measurements = (
                breach_simulator
                .simulate_breach(
                    saved_agreement,
                    breach_type
                )
            )

            monitor.display_measurements(
                measurements
            )

            print()
            print(
                "[SLA Monitor] "
                "Evaluating SLA conditions..."
            )

            pause()

            # ------------------------------------------------
            # AUTOMATIC BREACH DETECTION
            # ------------------------------------------------

            result = monitor.check_sla(
                saved_agreement,
                measurements
            )

            monitor.display_result(
                result
            )

            # ------------------------------------------------
            # NO BREACH
            # ------------------------------------------------

            if not result["breached"]:

                print()
                print(
                    "[SLA Monitor] "
                    "No SLA violation detected."
                )

                continue

            # ------------------------------------------------
            # BREACH DETECTED
            # ------------------------------------------------

            print()
            print(
                "[Negotiation Manager] "
                "SLA breach detected."
            )

            print(
                "[Negotiation Manager] "
                "Starting automatic renegotiation..."
            )

            pause()

            # ------------------------------------------------
            # BREACH NOTIFICATION
            # ------------------------------------------------

            renegotiation_manager.display_breach_notification(
                saved_agreement,
                result
            )

            # ------------------------------------------------
            # RENEGOTIATION
            # ------------------------------------------------

            new_agreement = (
                renegotiation_manager
                .create_renegotiated_agreement(
                    saved_agreement,
                    result
                )
            )

            if not new_agreement:

                print()
                print(
                    "Renegotiation failed."
                )

                continue

            # ------------------------------------------------
            # SAVE NEW AGREEMENT VERSION
            # ------------------------------------------------

            renegotiation_manager.save_renegotiated_agreement(
                new_agreement
            )

            print()
            line()
            print(
                "RENEGOTIATION COMPLETED"
            )
            line()

            print(
                f"New Agreement ID : "
                f"{new_agreement.get('agreement_id', 'N/A')}"
            )

            print(
                f"Version           : "
                f"{new_agreement.get('version', 'N/A')}"
            )

            print(
                f"Status            : "
                f"{new_agreement.get('status', 'N/A')}"
            )

            try:
                new_price = float(
                    new_agreement.get(
                        "price",
                        0
                    )
                )
            except (TypeError, ValueError):
                new_price = 0.0

            print(
                f"New Price         : "
                f"${new_price:.4f}/hr"
            )

            print(
                f"Original Agreement : "
                f"{saved_agreement.get('agreement_id', 'N/A')}"
            )

            line()

            # ------------------------------------------------
            # NEW AGREEMENT BECOMES ACTIVE
            # ------------------------------------------------

            saved_agreement = (
                new_agreement
            )

            print()
            print(
                "[SLA Monitor] "
                "Renegotiated agreement "
                "is now the active SLA."
            )

            print()
            print(
                "The original agreement "
                "has NOT been overwritten."
            )

        # ====================================================
        # EXIT
        # ====================================================

        elif command == "EXIT":

            print()
            print(
                "Exiting SLA monitoring phase."
            )

            print(
                "Original and renegotiated "
                "agreements remain saved."
            )

            break

        # ====================================================
        # INVALID COMMAND
        # ====================================================

        else:

            print()
            print(
                "Unknown command."
            )

            print(
                "Use STATUS, BREACH, or EXIT."
            )


# ============================================================
# MAIN
# ============================================================

def main():

    title(
        "AGENTIC CLOUD MANAGEMENT"
    )

    print(
        "LIVE RACKSPACE SPOT PRICING "
        "+ SIMULATED MAS NEGOTIATION"
    )

    print()
    print(
        "Research Simulation Only"
    )

    print(
        "No real cloud SLA is created, "
        "modified, or negotiated."
    )

    # ========================================================
    # STEP 1
    # CUSTOMER REQUIREMENTS
    # ========================================================

    request = (
        get_customer_request()
    )

    display_customer_request(
        request
    )

    # ========================================================
    # STEP 2
    # CUSTOMER AGENT
    # ========================================================

    customer_agent = (
        CustomerAgent(
            request
        )
    )

    # ========================================================
    # STEP 3
    # LIVE PRICING
    # ========================================================

    live_offers = (
        fetch_live_offers()
    )

    if not live_offers:

        print()
        print(
            "Program stopped."
        )

        return

    # ========================================================
    # STEP 4
    # FEASIBLE OFFERS
    # ========================================================

    feasible_offers = (
        find_feasible_offers(
            live_offers,
            request
        )
    )

    print()
    print(
        f"Feasible offers: "
        f"{len(feasible_offers)}"
    )

    if not feasible_offers:

        print()
        print(
            "No provider satisfies "
            "all customer constraints."
        )

        return

    display_market_offers(
        feasible_offers,
        limit=10
    )

    # ========================================================
    # STEP 5
    # PROVIDER AGENTS
    # ========================================================

    provider_agents = (
        create_provider_agents(
            feasible_offers,
            request
        )
    )

    # Keep the interactive demo manageable.
    provider_agents = (
        select_provider_agents(
            provider_agents,
            limit=10
        )
    )

    print()
    print(
        f"Provider Agents created: "
        f"{len(provider_agents)}"
    )

    # ========================================================
    # STEP 6
    # MAS
    # ========================================================

    display_mas(
        customer_agent,
        provider_agents
    )

    # ========================================================
    # STEP 7
    # BDI
    # ========================================================

    display_bdi_states(
        customer_agent,
        provider_agents
    )

    # ========================================================
    # STEP 8
    # INITIAL COMMUNICATION
    # ========================================================

    display_initial_communication(
        customer_agent,
        provider_agents
    )

    # ========================================================
    # STEP 9
    # NEGOTIATION
    # ========================================================

    title(
        "MULTI-ROUND SLA NEGOTIATION"
    )

    negotiation_manager = (
        NegotiationManager(
            max_rounds=5,
            min_rounds=3
        )
    )

    try:

        # IMPORTANT:
        # Your current NegotiationManager expects:
        #
        # negotiate(
        #     customer_agent,
        #     provider_agents
        # )
        #
        # NOT:
        #
        # negotiate(
        #     request,
        #     customer_agent,
        #     provider_agents
        # )

        agreement = (
            negotiation_manager.negotiate(
                customer_agent,
                provider_agents
            )
        )

    except Exception as error:

        print()
        print(
            "Negotiation error:"
        )

        print(
            error
        )

        return

    # ========================================================
    # STEP 10
    # NEGOTIATION RESULT
    # ========================================================

    if not agreement:

        print()
        line()
        print(
            "NEGOTIATION FAILED"
        )
        line()

        print(
            "No provider reached an acceptable "
            "simulated SLA agreement."
        )

        return

    # ========================================================
    # STEP 11
    # DISPLAY AGREEMENT
    # ========================================================

    def display_final_result(agreement):

        title("FINAL SIMULATED SLA AGREEMENT")

        if not agreement:
            print("No agreement was reached.")
            return

        # ProviderAgent object
        provider = agreement.get("provider")

        # Provider's actual offer dictionary
        offer = {}

        if provider is not None:
            offer = getattr(provider, "offer", {}) or {}

        # Extract provider details
        provider_agent = getattr(
            provider,
            "agent_id",
            "N/A"
        )

        server_class = offer.get(
            "server_class",
            "N/A"
        )

        region = offer.get(
            "region",
            "N/A"
        )

        cpu = offer.get(
            "cpu",
            "N/A"
        )

        memory = offer.get(
            "memory",
            "N/A"
        )

        # Extract negotiation details
        price = agreement.get(
            "price",
            0
        )

        utility = agreement.get(
            "utility",
            "N/A"
        )

        round_number = agreement.get(
            "round",
            "N/A"
        )

        status = agreement.get(
            "status",
            "N/A"
        )

        print(
            f"Provider Agent    : "
            f"{provider_agent}"
        )

        print(
            f"Server Class      : "
            f"{server_class}"
        )

        print(
            f"Region            : "
            f"{region}"
        )

        print(
            f"CPU               : "
            f"{cpu} vCPU"
        )

        print(
            f"Memory            : "
            f"{memory} GB"
        )

        print(
            f"Agreed Price      : "
            f"${float(price):.4f}/hour"
        )

        print(
            f"Utility Score     : "
            f"{utility}"
        )

        print(
            f"Negotiation Round : "
            f"{round_number}"
        )

        print(
            f"Status            : "
            f"{status}"
        )

        line()

        print(
            "NOTE: This is a SIMULATED research agreement."
        )

        print(
            "No real Rackspace SLA was created or modified."
        )

        line()
        # ========================================================
        # STEP 12
        # SAVE AGREEMENT
        # ========================================================

        print()
        print(
            "[Agreement Manager] "
            "Saving simulated SLA agreement..."
        )

    try:

        agreement_manager = (
            AgreementManager()
        )

        saved_agreement = (
            agreement_manager.save_agreement(
                agreement,
                request
            )
        )

        # Depending on your AgreementManager,
        # save_agreement may return the agreement
        # or may simply save it.

        if isinstance(
            saved_agreement,
            dict
        ):

            agreement = (
                saved_agreement
            )

    except Exception as error:

        print()
        print(
            "Agreement saving error:"
        )

        print(
            error
        )

        return

    print()
    print(
        "[Agreement Manager] "
        "Agreement saved successfully."
    )

    # ========================================================
    # STEP 13
    # INTERACTIVE SLA MONITORING
    # ========================================================

    run_sla_monitoring_phase(
        agreement
    )

    # ========================================================
    # END
    # ========================================================

    print()
    title(
        "AGENTIC CLOUD MANAGEMENT COMPLETED"
    )

    print(
        "Negotiation + agreement persistence + "
        "interactive SLA monitoring completed."
    )

    print(
        "All cloud behavior was simulated "
        "for research purposes."
    )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()