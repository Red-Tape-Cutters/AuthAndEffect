# Use Cases

These use cases are consolidated from the user stories in `design/user_stories.md`. Each use case groups users who share the same underlying goal, even if their roles differ. The source personas are listed under each one.

------------------------------------------------------------------------

# Use Case 1: Compare Insurers to Make a Coverage or Care Decision

### Who is the User?

-   **Persona/Role:** Decision-makers choosing or navigating insurance: individual consumers (Emma, elderly patient; a member of the public; a non-native English speaker; Mario's brother; Julia, a patient who was denied), employers and benefits staff (David, benefits counselor; an HR professional), patient advocates (Linda; Sheila), and provider staff (a primary care provider; a doctor; Rob, patient financial services specialist)
-   **Context:** People who need to pick a plan, advise someone else on a plan, or anticipate how an insurer will handle a request. They care about practical answers, not the underlying data.

### What Do They Want to Do with the Tool?

-   **Primary Tasks:**
    -   Compare insurers and plans on denial rates, appeal overturn rates, approval rates by treatment, and decision times.
    -   Understand how prior authorization works and what a plan is likely to cover.
    -   Use the comparison to choose a plan, advise a client or employee, or set expectations with a patient.
-   **Operational Workflows:**
    -   *Standard Operations:* Select the insurers or plans of interest, view a simple side-by-side or ranked comparison, and export or share the result (e.g., to Excel or a slide for leadership, or in a meeting with a client).
    -   *Edge/Exception Operations:* When an insurer has too little data for a reliable rate, a treatment isn't listed, or insurers report in different units, rely on the tool's caveats, search across similar treatments, and use standardized values rather than raw numbers.

### What Needs and Desires Do They Have for the Tool?

-   **Functional Needs:** Ranked and side-by-side comparisons of plans and insurers; measures standardized to the same unit; plain-language caveats shown next to the numbers; search by treatment; exports and simple charts; translated options for non-English speakers; works on locked-down work computers.
-   **Desires / Experience Preferences:** Simple, fast, and intuitive, with plain language and no need to understand the underlying data.

### What is Their Skill Level?

-   **Technical Proficiency:** Low to Medium (ranges from people with little experience using interactive platforms to staff comfortable with Excel or basic Python)
-   **Domain Knowledge:** Ranges from little knowledge of insurance terms (consumers) to deep practical knowledge of enrollment, benefits, appeals, or clinical approval processes (advocates, HR, providers).

------------------------------------------------------------------------

# Use Case 2: Analyze the Data for Research, Reporting, or Learning

### Who is the User?

-   **Persona/Role:** Analysts who produce their own findings: researchers (Maria, health policy researcher; Helen, PhD student in health policy), journalists (Tom, data journalist; Ava, journalist), and students (Priya, data science master's student; Mike, health economics PhD student)
-   **Context:** Users who download or query the data to produce briefs, papers, news stories, or course projects, and who need numbers they can defend in public.

### What Do They Want to Do with the Tool?

-   **Primary Tasks:**
    -   Download the cleaned dataset or query it directly.
    -   Compute their own statistics, such as enrollment-weighted denial rates across Medicare Advantage parent companies or state-level rankings.
    -   Produce tables and charts for a publication or project.
-   **Operational Workflows:**
    -   *Standard Operations:* Install the package or open a notebook, load the data as one consistent table, read the data dictionary, filter by insurer, state, and year, and export results.
    -   *Edge/Exception Operations:* When a value is missing, suspicious, or can't support a claim, trace it back to the insurer's original report and decide whether to exclude it or add a caveat.

### What Needs and Desires Do They Have for the Tool?

-   **Functional Needs:** One tidy table with a clear data dictionary; enrollment weighting; a source link from every number to the original report; flexibility to choose variables; publication-ready charts; a clear statement of what the data cannot show.
-   **Desires / Experience Preferences:** Accurate and citable without extra cleaning; easy enough for occasional coders while still allowing exploration.

### What is Their Skill Level?

-   **Technical Proficiency:** Medium to High (from running a prepared notebook to writing pandas code)
-   **Domain Knowledge:** Ranges from expert knowledge of prior authorization policy (researchers) to general data and storytelling skills (journalists, students).

------------------------------------------------------------------------

# Use Case 3: Monitor and Benchmark Insurer Performance

### Who is the User?

-   **Persona/Role:** Oversight and industry users: regulators and policymakers (James, state insurance regulator's analyst; a lawmaker) and insurers (an insurance company C-suite executive)
-   **Context:** Users who judge insurers against peers or national averages, either to decide where to intervene or to see how their own company compares.

### What Do They Want to Do with the Tool?

-   **Primary Tasks:**
    -   Compare insurers in a state or peer group against national averages.
    -   Identify outliers and insurers that may need follow-up.
    -   Confirm that insurers report the information they are required to provide.
-   **Operational Workflows:**
    -   *Standard Operations:* Select an insurer or state, view enrollment-weighted comparisons against benchmarks, and review summary charts.
    -   *Edge/Exception Operations:* When an insurer is an outlier or is missing required information, flag it for a request for more information or internal review.

### What Needs and Desires Do They Have for the Tool?

-   **Functional Needs:** Integration with CMS enrollment data so large insurers count more; state, peer, and national benchmarks; outlier detection; reporting-completeness checks.
-   **Desires / Experience Preferences:** Quick, high-level visual summaries that are easy to reference.

### What is Their Skill Level?

-   **Technical Proficiency:** Low to High (from a lawmaker with no technical skills to an analyst who uses Python occasionally)
-   **Domain Knowledge:** Strong knowledge of insurance regulation, reporting requirements, or insurer operations.

------------------------------------------------------------------------

# Use Case 4: Verify the Accuracy of the Data

### Who is the User?

-   **Persona/Role:** Data quality analysts (Sarah, analyst at a health research firm; Jackson, CMS data analyst)
-   **Context:** Analysts who must confirm the data is correct before it is used in published work or regulatory review.

### What Do They Want to Do with the Tool?

-   **Primary Tasks:**
    -   Check whether values were transcribed correctly from the source reports.
    -   Find missing required fields and outlier values.
-   **Operational Workflows:**
    -   *Standard Operations:* Run validation checks and review a report of flagged values.
    -   *Edge/Exception Operations:* When a value fails a check (e.g., a percentage that doesn't match its counts), inspect it against the original report.

### What Needs and Desires Do They Have for the Tool?

-   **Functional Needs:** Automatic flags for inconsistent, missing, and outlier values; traceability to source documents.
-   **Desires / Experience Preferences:** Suspicious values are surfaced, never silently dropped; ability to dig deeply into the data.

### What is Their Skill Level?

-   **Technical Proficiency:** Medium to High
-   **Domain Knowledge:** Experienced in data QA/QC; knows SQL and basic Python; familiar with CMS reporting requirements.

------------------------------------------------------------------------

# Use Case 5: Maintain and Extend the Dataset

### Who is the User?

-   **Persona/Role:** Project maintainer (Kevin, software developer)
-   **Context:** A developer responsible for keeping the dataset current as new insurers and reporting years appear.

### What Do They Want to Do with the Tool?

-   **Primary Tasks:**
    -   Add a new insurer or a new year of reports.
-   **Operational Workflows:**
    -   *Standard Operations:* Add a registry entry and a small parser for the new source, then run the test suite.
    -   *Edge/Exception Operations:* When an insurer changes its report format, update the parser and rely on tests to catch regressions.

### What Needs and Desires Do They Have for the Tool?

-   **Functional Needs:** A modular registry and parser design; automated tests covering parsing and validation.
-   **Desires / Experience Preferences:** Adding a source takes minimal code and no rewrite, and tests catch mistakes.

### What is Their Skill Level?

-   **Technical Proficiency:** Expert
-   **Domain Knowledge:** Advanced Python, git, and pytest; understands the project's data pipeline.
