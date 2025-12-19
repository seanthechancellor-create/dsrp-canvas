# CIPP/E Exam Prep using DSRP 4-8-3 Framework
## Spaced Repetition Study Guide for RemNote

**Goal**: 100% on IAPP CIPP/E using 80/20 Rule + DSRP 4-8-3
**Strategy**: Focus on ~20% of concepts that appear in ~80% of exam questions

---

## HIGH-PRIORITY CONCEPTS (The 20% that matters most)

### 1. Personal Data
Pattern:: D (Distinction)
Identity:: Any information relating to an identified or identifiable natural person, includes name, ID number, location data, online identifiers, biometric data, genetic data
Other:: Anonymous data, aggregated statistics, data about legal entities (companies), deceased persons' data (varies by member state), truly anonymized data
Boundary:: Identifiability test - can a natural person be directly or indirectly identified?
#DSRP #Distinction #GDPR #Article4

### 2. What is Personal Data NOT?
Answer:: Anonymous data that cannot be re-identified, corporate/business data, data about deceased persons (generally), purely statistical aggregates with no individual linkage
#DSRP #Distinction #GDPR

---

### 3. GDPR (Zoom Out - Context)
Pattern:: S (System)
Part of:: EU Data Protection Framework, which includes ePrivacy Directive, Law Enforcement Directive, EU Charter of Fundamental Rights Article 8
Context:: Replaces 1995 Data Protection Directive (95/46/EC), harmonizes data protection across EU/EEA
#DSRP #System #ZoomOut #GDPR

### 4. GDPR Structure (Zoom In - Parts)
Pattern:: S (System)
Parts:: 11 Chapters, 99 Articles, 173 Recitals
Key Chapters:: Ch.1 General Provisions, Ch.2 Principles, Ch.3 Data Subject Rights, Ch.4 Controller/Processor, Ch.5 International Transfers, Ch.6 Supervisory Authorities, Ch.7 Cooperation, Ch.8 Remedies, Ch.9 Specific Situations, Ch.10 Delegated Acts, Ch.11 Final Provisions
#DSRP #System #ZoomIn #GDPR

---

### 5. Six Legal Bases for Processing
Pattern:: S (System)
Parts:: Consent (Art.6(1)(a)), Contract (Art.6(1)(b)), Legal Obligation (Art.6(1)(c)), Vital Interests (Art.6(1)(d)), Public Task (Art.6(1)(e)), Legitimate Interests (Art.6(1)(f))
Critical Note:: Must identify legal basis BEFORE processing, cannot change basis retroactively
#DSRP #System #ZoomIn #Article6 #LegalBasis

### 6. Consent Requirements
Pattern:: D (Distinction)
Identity:: Freely given, specific, informed, unambiguous, clear affirmative action, withdrawable at any time, as easy to withdraw as to give
Other:: Pre-ticked boxes (NOT valid), silence (NOT valid), bundled consent (NOT valid), consent under duress (NOT valid), implied consent (NOT valid for GDPR)
Boundary:: Active vs passive - consent requires affirmative action
#DSRP #Distinction #Consent #Article7

---

### 7. Data Controller vs Data Processor
Pattern:: D (Distinction)
Identity (Controller):: Determines purposes and means of processing, bears primary compliance responsibility, must implement appropriate measures
Identity (Processor):: Processes on behalf of controller, follows controller instructions, requires written contract (Art.28)
Boundary:: Who decides WHY and HOW data is processed? Controller = decision maker, Processor = executor
#DSRP #Distinction #Article4 #Article28

### 8. Controller-Processor Relationship
Pattern:: R (Relationship)
Action:: Controller instructs and oversees
Reaction:: Processor implements and reports
Key Contract Terms:: Subject matter, duration, nature/purpose, data types, categories of subjects, controller obligations, processor obligations
#DSRP #Relationship #RDSBarbell #Article28

---

### 9. Data Subject Rights (The 8 Rights)
Pattern:: S (System)
Parts:: Right to Information (Art.13-14), Right of Access (Art.15), Right to Rectification (Art.16), Right to Erasure (Art.17), Right to Restriction (Art.18), Right to Data Portability (Art.20), Right to Object (Art.21), Rights re: Automated Decision-Making (Art.22)
Critical:: Must respond within 1 month (extendable by 2 months for complex requests)
#DSRP #System #ZoomIn #DataSubjectRights #Chapter3

### 10. Right to Erasure ("Right to be Forgotten")
Pattern:: D (Distinction)
Identity:: Applies when: consent withdrawn, data no longer necessary, unlawful processing, legal obligation to erase, objection with no overriding grounds
Other:: Does NOT apply when: freedom of expression, legal obligation to retain, public health, archiving/research, legal claims
Boundary:: Balancing individual rights vs legitimate retention needs
#DSRP #Distinction #Article17 #Erasure

---

### 11. Data Breach Notification
Pattern:: R (Relationship - Web of Causality)
Cause:: Personal data breach (confidentiality, integrity, or availability)
Effects (Level 1):: Notify supervisory authority within 72 hours (if risk to rights)
Effects (Level 2):: Notify affected individuals without undue delay (if high risk)
Effects (Level 3):: Document all breaches in internal register
#DSRP #Relationship #WoC #Article33 #Article34 #Breach

### 12. What Causes Data Breaches?
Pattern:: R (Relationship - Web of Anticausality)
Effect:: Data breach occurs
Root Causes:: Phishing attacks, misconfigured systems, lost/stolen devices, insider threats, inadequate access controls, unpatched vulnerabilities, third-party failures
Prevention:: Technical measures (encryption, access controls) + Organizational measures (training, policies)
#DSRP #Relationship #WAoC #DataBreach #Security

---

### 13. International Data Transfers
Pattern:: D (Distinction)
Identity (Allowed):: Adequacy decisions (Art.45), Standard Contractual Clauses (Art.46), Binding Corporate Rules (Art.47), Derogations (Art.49)
Other (Not Allowed):: Transfers to non-adequate countries without safeguards, reliance on invalidated mechanisms (Privacy Shield post-Schrems II)
Boundary:: Is there "essentially equivalent" protection in the destination country?
#DSRP #Distinction #Chapter5 #InternationalTransfers #SchremsII

### 14. Adequacy Decisions (Current List)
Pattern:: S (System)
Parts:: Andorra, Argentina, Canada (commercial), Faroe Islands, Guernsey, Israel, Isle of Man, Japan, Jersey, New Zealand, South Korea, Switzerland, UK, Uruguay, EU-US Data Privacy Framework (2023)
Note:: Adequacy allows free flow of data without additional safeguards
#DSRP #System #ZoomIn #Article45 #Adequacy

---

### 15. DPO Requirements
Pattern:: D (Distinction)
Identity (Required):: Public authority, core activities = large-scale systematic monitoring, core activities = large-scale special category data processing
Other (Not Required):: Small businesses without systematic monitoring, one-off processing, non-core processing activities
DPO Qualities:: Expert knowledge, independent, report to highest management, no conflict of interest
#DSRP #Distinction #Article37 #DPO

### 16. DPO Tasks
Pattern:: S (System)
Parts:: Inform/advise controller, monitor compliance, advise on DPIAs, cooperate with supervisory authority, act as contact point
Independence:: Cannot be dismissed/penalized for performing tasks, no instructions regarding exercise of tasks
#DSRP #System #ZoomIn #Article39 #DPO

---

### 17. DPIA (Data Protection Impact Assessment)
Pattern:: R (Relationship - Web of Causality)
Cause:: High-risk processing (systematic evaluation, large-scale special categories, systematic public monitoring)
Effects:: Must conduct DPIA before processing, consult DPO, consult supervisory authority if high residual risk
Content:: Description of processing, necessity assessment, risk assessment, mitigation measures
#DSRP #Relationship #WoC #Article35 #DPIA

---

### 18. Supervisory Authority Powers
Pattern:: S (System)
Parts (Investigative):: Order information, conduct audits, review certifications, notify of violations
Parts (Corrective):: Issue warnings, reprimands, orders to comply, impose processing bans, order rectification/erasure, suspend data flows, impose fines
Parts (Advisory):: Issue opinions, approve BCRs, accredit certification bodies
#DSRP #System #ZoomIn #Article58 #Enforcement

### 19. GDPR Fines Structure
Pattern:: D (Distinction)
Identity (Tier 1 - Lower):: Up to €10M or 2% global turnover - for violations of controller/processor obligations, certification bodies, monitoring bodies
Identity (Tier 2 - Higher):: Up to €20M or 4% global turnover - for violations of principles, data subject rights, international transfers, non-compliance with orders
Calculation Factors:: Nature/gravity, intentional/negligent, mitigation, previous violations, cooperation, data categories, notification, certifications
#DSRP #Distinction #Article83 #Fines #Enforcement

---

### 20. Key GDPR Principles (Article 5)
Pattern:: S (System)
Parts:: Lawfulness/fairness/transparency, Purpose limitation, Data minimisation, Accuracy, Storage limitation, Integrity/confidentiality, Accountability
Accountability:: Controller must demonstrate compliance (documentation, records, policies)
#DSRP #System #ZoomIn #Article5 #Principles

---

## 80/20 EXAM STRATEGY

### Focus Areas (High Exam Weight):
1. **Article 4 Definitions** - Personal data, controller, processor, consent
2. **Article 5 Principles** - The 7 principles
3. **Article 6 Legal Bases** - The 6 bases, especially consent and legitimate interests
4. **Chapter 3 Data Subject Rights** - All 8 rights, timelines, exceptions
5. **Article 28 Processor Requirements** - Contract terms
6. **Articles 33-34 Breach Notification** - 72-hour rule, when to notify subjects
7. **Article 35 DPIA** - When required, what to include
8. **Chapter 5 International Transfers** - Mechanisms, Schrems II impact
9. **Article 83 Fines** - Two tiers, calculation factors

### Study Method with DSRP:
1. **D (Distinction)**: For EVERY concept, know what it IS and IS NOT
2. **S (System)**: Know parts (zoom-in) and context (zoom-out)
3. **R (Relationship)**: Understand cause→effect chains
4. **P (Perspective)**: Consider DPA view, controller view, data subject view

### Spaced Repetition Schedule:
- Day 1: Learn new cards
- Day 2: Review
- Day 4: Review
- Day 7: Review
- Day 14: Review
- Day 30: Review

---

## QUICK REFERENCE - GDPR Numbers to Memorize

| Number | Meaning |
|--------|---------|
| 72 hours | Breach notification to authority |
| 1 month | Response time for data subject requests |
| 2 months | Extension for complex requests |
| €10M/2% | Lower tier fine |
| €20M/4% | Higher tier fine |
| 16 years | Default age for child consent (member states can lower to 13) |
| 3 years | Records retention for processing activities |

---

*Generated with DSRP Canvas 4-8-3 Framework*
*For IAPP CIPP/E Certification Exam Prep*
