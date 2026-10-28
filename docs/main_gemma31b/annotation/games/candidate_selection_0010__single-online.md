# candidate_selection_0010__single-online (candidate_selection)

## Round 1
- [5] **Daisuke**: I think we should look at the misrouted deliveries in the incident logs and the time lost to copying existing records to see where the real problems are.
- [6] **May**: I'll go with staffing of the coordination group and in-house developer availability. We can't just assume people have the time to actually build these things.
- [7] **Shunichi**: I'll check network coverage at customer plants and vendor licence pricing versus fixed-fee work. It's better to know the actual constraints before we get carried away.
- [8] **Ryuji**: I will look into the capital budget and software allowance, as well as the handling of vendor queries. We need to be clear on the financial boundaries first.
- [9] **Kenji**: I'll take the outcomes of the last three internal rollouts and the record of cross-unit standardization efforts. I want to see what actually worked in the past!
- [11] **May**: Does anyone else think we should check the coordination group's workload, or are we satisfied with my choice?
- [12] **Shunichi**: @May, your choice covers it. I'm more interested in whether the external environment even supports the ideas we're about to see.
- [13] **Ryuji**: I agree with Shunichi. We must ensure the funding source is compatible with the project's cost structure before we commit.
- [14] **Kenji**: I think it's great we're covering the budget and the staff, but I really believe the history of our rollouts will tell us which proposals are actually realistic!
- [16] **May**: I'm satisfied with our current list. It seems we've covered the budget, the people, and the technical side. I'll stick with my two.
- [17] **Shunichi**: I'm also satisfied. We have a comprehensive spread of data points. I'll stick with my selections.
- [18] **Ryuji**: I will also maintain my choices. It is prudent to have a clear picture of the budget and vendor interactions before we evaluate the candidates.
- [19] **Kenji**: Me too! I'm excited to see what the records show. I'll stick with my two choices.
- [20] **Daisuke**: I'll stick with mine as well. I think it's important to understand the daily losses before we decide.
## Round 2
- [35] **Daisuke**: It turns out we're losing nearly an hour a day to copying records, and there are several misrouted deliveries because different units have different addresses for the same firms.
- [36] **May**: That's a lot of wasted time, but my findings are worrying. Our in-house developers are tied up until Q3, and the coordination group is severely understaffed.
- [37] **Shunichi**: To add to that, network coverage at customer plants is unreliable, with some losing signal for whole afternoons, and vendor pricing for licenses scales up per person, which could get expensive.
- [38] **Ryuji**: The capital budget is frozen, though we have some room in the software allowance. Also, vendor queries are being handled inefficiently, with the same certificates requested multiple times.
- [39] **Kenji**: I found out that tools requiring daily entry from everyone were dropped in the last three rollouts, and most cross-unit standardization efforts ended without an owner. Only the tool room walkthroughs are still used!
- [40] **Daisuke**: @May, if the developers are busy and the coordination group is understaffed, we should be very careful about any proposal that requires a lot of internal setup or manual maintenance.
- [41] **May**: Exactly. We can't afford a project that adds more burden to the few people we have left, or one that relies on developers who aren't available.
- [42] **Shunichi**: @Ryuji, given the frozen capital budget and the per-head license costs I found, we should probably avoid any proposal that requires a large upfront investment or a scaling subscription model.
- [43] **Ryuji**: I agree. We should prioritize solutions that fit within the recurring software allowance and avoid those that would trigger a capital expenditure request we cannot fulfill.
- [44] **Kenji**: @Daisuke, your point about the daily losses is key, but we must remember that tools requiring everyone's daily input usually fail here. We need something that solves those problems without becoming another abandoned project.
- [45] **Daisuke**: I see your point, @Kenji. We need a solution that addresses the copying and delivery errors but doesn't rely on a high-maintenance daily routine that people will just stop doing.
- [46] **May**: And we must avoid anything that requires our in-house developers immediately. If a proposal needs a custom build right now, it's a non-starter.
- [47] **Shunichi**: @Ryuji, we should also be wary of any proposal that assumes seamless connectivity at customer sites, given the signal gaps I discovered. That could be a fatal flaw for certain types of apps.
- [48] **Ryuji**: That is a critical observation, @Shunichi. Any proposal relying on real-time cloud synchronization at customer plants would be fundamentally flawed and likely to fail in practice.
- [49] **Kenji**: I'm starting to think we need a project that is narrow in scope and has a clear owner, since the broad standardization efforts usually just vanish into thin air.
- [50] **Daisuke**: I agree with @Kenji. A focused tool that solves a specific, tangible problem—like the record copying or the address errors—seems much safer than a massive overhaul.
- [51] **May**: I agree. Let's look for something that doesn't require a huge team to maintain or a massive amount of developer time to launch.
- [52] **Shunichi**: I'll be looking for a proposal that avoids the per-head license trap and doesn't assume our technicians have a perfect signal in the field. That should narrow it down.
- [53] **Ryuji**: I will be looking for a proposal that fits within the software allowance and avoids capital expenditure, while addressing the inefficiencies in how we handle vendor and supplier data.
- [54] **Kenji**: I'll be looking for something that doesn't require everyone to use it every single day, or it'll just end up like the last three failures!
## Round 3
- [60] **Daisuke**: Looking at the candidates, the Supplier Data Hub seems to address the misrouted deliveries and the redundant vendor queries Ryuji mentioned, without requiring daily input from everyone.
- [61] **May**: The Supplier Data Hub sounds promising, but I'm worried about the developer availability. If it requires a custom build, we're stuck until Q3. Does it look like a vendor product or an in-house build?
- [62] **Shunichi**: The Field Service App is out because of the network gaps I found. The Supplier Data Hub is better, provided it doesn't use those per-head licenses that scale with every department.
- [63] **Ryuji**: The Supplier Data Hub aligns with the software allowance and solves the vendor query issue. It is a central repository, which suggests a more manageable cost structure than a per-head license.
- [64] **Kenji**: The Supplier Data Hub is a narrow tool for a specific problem, which fits the pattern of what actually survives here, unlike the Workflow Assistant which sounds like it requires daily entry from everyone.
- [65] **Daisuke**: @May, the Supplier Data Hub is a central repository for records, which might be easier to implement than a full app, and it directly fixes the address errors I found.
- [66] **May**: I'm still concerned about the coordination group, but a central hub for supplier records seems less demanding than a full-scale app or a training studio. It feels like the most sustainable option.
- [67] **Shunichi**: @Ryuji, if the Supplier Data Hub is a consolidated catalog, it likely avoids the connectivity issues of the Field Service App and the high maintenance of the Workflow Assistant. It seems the most rational choice.
- [68] **Ryuji**: I agree. It addresses the inefficiencies in vendor data handling and fits our financial constraints, making it the most logical and prudent selection among the candidates.
- [69] **Kenji**: I'm on board! It's a specific fix for a real problem, and it doesn't sound like it'll be abandoned like those broad standardization projects. I vote for the Supplier Data Hub.
- [70] **Daisuke**: I agree with everyone. It solves the daily losses I found without being too ambitious. I vote for the Supplier Data Hub.
- [71] **May**: It seems to be the only one that won't break our staff or our budget. I vote for the Supplier Data Hub.
- [72] **Shunichi**: It is the only proposal that survives the constraints we've identified. I vote for the Supplier Data Hub.
- [73] **Ryuji**: It is the most reasonable choice given the budget and the operational inefficiencies. I vote for the Supplier Data Hub.
### Vote
- Daisuke -> C
- May -> C
- Shunichi -> C
- Ryuji -> C
- Kenji -> C
## Result
- adopted: C
