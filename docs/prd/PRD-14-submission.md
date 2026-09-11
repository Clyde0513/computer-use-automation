Objective

Produce exactly the submission structure

/README.md

Must include:

What this is
Architecture overview
Prerequisites
Installation
Configuration/API key
Running without live services where applicable
Starting proxy app
Running discovery
Running replay
Triggering failure demonstration
Triggering human intervention
Tests
Repository structure
Security notes

/REPORT.md

The assignment requires exactly these seven headings:

1. Architecture
2. Artifact schema
3. Determinism & error handling
4. Heterogeneity & multi-tenant
5. Escalation & handoff
6. Safety
7. Cuts

/evidence/

Must contain:

1. example capability artifact
2. discovery log
3. successful replay log
4. exceptional replay log
5. failure screenshot/snapshot where appropriate

Explicitly asks for evidence from discovery and replay and recommends demonstrating an exceptional replay case

Final repository audit

Check:

[ ] public repository
[ ] README.md
[ ] REPORT.md
[ ] evidence/
[ ] real discovery evidence
[ ] replay evidence
[ ] no secrets
[ ] no real PII
[ ] clean clone works
[ ] exact commands tested

Acceptance criteria
 All mandatory deliverables exist.
 REPORT uses exact headings.
 README demo commands actually work.
 Evidence reflects genuine runs.
 Repository contains no credentials.
 Fresh-clone setup verified.