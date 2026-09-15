import time

from negotiation.utility import UtilityEngine


class NegotiationManager:
    """
    Negotiation Manager for the simulated MAS SLA negotiation.

    Responsibilities:
        1. Receive provider agents.
        2. Evaluate provider offers.
        3. Apply hard SLA constraints.
        4. Rank feasible providers using fixed-weight utility.
        5. Conduct controlled multi-round negotiation.
        6. Accept a feasible agreement after the minimum
           negotiation rounds have been completed.
        7. Return a simulated SLA agreement.

    IMPORTANT:
    Rackspace pricing is used only as external market-price input.

    The negotiation itself is completely simulated for research.
    No real Rackspace SLA is created, modified, or negotiated.
    """

    def __init__(self, max_rounds=5, min_rounds=3):
        """
        Parameters
        ----------
        max_rounds : int
            Maximum number of negotiation rounds.

        min_rounds : int
            Minimum number of rounds that must be completed
            before an agreement can be finalized.

        The default configuration is:

            Minimum rounds = 3
            Maximum rounds = 5
        """

        self.max_rounds = max_rounds
        self.min_rounds = min_rounds

        self.history = []

        self.utility_engine = UtilityEngine()

    # =========================================================
    # COMMUNICATION LOGGING
    # =========================================================

    def log(
        self,
        sender,
        receiver,
        message
    ):
        """
        Print and store agent communication.
        """

        timestamp = time.strftime("%H:%M:%S")

        print(
            f"[{timestamp}] "
            f"{sender:<24} -> "
            f"{receiver:<24} | "
            f"{message}"
        )

        self.history.append(
            {
                "time": timestamp,
                "sender": sender,
                "receiver": receiver,
                "message": message,
            }
        )

    # =========================================================
    # ROUND HEADER
    # =========================================================

    def show_round_header(
        self,
        round_number
    ):
        """
        Display the current negotiation round.
        """

        print()
        print("=" * 72)
        print(
            f"NEGOTIATION ROUND "
            f"{round_number} OF {self.max_rounds}"
        )
        print("=" * 72)

    # =========================================================
    # CUSTOMER INITIAL PRICE
    # =========================================================

    def calculate_customer_start_price(
        self,
        market_price,
        max_budget
    ):
        """
        Calculate the customer's initial proposal.

        The customer begins at 70% of the provider's
        current market price.

        This creates a meaningful initial negotiation gap.
        """

        market_price = float(
            market_price
        )

        max_budget = float(
            max_budget
        )

        if market_price <= 0:
            return 0.0

        starting_price = (
            market_price * 0.70
        )

        starting_price = min(
            starting_price,
            max_budget
        )

        starting_price = max(
            starting_price,
            0.0
        )

        return round(
            starting_price,
            4
        )

    # =========================================================
    # CUSTOMER COUNTER-OFFER
    # =========================================================

    def calculate_customer_counter(
        self,
        current_provider_price,
        market_price,
        max_budget,
        round_number
    ):
        """
        Calculate the customer's next counter-offer.

        The customer gradually increases its offer.

        Concession schedule:

            Round 1 -> 15%
            Round 2 -> 12%
            Round 3 -> 9%
            Round 4 -> 6%
            Round 5 -> 3%

        The offer can never exceed the customer's
        maximum budget.
        """

        current_provider_price = float(
            current_provider_price
        )

        market_price = float(
            market_price
        )

        max_budget = float(
            max_budget
        )

        concession_schedule = {
            1: 0.15,
            2: 0.12,
            3: 0.09,
            4: 0.06,
            5: 0.03,
        }

        concession = concession_schedule.get(
            round_number,
            0.03
        )

        target_price = (
            market_price
            * (1.0 - concession)
        )

        target_price = min(
            target_price,
            max_budget
        )

        # Customer should not move backwards.
        target_price = max(
            target_price,
            current_provider_price
        )

        return round(
            target_price,
            4
        )

    # =========================================================
    # FINAL CUSTOMER OFFER
    # =========================================================

    def calculate_final_customer_offer(
        self,
        provider_price,
        market_price,
        max_budget
    ):
        """
        Calculate the customer's final possible offer.

        In the final round the customer can move closer
        to the market reference price.
        """

        provider_price = float(
            provider_price
        )

        market_price = float(
            market_price
        )

        max_budget = float(
            max_budget
        )

        final_target = (
            market_price * 0.97
        )

        final_target = min(
            final_target,
            max_budget
        )

        final_target = max(
            final_target,
            provider_price
        )

        return round(
            final_target,
            4
        )

    # =========================================================
    # PROVIDER EVALUATION
    # =========================================================

    def evaluate_provider(
        self,
        provider,
        customer_agent
    ):
        """
        Evaluate a provider using the fixed-weight
        utility engine and hard SLA constraints.
        """

        request = customer_agent.request

        result = (
            self.utility_engine.calculate_utility(
                offer=provider.offer,

                max_budget=request.max_budget,

                max_latency=request.max_latency,

                min_availability=request.min_availability,

                required_cpu=request.required_cpu,

                required_memory=request.required_memory
            )
        )

        return result

    # =========================================================
    # PROVIDER RANKING
    # =========================================================

    def rank_providers(
        self,
        customer_agent,
        provider_agents
    ):
        """
        Evaluate and rank all provider agents.

        Only providers satisfying all hard constraints
        are considered feasible candidates.

        Ranking is based on utility score.
        """

        print()
        print("=" * 72)
        print(
            "PHASE 1: PROVIDER DISCOVERY "
            "AND UTILITY EVALUATION"
        )
        print("=" * 72)

        self.log(
            "Customer Agent",
            "Negotiation Manager",
            (
                "SLA request received; "
                "evaluating provider offers."
            )
        )

        candidates = []

        for provider in provider_agents:

            offer = provider.offer

            result = self.evaluate_provider(
                provider,
                customer_agent
            )

            utility = result["utility"]

            feasible = result["feasible"]

            if feasible:

                candidates.append(
                    {
                        "provider": provider,
                        "utility": utility,
                        "result": result,
                    }
                )

                self.log(
                    "Negotiation Manager",
                    provider.agent_id,
                    (
                        f"Offer evaluated | "
                        f"price="
                        f"${offer.get('market_price', 0):.4f}/hr | "
                        f"CPU="
                        f"{offer.get('cpu', 0):.0f} | "
                        f"Memory="
                        f"{offer.get('memory', 0):.0f} GB | "
                        f"utility="
                        f"{utility:.4f} | "
                        f"FEASIBLE"
                    )
                )

            else:

                failed = [
                    key
                    for key, value
                    in result["constraints"].items()
                    if not value
                ]

                self.log(
                    "Negotiation Manager",
                    provider.agent_id,
                    (
                        "Offer rejected by hard constraints | "
                        f"failed={', '.join(failed)}"
                    )
                )

        # Highest utility first.
        candidates.sort(
            key=lambda item: item["utility"],
            reverse=True
        )

        print()
        print("PROVIDER RANKING")
        print("-" * 72)

        if not candidates:

            print(
                "No feasible provider offers were found."
            )

            return []

        for index, candidate in enumerate(
            candidates,
            start=1
        ):

            provider = candidate[
                "provider"
            ]

            utility = candidate[
                "utility"
            ]

            offer = provider.offer

            print(
                f"{index}. "
                f"{provider.agent_id:<24} "
                f"Utility={utility:.4f} "
                f"Price="
                f"${offer.get('market_price', 0):.4f}/hr "
                f"CPU="
                f"{offer.get('cpu', 0):.0f} "
                f"Memory="
                f"{offer.get('memory', 0):.0f} GB"
            )

        return candidates

    # =========================================================
    # NEGOTIATION STATE
    # =========================================================

    def display_negotiation_state(
        self,
        customer_price,
        provider_price,
        market_price,
        round_number
    ):
        """
        Display the current negotiation state.
        """

        gap = abs(
            provider_price
            - customer_price
        )

        print()
        print("NEGOTIATION STATE")
        print("-" * 72)

        print(
            f"Customer offer    : "
            f"${customer_price:.4f}/hr"
        )

        print(
            f"Provider offer    : "
            f"${provider_price:.4f}/hr"
        )

        print(
            f"Market reference  : "
            f"${market_price:.4f}/hr"
        )

        print(
            f"Current price gap : "
            f"${gap:.4f}/hr"
        )

        print(
            f"Round             : "
            f"{round_number}/{self.max_rounds}"
        )

        print(
            f"Minimum round     : "
            f"{self.min_rounds}"
        )

        print("-" * 72)

    # =========================================================
    # BUILD FINAL OFFER
    # =========================================================

    def build_final_offer(
        self,
        provider,
        final_price
    ):
        """
        Create a copy of the provider offer using
        the negotiated price.
        """

        final_offer = dict(
            provider.offer
        )

        final_offer[
            "market_price"
        ] = round(
            float(final_price),
            4
        )

        return final_offer

    # =========================================================
    # FINAL UTILITY
    # =========================================================

    def calculate_final_utility(
        self,
        provider,
        customer_agent,
        final_price
    ):
        """
        Calculate utility using the final negotiated price.
        """

        request = customer_agent.request

        final_offer = (
            self.build_final_offer(
                provider,
                final_price
            )
        )

        return (
            self.utility_engine.calculate_utility(
                offer=final_offer,

                max_budget=request.max_budget,

                max_latency=request.max_latency,

                min_availability=request.min_availability,

                required_cpu=request.required_cpu,

                required_memory=request.required_memory
            )
        )

    # =========================================================
    # NEGOTIATION WITH PROVIDER
    # =========================================================

    def negotiate_with_provider(
        self,
        customer_agent,
        provider,
        initial_utility,
        provider_rank
    ):
        """
        Conduct multi-round negotiation with one provider.

        IMPORTANT SIMULATION POLICY:

        A provider's early ACCEPT response does not immediately
        finalize the SLA.

        The Negotiation Manager requires at least
        self.min_rounds rounds.

        Therefore:

            Round 1 -> negotiation
            Round 2 -> negotiation
            Round 3 -> earliest possible agreement
            Round 4 -> possible
            Round 5 -> final opportunity

        This minimum-round rule is a research simulation
        parameter and does NOT represent Rackspace behavior.
        """

        request = customer_agent.request

        market_price = float(
            provider.offer.get(
                "market_price",
                0
            )
        )

        if market_price <= 0:

            self.log(
                "Negotiation Manager",
                provider.agent_id,
                "Invalid market price; negotiation skipped."
            )

            return None

        # -----------------------------------------------------
        # INITIAL CUSTOMER POSITION
        # -----------------------------------------------------

        customer_price = (
            self.calculate_customer_start_price(
                market_price,
                request.max_budget
            )
        )

        print()
        print("=" * 72)
        print(
            f"NEGOTIATING WITH "
            f"{provider.agent_id}"
        )
        print("=" * 72)

        self.log(
            "Negotiation Manager",
            provider.agent_id,
            (
                f"Selected candidate #{provider_rank} "
                f"based on utility="
                f"{initial_utility:.4f}"
            )
        )

        self.log(
            "Negotiation Manager",
            "Customer Agent",
            (
                f"Negotiation started with "
                f"{provider.agent_id}"
            )
        )

        self.log(
            "Customer Agent",
            provider.agent_id,
            (
                f"INITIAL PROPOSAL | "
                f"price=${customer_price:.4f}/hr | "
                f"budget="
                f"${request.max_budget:.4f}/hr"
            )
        )

        # -----------------------------------------------------
        # MULTI-ROUND LOOP
        # -----------------------------------------------------

        for round_number in range(
            1,
            self.max_rounds + 1
        ):

            self.show_round_header(
                round_number
            )

            # =================================================
            # CUSTOMER PROPOSAL
            # =================================================

            self.log(
                "Customer Agent",
                provider.agent_id,
                (
                    f"Round {round_number}: "
                    f"PROPOSAL "
                    f"${customer_price:.4f}/hr"
                )
            )

            # =================================================
            # PROVIDER EVALUATION
            # =================================================

            provider_response = (
                provider.evaluate_customer_offer(
                    customer_price,
                    round_number,
                    self.max_rounds
                )
            )

            decision = provider_response[
                "decision"
            ]

            provider_price = float(
                provider_response[
                    "price"
                ]
            )

            # =================================================
            # DISPLAY NEGOTIATION STATE
            # =================================================

            self.display_negotiation_state(
                customer_price,
                provider_price,
                market_price,
                round_number
            )

            # =================================================
            # PROVIDER ACCEPTS
            # =================================================

            if decision == "ACCEPT":

                # -------------------------------------------------
                # EARLY ACCEPTANCE
                # -------------------------------------------------

                if round_number < self.min_rounds:

                    self.log(
                        provider.agent_id,
                        "Customer Agent",
                        (
                            f"PROVISIONAL ACCEPTANCE | "
                            f"${provider_price:.4f}/hr"
                        )
                    )

                    self.log(
                        "Negotiation Manager",
                        provider.agent_id,
                        (
                            f"Provider accepted early at "
                            f"round {round_number}. "
                            f"Minimum required round is "
                            f"{self.min_rounds}."
                        )
                    )

                    self.log(
                        "Negotiation Manager",
                        "Customer Agent",
                        (
                            "Early acceptance detected. "
                            "Continuing negotiation to complete "
                            "the required multi-round process."
                        )
                    )

                    # Customer makes another controlled concession.
                    customer_counter = (
                        self.calculate_customer_counter(
                            provider_price,
                            market_price,
                            request.max_budget,
                            round_number
                        )
                    )

                    customer_counter = min(
                        customer_counter,
                        request.max_budget
                    )

                    customer_counter = max(
                        customer_counter,
                        customer_price
                    )

                    self.log(
                        "Customer Agent",
                        provider.agent_id,
                        (
                            f"CONTINUED NEGOTIATION OFFER | "
                            f"${customer_counter:.4f}/hr"
                        )
                    )

                    customer_price = (
                        customer_counter
                    )

                    time.sleep(0.5)

                    continue

                # -------------------------------------------------
                # ACCEPTANCE AFTER MINIMUM ROUNDS
                # -------------------------------------------------

                final_price = (
                    provider_price
                )

                final_result = (
                    self.calculate_final_utility(
                        provider,
                        customer_agent,
                        final_price
                    )
                )

                # -------------------------------------------------
                # FINAL HARD-CONSTRAINT CHECK
                # -------------------------------------------------

                if (
                    final_result["feasible"]
                    and
                    final_price <= request.max_budget
                ):

                    self.log(
                        provider.agent_id,
                        "Customer Agent",
                        (
                            f"ACCEPTED FINAL PROPOSAL | "
                            f"${final_price:.4f}/hr"
                        )
                    )

                    self.log(
                        "Negotiation Manager",
                        "Customer Agent",
                        (
                            f"Agreement reached with "
                            f"{provider.agent_id} | "
                            f"utility="
                            f"{final_result['utility']:.4f} | "
                            f"round={round_number}"
                        )
                    )

                    self.log(
                        "Negotiation Manager",
                        provider.agent_id,
                        (
                            "Negotiation successfully "
                            "converged."
                        )
                    )

                    return {
                        "provider": provider,

                        "price": round(
                            final_price,
                            4
                        ),

                        "round": round_number,

                        "utility": final_result[
                            "utility"
                        ],

                        "status": "ACCEPTED",

                        "provider_rank": provider_rank,

                        "constraints": final_result[
                            "constraints"
                        ],
                    }

                else:

                    self.log(
                        "Negotiation Manager",
                        provider.agent_id,
                        (
                            "Provider acceptance cannot be "
                            "finalized because the final "
                            "proposal violates hard SLA "
                            "constraints."
                        )
                    )

                    return None

            # =================================================
            # PROVIDER COUNTERS
            # =================================================

            elif decision == "COUNTER":

                self.log(
                    provider.agent_id,
                    "Customer Agent",
                    (
                        f"COUNTER-OFFER | "
                        f"${provider_price:.4f}/hr"
                    )
                )

                # -------------------------------------------------
                # CUSTOMER CALCULATES COUNTER
                # -------------------------------------------------

                if round_number < self.max_rounds:

                    customer_counter = (
                        self.calculate_customer_counter(
                            provider_price,
                            market_price,
                            request.max_budget,
                            round_number
                        )
                    )

                else:

                    customer_counter = (
                        self.calculate_final_customer_offer(
                            provider_price,
                            market_price,
                            request.max_budget
                        )
                    )

                # Customer can never exceed budget.
                customer_counter = min(
                    customer_counter,
                    request.max_budget
                )

                # Customer can never move backwards.
                customer_counter = max(
                    customer_counter,
                    customer_price
                )

                self.log(
                    "Negotiation Manager",
                    "Customer Agent",
                    (
                        f"Counter-offer calculated "
                        f"for round {round_number}."
                    )
                )

                self.log(
                    "Customer Agent",
                    provider.agent_id,
                    (
                        f"COUNTER-OFFER | "
                        f"${customer_counter:.4f}/hr"
                    )
                )

                # -------------------------------------------------
                # PRICE GAP
                # -------------------------------------------------

                gap = abs(
                    provider_price
                    - customer_counter
                )

                acceptable_gap = max(
                    market_price * 0.005,
                    0.00005
                )

                # -------------------------------------------------
                # EARLY ROUND
                # -------------------------------------------------

                if round_number < self.min_rounds:

                    if gap <= acceptable_gap:

                        self.log(
                            "Negotiation Manager",
                            provider.agent_id,
                            (
                                f"Offers are close "
                                f"(gap=${gap:.4f}), "
                                f"but minimum negotiation "
                                f"round {self.min_rounds} "
                                f"has not been reached."
                            )
                        )

                    else:

                        self.log(
                            "Negotiation Manager",
                            provider.agent_id,
                            (
                                f"Negotiation continues | "
                                f"price gap="
                                f"${gap:.4f}"
                            )
                        )

                    customer_price = (
                        customer_counter
                    )

                    time.sleep(0.5)

                    continue

                # -------------------------------------------------
                # AFTER MINIMUM ROUND
                # -------------------------------------------------

                if (
                    gap <= acceptable_gap
                    and
                    round_number >= self.min_rounds
                ):

                    final_price = min(
                        provider_price,
                        customer_counter
                    )

                    final_price = min(
                        final_price,
                        request.max_budget
                    )

                    final_result = (
                        self.calculate_final_utility(
                            provider,
                            customer_agent,
                            final_price
                        )
                    )

                    if final_result["feasible"]:

                        self.log(
                            "Negotiation Manager",
                            provider.agent_id,
                            (
                                f"CONVERGENCE DETECTED | "
                                f"gap=${gap:.4f} | "
                                f"final price="
                                f"${final_price:.4f}/hr"
                            )
                        )

                        self.log(
                            provider.agent_id,
                            "Customer Agent",
                            (
                                f"FINAL ACCEPTANCE | "
                                f"${final_price:.4f}/hr"
                            )
                        )

                        self.log(
                            "Customer Agent",
                            "Negotiation Manager",
                            (
                                f"Agreement accepted | "
                                f"provider="
                                f"{provider.agent_id} | "
                                f"price="
                                f"${final_price:.4f}/hr"
                            )
                        )

                        return {
                            "provider": provider,

                            "price": round(
                                final_price,
                                4
                            ),

                            "round": round_number,

                            "utility": final_result[
                                "utility"
                            ],

                            "status": "ACCEPTED",

                            "provider_rank": provider_rank,

                            "constraints": final_result[
                                "constraints"
                            ],
                        }

                    else:

                        self.log(
                            "Negotiation Manager",
                            provider.agent_id,
                            (
                                "Converged price failed "
                                "hard SLA constraint validation."
                            )
                        )

                        return None

                # -------------------------------------------------
                # NOT YET CONVERGED
                # -------------------------------------------------

                self.log(
                    "Negotiation Manager",
                    provider.agent_id,
                    (
                        f"Negotiation continues | "
                        f"gap=${gap:.4f}"
                    )
                )

                customer_price = (
                    customer_counter
                )

            # =================================================
            # PROVIDER REJECTS
            # =================================================

            else:

                self.log(
                    provider.agent_id,
                    "Customer Agent",
                    (
                        "REJECTED customer proposal."
                    )
                )

                self.log(
                    "Negotiation Manager",
                    provider.agent_id,
                    (
                        "Provider rejected the "
                        "current negotiation."
                    )
                )

                return None

            time.sleep(0.5)

        # =====================================================
        # MAXIMUM ROUNDS EXHAUSTED
        # =====================================================

        self.log(
            "Negotiation Manager",
            provider.agent_id,
            (
                f"Negotiation ended after "
                f"{self.max_rounds} rounds "
                f"without agreement."
            )
        )

        return None

    # =========================================================
    # MAIN NEGOTIATION
    # =========================================================

    def negotiate(
        self,
        customer_agent,
        provider_agents
    ):
        """
        Main negotiation workflow.

        Providers are:

            1. evaluated,
            2. filtered using hard constraints,
            3. ranked using utility,
            4. negotiated in utility order.

        The first provider that reaches a feasible agreement
        is selected.
        """

        print()
        print("=" * 72)
        print("MULTI-AGENT BDI SLA NEGOTIATION")
        print("=" * 72)

        print(
            f"Negotiation rounds: "
            f"{self.min_rounds}-"
            f"{self.max_rounds}"
        )

        print(
            "Minimum-round policy: "
            f"agreement cannot be finalized before "
            f"round {self.min_rounds}"
        )

        print(
            "Acceptance policy: "
            "highest-utility feasible provider"
        )

        print(
            "Utility weights: "
            "Cost=0.40 | "
            "Resources=0.25 | "
            "Latency=0.20 | "
            "Availability=0.15"
        )

        print(
            "SLA policy: "
            "hard constraints are mandatory"
        )

        print()

        # =====================================================
        # PROVIDER RANKING
        # =====================================================

        candidates = (
            self.rank_providers(
                customer_agent,
                provider_agents
            )
        )

        if not candidates:

            print()
            print("=" * 72)
            print("NEGOTIATION FAILED")
            print("=" * 72)

            print(
                "No provider satisfies all "
                "hard SLA constraints."
            )

            print("=" * 72)

            return None

        # =====================================================
        # NEGOTIATE IN UTILITY ORDER
        # =====================================================

        for rank, candidate in enumerate(
            candidates,
            start=1
        ):

            provider = candidate[
                "provider"
            ]

            utility = candidate[
                "utility"
            ]

            agreement = (
                self.negotiate_with_provider(
                    customer_agent,
                    provider,
                    utility,
                    rank
                )
            )

            if agreement is not None:

                return self.display_agreement(
                    customer_agent,
                    agreement
                )

            self.log(
                "Negotiation Manager",
                "Customer Agent",
                (
                    f"{provider.agent_id} failed; "
                    "trying next highest-utility provider."
                )
            )

        # =====================================================
        # COMPLETE FAILURE
        # =====================================================

        print()
        print("=" * 72)
        print("NEGOTIATION FAILED")
        print("=" * 72)

        print(
            "No provider reached an agreement "
            f"within {self.max_rounds} rounds."
        )

        print("=" * 72)

        return None

    # =========================================================
    # DISPLAY FINAL AGREEMENT
    # =========================================================

    def display_agreement(
        self,
        customer_agent,
        agreement
    ):
        """
        Display and record the final simulated SLA agreement.
        """

        provider = agreement[
            "provider"
        ]

        offer = provider.offer

        print()
        print("=" * 72)
        print("NEGOTIATION SUCCESSFUL")
        print("=" * 72)

        print(
            f"Customer          : "
            f"{customer_agent.request.customer_name}"
        )

        print(
            f"Provider Agent    : "
            f"{provider.agent_id}"
        )

        print(
            f"Server Class      : "
            f"{offer.get('server_class', 'Unknown')}"
        )

        print(
            f"Region            : "
            f"{offer.get('region', 'Unknown')}"
        )

        print(
            f"CPU               : "
            f"{offer.get('cpu', 0):.0f} vCPU"
        )

        print(
            f"Memory            : "
            f"{offer.get('memory', 0):.0f} GB"
        )

        print(
            f"Agreed Price      : "
            f"${agreement['price']:.4f}/hour"
        )

        print(
            f"Utility Score     : "
            f"{agreement['utility']:.4f}"
        )

        print(
            f"Negotiation Round : "
            f"{agreement['round']}"
        )

        print(
            f"Provider Rank     : "
            f"#{agreement['provider_rank']}"
        )

        print(
            f"Status            : "
            f"{agreement['status']}"
        )

        print("=" * 72)

        print(
            "NOTE: This SLA is a SIMULATED research agreement."
        )

        print(
            "No real Rackspace SLA was created or modified."
        )

        print("=" * 72)

        # =====================================================
        # SAVE AGREEMENT TO MANAGER HISTORY
        # =====================================================

        self.history.append(
            {
                "type": "simulated_sla_agreement",

                "customer": (
                    customer_agent
                    .request
                    .customer_name
                ),

                "provider": provider.agent_id,

                "server_class": offer.get(
                    "server_class",
                    "Unknown"
                ),

                "region": offer.get(
                    "region",
                    "Unknown"
                ),

                "cpu": offer.get(
                    "cpu",
                    0
                ),

                "memory": offer.get(
                    "memory",
                    0
                ),

                "price": agreement[
                    "price"
                ],

                "round": agreement[
                    "round"
                ],

                "utility": agreement[
                    "utility"
                ],

                "status": agreement[
                    "status"
                ],
            }
        )

        return agreement