# Interview playbook: how to use this project

The project exists to answer one question for the hiring manager: *can this person do the job on day one?*
Use it to show judgment, not to show off tooling.

## The 30-second version

"I built a working model of this role on synthetic data calibrated to Palo Alto Networks' public numbers.
It covers all five responsibilities in the job description. The headline: in this book, the SASE gap is
a coverage problem, not a demand problem. Territories without a specialist attach at 12% against a
modeled 29%. Two win-rate plays, SD-WAN in competitive deals and renewal timing, close most of the FY27
gap without headcount, and four hires close the rest instead of fourteen. The Market page is real
public data: Palo Alto's SASE ARR is growing about twice as fast as the SASE market."

## Say "synthetic" early, then move on

Open with it so nobody feels misled: the accounts and deals are simulated, the public figures are
cited, and every planted pattern is disclosed in the methodology. Then focus on the method.

## A three-minute demo path

1. **Briefing** (30 seconds): read the headline and the three findings. Stop there if time is short.
2. **Revenue intelligence, Attach and whitespace** (45 seconds): the scatter. Red dots below the line
   are uncovered territories. "The model was trained only where coverage is good, so it tells us what
   attach should look like."
3. **Planning simulator** (60 seconds): select Load recommended plan, then drag hiring lead time to
   six months and show attainment drop. "This is the conversation I'd want with Finance."
4. **Executive layer** (30 seconds): the weekly business review that drafts itself. Switch the week.
5. **Close** (15 seconds): "Everything reconciles: the app and the Python pipeline are tested to
   produce the same numbers."

## Questions to expect, and strong answers

**Why synthetic data?** Real CRM data is confidential. I calibrated scale and growth to public
figures (SASE ARR of $1.6B growing 40%, SASE bookings up 40% in FY26) and disclosed every planted
pattern, so the value is the method, which runs unchanged on a real Salesforce export.

**Is any of this real?** The deals are synthetic, because real CRM data is confidential. The Market
context page is real: company earnings releases, Dell'Oro market figures, SEC filings, CISA's catalog
of exploited vulnerabilities, and Census business counts, with every figure linked to its source.
"Synthetic deals, real market" is the one-line version.

**How do you know coverage causes attach, and it's not just that covered territories were better?**
I don't, from this data alone. Coverage could reflect where leadership already saw demand. The right
test is a staggered pilot: add specialist coverage to half of the eligible uncovered territories,
hold the other half out, and compare attach after two quarters.

**Why logistic regression instead of gradient boosting?** It scored higher on cross-validated AUC
(0.76 against 0.73) and it's explainable to a sales leader: each driver has a direction and a size.

**Is the SD-WAN effect real?** Raw win rates can mislead because the sellers who bundle also have
better coverage. I re-estimated it with a logistic regression controlling for coverage, segment,
renewal timing, and source; the effect held (22% to 43%). In real data I'd confirm it with win/loss
interviews before changing the playbook.

**How did you size the win-rate levers?** From the deal-level effects times a realistic behavior
change: bundle rate in SSE-rival deals from 46% to 75%, renewal-timed deals from 28% to 50%. That's
about 2.8 and 2.3 points of blended win rate.

**What's the weakest part?** Three things: stage history is simplified to the current stage;
prices are illustrative; and productivity credits all covered-territory bookings to specialists,
though core sellers contribute too. I'd fix all three first with real data.

**How would you adapt this to our data in the first 30 days?** Map the Salesforce objects (Account,
Opportunity, field history for slips and stage changes, territory assignments) into BigQuery, agree
on the metric definitions with Sales Ops and Finance before building anything, and run the
data-quality checks on the real export. The SQL in `sql/` is the starting point.

**Tell me about your experience with SASE.** Be direct: I haven't sold or operated SASE. What I
bring is the operating system around it, which I've built in enterprise B2B (reference the upGrad
pipeline and launch work), plus a fast ramp: this project is how I learned the category.

## By interview type

- **Hiring manager:** lead with the memo and the planning simulator. They care about judgment and
  the FY27 plan.
- **Cross-functional (Sales, Product Marketing, Sales Ops):** lead with the weekly business review
  and the launch kit. Show you make their week easier.
- **Case or presentation round:** present `docs/SASE_GTM_readout.pptx` (about 12 minutes; the speaker notes
  are your script). Short on time? Present slides 1, 2, 8, and 11, and keep 12 for questions.

## Guardrails

- Never present a synthetic number as a Palo Alto Networks number. Use the cited public figures for
  anything about the real business.
- Say "in this model" or "in this dataset" when quoting results.
- Don't claim causality the data can't support; offer the pilot design instead.
- Never use the CISA vulnerability data to knock a competitor. Every edge vendor, Palo Alto Networks
  included, is in it. The argument is architectural: fewer internet-exposed appliances to patch.
- ARR definitions differ by company. Say "about twice the market," never a precise multiple.
