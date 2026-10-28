# candidate_selection_0010__single-batch (candidate_selection)

## Round 1
- [5] **Daisuke**: I think we should look at the misrouted deliveries in the incident logs and time lost to copying existing records.
- [6] **May**: I'll check the staffing of the coordination group and in-house developer availability. We can't ignore the workload.
- [7] **Shunichi**: I'll take network coverage at customer plants and vendor licence pricing versus fixed-fee work. Let's see the actual constraints.
- [8] **Ryuji**: I will examine the capital budget and software allowance, as well as the handling of vendor queries.
- [9] **Kenji**: I want to see the outcomes of the last three internal rollouts and the record of cross-unit standardization efforts!
## Round 2
- [30] **Daisuke**: It seems people are wasting an hour a day copying records, and misrouted deliveries are happening because of inconsistent addresses.
- [31] **May**: Our developers are tied up until Q3 and the coordination group is understaffed. We can't just add more tasks.
- [32] **Shunichi**: Customer plant networks are unreliable and visitor approval is a nightmare. Also, per-head licensing is a potential cost trap.
- [33] **Ryuji**: The capital budget is frozen, though we have some software allowance. Vendor queries are also being handled redundantly.
- [34] **Kenji**: Past rollouts that required everyone's daily input failed, but narrow tools for specific trades survived. Standardization often lacks owners.
- [35] **Daisuke**: @Ryuji, if the capital budget is frozen, does that mean we can only afford software-based solutions?
- [36] **May**: @Shunichi, if the network is that bad, any app relying on a live connection will fail immediately.
- [37] **Shunichi**: Exactly. Any "field" solution needs to be very robust regarding offline access.
- [38] **Ryuji**: Yes, Daisuke. We are limited to the recurring software allowance for now.
- [39] **Kenji**: @May, if developers are busy, maybe we should look for something that doesn't require heavy custom coding?
- [40] **Daisuke**: The data duplication issue is a real daily loss. It's not just a theory.
- [41] **May**: I'm worried about who actually manages the tool. If the coordination group is empty, it'll just crash.
- [42] **Shunichi**: @Ryuji, the redundant vendor queries suggest a data synchronization problem, similar to what Daisuke found.
- [43] **Ryuji**: I agree. The inefficiency is systemic. We need a solution that fits the current budget and doesn't add overhead.
- [44] **Kenji**: We should avoid anything that requires "everyone" to use it daily, or it will be dropped like the last ones.
## Round 3
- [55] **Daisuke**: Candidate C, the Supplier Data Hub, addresses the misrouted deliveries and the redundant vendor queries Ryuji mentioned.
- [56] **May**: Candidate D, the Workflow Assistant, sounds like it helps the coordination group, but does it require too much developer time?
- [57] **Shunichi**: Candidate A, the Field Service App, mentions synchronization for records away from the network, which solves my coverage concern.
- [58] **Ryuji**: Candidate C fits the software allowance and solves the redundant query issue without needing a massive capital investment.
- [59] **Kenji**: Candidate B, the Training Studio, is a narrow tool for specific skills. Those are the ones that actually survive!
- [60] **Daisuke**: @Kenji, but the Training Studio doesn't stop the daily time loss from copying records. Candidate C does.
- [61] **May**: @Ryuji, would Candidate C require the in-house developers? If so, we have to wait until Q3.
- [62] **Shunichi**: @Daisuke, Candidate C is a central repository. It's safer than A if we can't guarantee plant access.
- [63] **Ryuji**: Candidate C is likely a configuration of existing software, fitting our allowance and solving the data duplication.
- [64] **Kenji**: I see the point, but Candidate C is a "standardization effort." Those usually fail without an owner.
- [65] **Daisuke**: But the cost of doing nothing is an hour a day per person in some offices.
- [66] **May**: I'm leaning toward C if it doesn't break the staff rota, but D would help the coordinators.
- [67] **Shunichi**: A is too risky given the network logs. C is the most rational choice for the company's current state.
- [68] **Ryuji**: C addresses the budget, the vendor redundancies, and the data errors. It is the most logical.
- [69] **Kenji**: If we can ensure it's not a "daily entry for everyone" chore, I can support C.
- [70] **Daisuke**: I vote for C.
- [71] **May**: I'll go with C as well, provided it's managed centrally.
- [72] **Shunichi**: C is my choice.
- [73] **Ryuji**: I vote for C.
- [74] **Kenji**: I'll join the majority. C it is.
### Vote
- Daisuke -> C
- May -> C
- Shunichi -> C
- Ryuji -> C
- Kenji -> C
## Result
- adopted: C
