# Editorial workflow

`radar.html` contains the dated news cards and their original source links. `decisiones.html` contains the decision-point rules and the manual status for each one. They are separate pages so that one can be revised without editing the portfolio and scenario tools.

For every update, read the source in full and check its date. Edit the fact, timestamp, source link and editorial cutoff in `radar.html`. Then review each rule in `decisiones.html`: change its status only when every condition listed in the rule has source evidence; update the review timestamp, explanation and relevant source links. If evidence is missing, leave the state pending. Check the changed page on mobile before publishing. An old dated rule must not be presented as current. This is a manual editorial workflow, not a live feed, monitoring service, automatic trigger or trading signal.

The prototype's portfolio and scenarios are user-entered hypothetical calculations. Public editorial and tools require no registration. The proposed account layer would add personal trigger alerts, saved portfolios and analysis on those weights; none of that exists in the current static prototype. Signup remains disabled pending an account service, privacy setup, persistence and actual alert delivery.

## Radar precatalizador

`precatalizador/universe.json` is a **manual seed list of five**, not a universal scanner. `scanner.py` checks seven conditions with market and FX snapshots; financial amounts and event dates were manually copied from primary releases and require editorial review. `weekly.py` runs every Monday around 09:17 UTC on GitHub Actions and commits the refreshed `scan.json`. GitHub schedules can be delayed or disabled for inactivity, so verify the run history. Only a ticker moving from below 6/7 to at least 6/7 sends Telegram, using repository secrets. An existing 6/7 is not sent anew each week. A partial data error shows no score and does not alert; total failure leaves the prior snapshot. Do not conflate a 6/7 with an investment signal: unresolved dilution remains common, and scores are evidence completeness only.

To expand coverage, add a name only after verifying the financial and catalyst primary sources and economic rights. Recheck dates and dilution notes as releases change. Market data comes from Yahoo via yfinance for research, not execution or a licensed quote service.
