# Agentic Cloud Management

## Investigating Multi-Agent Systems for Service Level Agreement Negotiation

A simulation-based multi-agent cloud management framework that uses autonomous software agents to negotiate, monitor, and manage Service Level Agreements (SLAs).

The system combines **Multi-Agent Systems (MAS)**, **BDI (Belief-Desire-Intention) reasoning**, **utility-based negotiation**, **SLA monitoring**, **simulated breach detection**, and **automatic renegotiation** to demonstrate an autonomous SLA lifecycle.

> **Important:** This project is a research simulation. It does not create, modify, or negotiate real SLAs with AWS, Azure, GCP, or Rackspace. Rackspace Spot public market pricing is used only as an external pricing input for the simulation.

---

## 📌 Project Overview

Cloud service selection involves multiple factors such as:

- Cost
- CPU resources
- Memory resources
- Network latency
- Service availability
- SLA requirements

Traditional cloud management approaches often rely on static rules or manual decisions.

This project investigates whether a system of autonomous software agents can negotiate service requirements, select suitable providers, monitor SLA compliance, detect simulated SLA violations, and automatically renegotiate when required.

The proposed framework models the cloud management process as an interaction between autonomous agents.

---

## 🎯 Objectives

The main objectives of this project are:

1. Develop a multi-agent framework for simulated SLA negotiation.
2. Implement BDI reasoning for autonomous agent decision-making.
3. Use utility-based decision-making to evaluate provider offers.
4. Select the highest-utility provider satisfying the customer's hard SLA constraints.
5. Simulate multi-round negotiation between customer and provider agents.
6. Create and persist simulated SLA agreements.
7. Monitor SLA compliance during the agreement lifecycle.
8. Simulate SLA breaches such as:
   - Availability degradation
   - Increased latency
   - Price increase
   - CPU reduction
   - Memory reduction
9. Automatically detect SLA violations.
10. Trigger simulated renegotiation after a detected breach.
11. Maintain agreement versions and negotiation history.
12. Use publicly available Rackspace Spot pricing as realistic external pricing input.

---

## 🏗️ System Architecture

The system consists of the following major components:

### Customer Agent

Represents the customer requesting cloud resources.

The Customer Agent maintains:

**Beliefs**
- Maximum budget
- Maximum latency
- Minimum availability
- Required CPU
- Required memory

**Desires**
- Low cost
- Good performance
- High availability
- Sufficient resources
- Successful agreement

**Intentions**
- Evaluate provider offers
- Negotiate
- Minimize cost
- Satisfy SLA requirements
- Reach an agreement

---

### Provider Agents

Each Provider Agent represents a simulated cloud service offer.

Provider agents maintain information such as:

- Market price
- CPU
- Memory
- Region
- Server class

Provider agents participate in simulated negotiation by:

- Making initial offers
- Generating counter-offers
- Evaluating customer proposals
- Accepting feasible proposals

---

### Negotiation Manager

The Negotiation Manager supervises the negotiation process.

It:

1. Receives provider offers.
2. Applies hard SLA constraints.
3. Calculates utility for feasible offers.
4. Ranks providers.
5. Selects high-utility candidates.
6. Conducts multi-round negotiation.
7. Determines the final agreed price.
8. Produces the simulated SLA agreement.

---

### Utility Engine

The Utility Engine evaluates provider offers using fixed weights.

| Criterion | Weight |
|---|---:|
| Cost | 0.40 |
| Resources | 0.25 |
| Latency | 0.20 |
| Availability | 0.15 |

The utility score is used to rank providers after hard SLA constraints have been satisfied.

### Hard SLA Constraints

An offer must satisfy:

```text
Price <= Maximum Budget
Latency <= Maximum Latency
Availability >= Minimum Availability
CPU >= Required CPU
Memory >= Required Memory
