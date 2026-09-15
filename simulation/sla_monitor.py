class SLAMonitor:
    """
    Monitors simulated SLA measurements against
    the terms stored in the agreement.

    IMPORTANT:
    This monitor only evaluates simulated measurements.
    It does not monitor real cloud infrastructure.
    """

    # ============================================================
    # DISPLAY AGREEMENT
    # ============================================================

    def display_agreement(self, agreement):

        print()
        print("=" * 72)
        print("SLA MONITORING")
        print("=" * 72)

        print(
            f"Agreement ID      : "
            f"{agreement.get('agreement_id', 'Unknown')}"
        )

        print(
            f"Provider           : "
            f"{agreement.get('provider_agent', 'Unknown')}"
        )

        print(
            f"Agreed Price      : "
            f"${float(agreement.get('price', 0)):.4f}/hr"
        )

        print(
            f"Required CPU      : "
            f"{agreement.get('cpu', 0)} vCPU"
        )

        print(
            f"Required Memory   : "
            f"{agreement.get('memory', 0)} GB"
        )

        print(
            f"Max Latency       : "
            f"{agreement.get('max_latency', 'N/A')} ms"
        )

        print(
            f"Min Availability  : "
            f"{agreement.get('min_availability', 'N/A')}%"
        )

        print("=" * 72)

    # ============================================================
    # DISPLAY MEASUREMENTS
    # ============================================================

    def display_measurements(self, measurements):

        print()
        print("CURRENT SIMULATED MEASUREMENTS")
        print("-" * 72)

        print(
            f"Availability : "
            f"{measurements.get('availability', 'N/A')}%"
        )

        print(
            f"Latency      : "
            f"{measurements.get('latency', 'N/A')} ms"
        )

        print(
            f"Price        : "
            f"${float(measurements.get('price', 0)):.4f}/hr"
        )

        print(
            f"CPU          : "
            f"{measurements.get('cpu', 'N/A')} vCPU"
        )

        print(
            f"Memory       : "
            f"{measurements.get('memory', 'N/A')} GB"
        )

        print("-" * 72)

    # ============================================================
    # DETERMINE BREACH TYPE
    # ============================================================

    def determine_breach_type(
        self,
        agreement,
        measurements,
        violations
    ):
        """
        Converts monitor violations into the breach types
        expected by the RenegotiationManager.

        Supported types:

            AVAILABILITY
            LATENCY
            PRICE
            CPU
            MEMORY
        """

        if not violations:
            return None

        # --------------------------------------------------------
        # Check each violation
        # --------------------------------------------------------

        for violation in violations:

            violation_type = (
                violation.get("type", "")
                .lower()
            )

            # Availability
            if violation_type == "availability":
                return "AVAILABILITY"

            # Latency
            if violation_type == "latency":
                return "LATENCY"

            # Budget / price
            if violation_type == "budget":
                return "PRICE"

            # Resource violation
            if violation_type == "resource":

                required_cpu = float(
                    agreement.get("cpu", 0)
                )

                required_memory = float(
                    agreement.get("memory", 0)
                )

                actual_cpu = float(
                    measurements.get("cpu", 0)
                )

                actual_memory = float(
                    measurements.get("memory", 0)
                )

                if actual_cpu < required_cpu:
                    return "CPU"

                if actual_memory < required_memory:
                    return "MEMORY"

        # --------------------------------------------------------
        # Fallback
        # --------------------------------------------------------

        return (
            violations[0]
            .get("type", "UNKNOWN")
            .upper()
        )

    # ============================================================
    # DETERMINE SEVERITY
    # ============================================================

    def determine_severity(
        self,
        agreement,
        measurements,
        breach_type
    ):
        """
        Calculates a simple research-oriented breach severity.

        Levels:

            LOW
            MEDIUM
            HIGH
            CRITICAL
        """

        if not breach_type:
            return "NONE"

        breach_type = breach_type.upper()

        # --------------------------------------------------------
        # Availability
        # --------------------------------------------------------

        if breach_type == "AVAILABILITY":

            required = float(
                agreement.get(
                    "min_availability",
                    98.0
                )
            )

            actual = float(
                measurements.get(
                    "availability",
                    0
                )
            )

            difference = required - actual

            if difference >= 5:
                return "CRITICAL"

            if difference >= 3:
                return "HIGH"

            if difference >= 1:
                return "MEDIUM"

            return "LOW"

        # --------------------------------------------------------
        # Latency
        # --------------------------------------------------------

        if breach_type == "LATENCY":

            maximum = float(
                agreement.get(
                    "max_latency",
                    100.0
                )
            )

            actual = float(
                measurements.get(
                    "latency",
                    0
                )
            )

            if maximum <= 0:
                return "HIGH"

            ratio = actual / maximum

            if ratio >= 2.0:
                return "CRITICAL"

            if ratio >= 1.5:
                return "HIGH"

            if ratio >= 1.2:
                return "MEDIUM"

            return "LOW"

        # --------------------------------------------------------
        # Price
        # --------------------------------------------------------

        if breach_type == "PRICE":

            agreed = float(
                agreement.get(
                    "price",
                    0
                )
            )

            actual = float(
                measurements.get(
                    "price",
                    0
                )
            )

            if agreed <= 0:
                return "HIGH"

            ratio = actual / agreed

            if ratio >= 2.0:
                return "CRITICAL"

            if ratio >= 1.5:
                return "HIGH"

            if ratio >= 1.2:
                return "MEDIUM"

            return "LOW"

        # --------------------------------------------------------
        # CPU
        # --------------------------------------------------------

        if breach_type == "CPU":

            required = float(
                agreement.get(
                    "cpu",
                    0
                )
            )

            actual = float(
                measurements.get(
                    "cpu",
                    0
                )
            )

            if required <= 0:
                return "LOW"

            ratio = actual / required

            if ratio < 0.50:
                return "CRITICAL"

            if ratio < 0.75:
                return "HIGH"

            if ratio < 0.90:
                return "MEDIUM"

            return "LOW"

        # --------------------------------------------------------
        # MEMORY
        # --------------------------------------------------------

        if breach_type == "MEMORY":

            required = float(
                agreement.get(
                    "memory",
                    0
                )
            )

            actual = float(
                measurements.get(
                    "memory",
                    0
                )
            )

            if required <= 0:
                return "LOW"

            ratio = actual / required

            if ratio < 0.50:
                return "CRITICAL"

            if ratio < 0.75:
                return "HIGH"

            if ratio < 0.90:
                return "MEDIUM"

            return "LOW"

        return "MEDIUM"

    # ============================================================
    # CHECK SLA
    # ============================================================

    def check_sla(
        self,
        agreement,
        measurements
    ):
        """
        Automatically determines whether the SLA has been breached.

        The monitor independently detects the violation.

        Returned structure is compatible with
        RenegotiationManager.
        """

        # --------------------------------------------------------
        # SLA TERMS
        # --------------------------------------------------------

        min_availability = float(
            agreement.get(
                "min_availability",
                98.0
            )
        )

        max_latency = float(
            agreement.get(
                "max_latency",
                100.0
            )
        )

        agreed_price = float(
            agreement.get(
                "price",
                0.0
            )
        )

        required_cpu = float(
            agreement.get(
                "cpu",
                0
            )
        )

        required_memory = float(
            agreement.get(
                "memory",
                0
            )
        )

        # --------------------------------------------------------
        # ACTUAL MEASUREMENTS
        # --------------------------------------------------------

        availability = float(
            measurements.get(
                "availability",
                0
            )
        )

        latency = float(
            measurements.get(
                "latency",
                0
            )
        )

        price = float(
            measurements.get(
                "price",
                0
            )
        )

        cpu = float(
            measurements.get(
                "cpu",
                0
            )
        )

        memory = float(
            measurements.get(
                "memory",
                0
            )
        )

        # --------------------------------------------------------
        # VIOLATIONS
        # --------------------------------------------------------

        violations = []

        # Availability
        if availability < min_availability:

            violations.append({
                "type": "availability",
                "actual": availability,
                "required": min_availability,
                "message": (
                    f"Availability {availability}% is below "
                    f"required {min_availability}%"
                )
            })

        # Latency
        if latency > max_latency:

            violations.append({
                "type": "latency",
                "actual": latency,
                "required": max_latency,
                "message": (
                    f"Latency {latency} ms exceeds "
                    f"maximum {max_latency} ms"
                )
            })

        # Price
        if price > agreed_price:

            violations.append({
                "type": "budget",
                "actual": price,
                "required": agreed_price,
                "message": (
                    f"Price ${price:.4f}/hr exceeds "
                    f"agreed ${agreed_price:.4f}/hr"
                )
            })

        # CPU
        if cpu < required_cpu:

            violations.append({
                "type": "resource",
                "resource": "cpu",
                "actual": cpu,
                "required": required_cpu,
                "message": (
                    f"CPU {cpu} vCPU is below "
                    f"required {required_cpu} vCPU"
                )
            })

        # Memory
        if memory < required_memory:

            violations.append({
                "type": "resource",
                "resource": "memory",
                "actual": memory,
                "required": required_memory,
                "message": (
                    f"Memory {memory} GB is below "
                    f"required {required_memory} GB"
                )
            })

        # --------------------------------------------------------
        # BREACH STATUS
        # --------------------------------------------------------

        breached = (
            len(violations) > 0
        )

        # --------------------------------------------------------
        # DETERMINE TYPE + SEVERITY
        # --------------------------------------------------------

        if breached:

            breach_type = (
                self.determine_breach_type(
                    agreement,
                    measurements,
                    violations
                )
            )

            severity = (
                self.determine_severity(
                    agreement,
                    measurements,
                    breach_type
                )
            )

        else:

            breach_type = None
            severity = "NONE"

        # --------------------------------------------------------
        # RETURN COMPLETE RESULT
        # --------------------------------------------------------

        return {
            "breached": breached,

            "breach_type": breach_type,

            "severity": severity,

            "violations": violations,

            "measurement": measurements,
        }

    # ============================================================
    # DISPLAY RESULT
    # ============================================================

    def display_result(
        self,
        result
    ):

        print()

        # --------------------------------------------------------
        # HEALTHY
        # --------------------------------------------------------

        if not result["breached"]:

            print("=" * 72)
            print("SLA STATUS: HEALTHY")
            print("=" * 72)

            print(
                "All monitored SLA conditions are satisfied."
            )

            print("=" * 72)

            return

        # --------------------------------------------------------
        # BREACH
        # --------------------------------------------------------

        print("=" * 72)
        print("SLA BREACH DETECTED")
        print("=" * 72)

        print(
            f"Breach Type : "
            f"{result.get('breach_type', 'UNKNOWN')}"
        )

        print(
            f"Severity    : "
            f"{result.get('severity', 'UNKNOWN')}"
        )

        print()

        for violation in result["violations"]:

            print(
                f"  - {violation['message']}"
            )

        print("=" * 72)