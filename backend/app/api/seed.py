"""
Seed API for populating the knowledge base with sample concepts.
Useful for testing and demonstration purposes.
"""

from fastapi import APIRouter
from pydantic import BaseModel
import uuid

router = APIRouter()

# Sample CIPP/E concepts with full DSRP 4-8-3 analyses
CIPP_E_SEED_DATA = [
    {
        "id": "personal-data",
        "name": "Personal Data",
        "description": "Any information relating to an identified or identifiable natural person (GDPR Article 4)",
        "domain": "CIPP/E",
        "topic": "GDPR Fundamentals",
        "analyses": [
            {
                "move": "is-is-not",
                "pattern": "D",
                "elements": {
                    "identity": "Name, ID number, location data, online identifiers, biometric data, genetic data, health data, any info that can identify a natural person directly or indirectly",
                    "other": "Anonymous data, aggregated statistics, data about legal entities (companies), deceased persons' data (varies by member state), truly anonymized data that cannot be re-identified",
                    "boundary": "Identifiability test - can a natural person be directly or indirectly identified from the data?"
                },
                "reasoning": "Personal data is distinguished by whether it can identify a living natural person. The boundary is identifiability, not sensitivity."
            },
            {
                "move": "zoom-in",
                "pattern": "S",
                "elements": {
                    "parts": ["Direct identifiers (name, ID)", "Indirect identifiers (location, behavior)", "Special categories (health, biometric)", "Online identifiers (IP, cookies)", "Pseudonymized data"],
                    "whole": "Personal Data"
                },
                "reasoning": "Personal data contains multiple categories, each with different handling requirements under GDPR."
            },
            {
                "move": "zoom-out",
                "pattern": "S",
                "elements": {
                    "whole": "EU Data Protection Framework (GDPR, ePrivacy, LED, Charter Art.8)",
                    "context": "Personal data is the core subject matter that the entire framework aims to protect"
                },
                "reasoning": "Personal data sits at the center of the EU data protection ecosystem."
            }
        ]
    },
    {
        "id": "gdpr",
        "name": "GDPR",
        "description": "General Data Protection Regulation - EU regulation on data protection and privacy",
        "domain": "CIPP/E",
        "topic": "GDPR Fundamentals",
        "analyses": [
            {
                "move": "zoom-in",
                "pattern": "S",
                "elements": {
                    "parts": ["Chapter 1: General Provisions", "Chapter 2: Principles (Art.5)", "Chapter 3: Data Subject Rights", "Chapter 4: Controller/Processor Obligations", "Chapter 5: International Transfers", "Chapter 6: Supervisory Authorities", "Chapter 7: Cooperation", "Chapter 8: Remedies/Penalties", "Chapter 9: Specific Situations", "Chapter 10: Delegated Acts", "Chapter 11: Final Provisions"],
                    "whole": "GDPR"
                },
                "reasoning": "GDPR is structured into 11 chapters, 99 articles, and 173 recitals. Understanding the structure helps navigate compliance requirements."
            },
            {
                "move": "zoom-out",
                "pattern": "S",
                "elements": {
                    "whole": "EU Data Protection Framework",
                    "context": "GDPR replaced the 1995 Data Protection Directive (95/46/EC), works alongside ePrivacy Directive and Law Enforcement Directive"
                },
                "reasoning": "GDPR doesn't exist in isolation - it's part of a broader framework including ePrivacy (cookies, e-marketing) and LED (law enforcement)."
            },
            {
                "move": "woc",
                "pattern": "R",
                "elements": {
                    "cause": "GDPR",
                    "effects": [
                        {"effect": "Harmonized data protection across EU/EEA", "level": 1},
                        {"effect": "Extraterritorial reach to non-EU companies", "level": 1},
                        {"effect": "Significant fines (up to 4% global turnover)", "level": 1},
                        {"effect": "Global influence on privacy legislation (CCPA, LGPD)", "level": 2},
                        {"effect": "Growth of privacy professional industry", "level": 2}
                    ]
                },
                "reasoning": "GDPR's effects extend beyond direct compliance to global privacy norms."
            }
        ]
    },
    {
        "id": "consent",
        "name": "Consent",
        "description": "One of six legal bases for processing under GDPR Article 6(1)(a)",
        "domain": "CIPP/E",
        "topic": "Legal Bases",
        "analyses": [
            {
                "move": "is-is-not",
                "pattern": "D",
                "elements": {
                    "identity": "Freely given, specific, informed, unambiguous indication by statement or clear affirmative action, withdrawable at any time, as easy to withdraw as to give",
                    "other": "Pre-ticked boxes (NOT valid), silence or inactivity (NOT valid), bundled consent (NOT valid), consent obtained under duress or power imbalance (NOT valid), implied consent (NOT valid for GDPR)",
                    "boundary": "Active vs passive - consent requires a clear affirmative action demonstrating agreement"
                },
                "reasoning": "GDPR consent has strict requirements. Many practices valid under previous laws are no longer acceptable."
            },
            {
                "move": "zoom-out",
                "pattern": "S",
                "elements": {
                    "whole": "Six Legal Bases for Processing (Article 6)",
                    "context": "Consent is just one of six bases: Consent, Contract, Legal Obligation, Vital Interests, Public Task, Legitimate Interests"
                },
                "reasoning": "Organizations should not default to consent - other bases may be more appropriate and sustainable."
            },
            {
                "move": "p-circle",
                "pattern": "P",
                "elements": {
                    "perspectives": [
                        {"point": "Data Subject", "view": "Empowerment and control over personal data, but consent fatigue is real"},
                        {"point": "Controller", "view": "Flexible but fragile - can be withdrawn anytime, requires record-keeping"},
                        {"point": "DPA", "view": "High standard to meet, closely scrutinized, often finds consent invalid"}
                    ]
                },
                "reasoning": "Different stakeholders view consent differently - it's not always the best choice for controllers despite seeming intuitive."
            }
        ]
    },
    {
        "id": "controller-processor",
        "name": "Controller vs Processor",
        "description": "Key distinction in GDPR - who determines purposes vs who processes on behalf",
        "domain": "CIPP/E",
        "topic": "Roles & Responsibilities",
        "analyses": [
            {
                "move": "is-is-not",
                "pattern": "D",
                "elements": {
                    "identity": "Controller: determines purposes AND means of processing, bears primary compliance responsibility. Processor: processes personal data on behalf of controller, follows controller instructions",
                    "other": "Controller is NOT just whoever holds the data. Processor is NOT automatically the outsourced party. Joint controllers share determination of purposes/means",
                    "boundary": "WHO decides WHY (purpose) and HOW (means) data is processed? Decision-maker = Controller, Executor = Processor"
                },
                "reasoning": "The distinction is functional, not contractual. Actual control over purposes/means determines the role."
            },
            {
                "move": "rds-barbell",
                "pattern": "R",
                "elements": {
                    "action": "Controller instructs and oversees",
                    "reactions": ["Processor implements instructions", "Processor reports breaches to controller", "Processor assists with DPIA", "Processor deletes/returns data at end", "Processor allows audits"]
                },
                "reasoning": "The relationship is defined by instruction flow and accountability chain."
            },
            {
                "move": "zoom-in",
                "pattern": "S",
                "elements": {
                    "parts": ["Article 28 Contract Requirements", "Subject matter & duration", "Nature & purpose of processing", "Types of personal data", "Categories of data subjects", "Controller obligations", "Processor obligations", "Sub-processor rules"],
                    "whole": "Controller-Processor Relationship"
                },
                "reasoning": "Article 28 mandates specific contract terms - this is an exam favorite."
            }
        ]
    },
    {
        "id": "data-subject-rights",
        "name": "Data Subject Rights",
        "description": "The 8 rights granted to individuals under GDPR Chapter 3",
        "domain": "CIPP/E",
        "topic": "Data Subject Rights",
        "analyses": [
            {
                "move": "zoom-in",
                "pattern": "S",
                "elements": {
                    "parts": ["Right to Information (Art.13-14)", "Right of Access (Art.15)", "Right to Rectification (Art.16)", "Right to Erasure (Art.17)", "Right to Restriction (Art.18)", "Right to Data Portability (Art.20)", "Right to Object (Art.21)", "Rights re: Automated Decisions (Art.22)"],
                    "whole": "Data Subject Rights"
                },
                "reasoning": "These 8 rights form the core of individual empowerment under GDPR. Must respond within 1 month."
            },
            {
                "move": "woc",
                "pattern": "R",
                "elements": {
                    "cause": "Data Subject Request",
                    "effects": [
                        {"effect": "Controller must verify identity", "level": 1},
                        {"effect": "Response within 1 month (extendable by 2 months)", "level": 1},
                        {"effect": "Must be free of charge (usually)", "level": 1},
                        {"effect": "If refused, must explain why with appeal rights", "level": 2}
                    ]
                },
                "reasoning": "Understanding the response workflow is critical for compliance."
            }
        ]
    },
    {
        "id": "data-breach",
        "name": "Data Breach Notification",
        "description": "Requirements under Articles 33-34 for breach notification",
        "domain": "CIPP/E",
        "topic": "Security & Breaches",
        "analyses": [
            {
                "move": "is-is-not",
                "pattern": "D",
                "elements": {
                    "identity": "Breach of security leading to accidental or unlawful destruction, loss, alteration, unauthorized disclosure of, or access to personal data",
                    "other": "Security incidents not involving personal data, near-misses that were prevented, breaches of non-personal corporate data",
                    "boundary": "Must involve personal data AND a security breach (confidentiality, integrity, OR availability)"
                },
                "reasoning": "A breach can be CIA - Confidentiality (disclosure), Integrity (alteration), or Availability (loss/destruction)."
            },
            {
                "move": "woc",
                "pattern": "R",
                "elements": {
                    "cause": "Personal Data Breach",
                    "effects": [
                        {"effect": "Notify supervisory authority within 72 hours (if risk)", "level": 1},
                        {"effect": "Notify affected individuals without undue delay (if high risk)", "level": 1},
                        {"effect": "Document in internal breach register (ALL breaches)", "level": 1},
                        {"effect": "Potential investigation by DPA", "level": 2},
                        {"effect": "Potential fines up to €10M or 2%", "level": 2}
                    ]
                },
                "reasoning": "The 72-hour clock starts when you become AWARE of the breach, not when it occurred."
            },
            {
                "move": "waoc",
                "pattern": "R",
                "elements": {
                    "effect": "Data Breach",
                    "causes": [
                        {"cause": "Phishing/social engineering attacks", "level": 1},
                        {"cause": "Misconfigured systems/cloud storage", "level": 1},
                        {"cause": "Lost/stolen devices", "level": 1},
                        {"cause": "Insider threats (malicious or negligent)", "level": 1},
                        {"cause": "Inadequate access controls", "level": 2},
                        {"cause": "Unpatched vulnerabilities", "level": 2},
                        {"cause": "Third-party/supply chain failures", "level": 2}
                    ]
                },
                "reasoning": "Root cause analysis helps prevent future breaches - technical AND organizational measures needed."
            }
        ]
    },
    {
        "id": "international-transfers",
        "name": "International Data Transfers",
        "description": "Rules for transferring personal data outside EU/EEA (Chapter 5)",
        "domain": "CIPP/E",
        "topic": "International Transfers",
        "analyses": [
            {
                "move": "is-is-not",
                "pattern": "D",
                "elements": {
                    "identity": "Adequacy decisions (Art.45), Standard Contractual Clauses (Art.46), Binding Corporate Rules (Art.47), Derogations for specific situations (Art.49)",
                    "other": "Transfers to non-adequate countries without safeguards, reliance on invalidated mechanisms (Privacy Shield post-Schrems II), informal arrangements",
                    "boundary": "Is there 'essentially equivalent' protection in the destination country?"
                },
                "reasoning": "Post-Schrems II, transfer impact assessments (TIAs) are required for SCCs to verify destination country laws."
            },
            {
                "move": "zoom-in",
                "pattern": "S",
                "elements": {
                    "parts": ["Andorra", "Argentina", "Canada (commercial)", "Faroe Islands", "Guernsey", "Israel", "Isle of Man", "Japan", "Jersey", "New Zealand", "South Korea", "Switzerland", "UK", "Uruguay", "EU-US Data Privacy Framework (2023)"],
                    "whole": "Adequacy Decisions"
                },
                "reasoning": "Adequacy allows free data flow without additional safeguards - memorize this list for the exam."
            }
        ]
    },
    {
        "id": "dpo",
        "name": "Data Protection Officer (DPO)",
        "description": "Mandatory role under Article 37-39 for certain organizations",
        "domain": "CIPP/E",
        "topic": "Governance",
        "analyses": [
            {
                "move": "is-is-not",
                "pattern": "D",
                "elements": {
                    "identity": "Required when: public authority, core activities involve large-scale systematic monitoring, core activities involve large-scale special category data processing",
                    "other": "NOT required for: small businesses without systematic monitoring, one-off processing, non-core processing activities",
                    "boundary": "Is it a public authority OR do core activities involve large-scale systematic monitoring/special categories?"
                },
                "reasoning": "DPO is mandatory only in specific situations - many organizations appoint voluntarily."
            },
            {
                "move": "zoom-in",
                "pattern": "S",
                "elements": {
                    "parts": ["Inform and advise controller/processor", "Monitor GDPR compliance", "Advise on DPIAs", "Cooperate with supervisory authority", "Act as contact point for DPA and data subjects"],
                    "whole": "DPO Tasks"
                },
                "reasoning": "DPO must be independent, report to highest management, have no conflict of interest."
            }
        ]
    },
    {
        "id": "dpia",
        "name": "Data Protection Impact Assessment (DPIA)",
        "description": "Risk assessment required under Article 35 for high-risk processing",
        "domain": "CIPP/E",
        "topic": "Governance",
        "analyses": [
            {
                "move": "is-is-not",
                "pattern": "D",
                "elements": {
                    "identity": "Required when processing likely to result in HIGH RISK: systematic evaluation/profiling, large-scale special categories, systematic public area monitoring",
                    "other": "NOT required for: low-risk processing, processing already covered by existing DPIA, processing on DPA whitelist",
                    "boundary": "Does the processing meet TWO OR MORE criteria from EDPB guidelines?"
                },
                "reasoning": "DPIA is proactive risk management - must be done BEFORE processing begins."
            },
            {
                "move": "zoom-in",
                "pattern": "S",
                "elements": {
                    "parts": ["Description of processing operations", "Assessment of necessity and proportionality", "Assessment of risks to rights and freedoms", "Measures to address risks"],
                    "whole": "DPIA Contents"
                },
                "reasoning": "If high residual risk remains after mitigation, must consult supervisory authority."
            },
            {
                "move": "woc",
                "pattern": "R",
                "elements": {
                    "cause": "High-risk processing identified",
                    "effects": [
                        {"effect": "DPIA must be conducted before processing", "level": 1},
                        {"effect": "DPO must be consulted", "level": 1},
                        {"effect": "If high residual risk, consult supervisory authority", "level": 2},
                        {"effect": "DPA may prohibit processing or impose conditions", "level": 2}
                    ]
                },
                "reasoning": "DPIA is a checkpoint that can result in processing being modified or stopped."
            }
        ]
    },
    {
        "id": "fines",
        "name": "GDPR Fines Structure",
        "description": "Two-tier administrative fine system under Article 83",
        "domain": "CIPP/E",
        "topic": "Enforcement",
        "analyses": [
            {
                "move": "is-is-not",
                "pattern": "D",
                "elements": {
                    "identity": "Tier 1 (Lower): Up to €10M or 2% global turnover - controller/processor obligations, certification bodies. Tier 2 (Higher): Up to €20M or 4% global turnover - principles, data subject rights, international transfers, non-compliance with orders",
                    "other": "Criminal penalties (handled by member states separately), non-monetary corrective measures (warnings, orders, bans)",
                    "boundary": "Severity of violation - principles/rights violations are higher tier than operational failures"
                },
                "reasoning": "Know which violations fall into which tier - this is frequently tested."
            },
            {
                "move": "zoom-in",
                "pattern": "S",
                "elements": {
                    "parts": ["Nature, gravity, duration", "Intentional vs negligent", "Mitigation actions taken", "Previous violations", "Cooperation with DPA", "Categories of data affected", "How DPA learned of violation", "Certifications in place"],
                    "whole": "Fine Calculation Factors"
                },
                "reasoning": "Fines must be effective, proportionate, and dissuasive - these factors determine the amount."
            }
        ]
    }
]


# Additional seed data for other domains
CIPP_US_SEED_DATA = [
    {
        "id": "ccpa",
        "name": "CCPA/CPRA",
        "description": "California Consumer Privacy Act / California Privacy Rights Act",
        "domain": "CIPP/US",
        "topic": "State Privacy Laws",
        "analyses": [
            {
                "move": "is-is-not",
                "pattern": "D",
                "elements": {
                    "identity": "California state law, applies to businesses meeting thresholds (revenue, data volume, data sales), grants consumer rights (know, delete, opt-out, correct, limit)",
                    "other": "NOT federal law, NOT applicable to small businesses below thresholds, NOT applicable to employee data (until 2023), NOT as comprehensive as GDPR",
                    "boundary": "Does the business meet California's threshold requirements and process California residents' data?"
                },
                "reasoning": "CCPA/CPRA is the most comprehensive US state privacy law, often compared to GDPR."
            },
            {
                "move": "zoom-in",
                "pattern": "S",
                "elements": {
                    "parts": ["Right to Know", "Right to Delete", "Right to Opt-Out of Sale", "Right to Correct", "Right to Limit Sensitive Data Use", "Non-Discrimination Right"],
                    "whole": "CCPA Consumer Rights"
                },
                "reasoning": "Understanding the specific rights granted is essential for compliance."
            }
        ]
    },
    {
        "id": "hipaa",
        "name": "HIPAA",
        "description": "Health Insurance Portability and Accountability Act",
        "domain": "CIPP/US",
        "topic": "Sector-Specific Laws",
        "analyses": [
            {
                "move": "is-is-not",
                "pattern": "D",
                "elements": {
                    "identity": "Federal law protecting health information (PHI), applies to covered entities (healthcare providers, health plans, clearinghouses) and business associates",
                    "other": "NOT applicable to employers (as employers), NOT applicable to life insurers, NOT applicable to most schools, NOT applicable to law enforcement",
                    "boundary": "Is the entity a covered entity or business associate handling PHI?"
                },
                "reasoning": "HIPAA's scope is narrower than many assume - it only applies to specific healthcare entities."
            }
        ]
    },
    {
        "id": "ftc-act",
        "name": "FTC Act Section 5",
        "description": "Federal Trade Commission Act - unfair/deceptive practices authority",
        "domain": "CIPP/US",
        "topic": "Federal Framework",
        "analyses": [
            {
                "move": "zoom-out",
                "pattern": "S",
                "elements": {
                    "whole": "US Privacy Framework (sectoral approach)",
                    "context": "FTC Act provides baseline privacy enforcement through unfair/deceptive practices prohibition, complemented by sector-specific laws"
                },
                "reasoning": "The FTC is the de facto federal privacy regulator in the absence of comprehensive federal privacy law."
            }
        ]
    }
]

CIPM_SEED_DATA = [
    {
        "id": "privacy-program",
        "name": "Privacy Program",
        "description": "Organizational structure for managing privacy compliance",
        "domain": "CIPM",
        "topic": "Program Development",
        "analyses": [
            {
                "move": "zoom-in",
                "pattern": "S",
                "elements": {
                    "parts": ["Governance Structure", "Policies & Procedures", "Training & Awareness", "Data Inventory", "Risk Assessment", "Incident Response", "Vendor Management", "Monitoring & Audit"],
                    "whole": "Privacy Program"
                },
                "reasoning": "A mature privacy program has these key components working together."
            },
            {
                "move": "p-circle",
                "pattern": "P",
                "elements": {
                    "perspectives": [
                        {"point": "Executive Leadership", "view": "Risk management, liability reduction, competitive advantage"},
                        {"point": "Legal/Compliance", "view": "Regulatory compliance, contractual obligations"},
                        {"point": "IT/Security", "view": "Technical controls, data protection, access management"},
                        {"point": "Business Units", "view": "Operational enablement, customer trust"}
                    ]
                },
                "reasoning": "Different stakeholders view the privacy program through different lenses."
            }
        ]
    },
    {
        "id": "privacy-metrics",
        "name": "Privacy Metrics",
        "description": "Key performance indicators for privacy programs",
        "domain": "CIPM",
        "topic": "Program Measurement",
        "analyses": [
            {
                "move": "zoom-in",
                "pattern": "S",
                "elements": {
                    "parts": ["DSR Response Times", "Training Completion Rates", "Incident Count/Severity", "Audit Findings", "Vendor Assessment Scores", "Privacy by Design Adoption", "Data Inventory Coverage"],
                    "whole": "Privacy Metrics Framework"
                },
                "reasoning": "What gets measured gets managed - these metrics demonstrate program effectiveness."
            }
        ]
    }
]


def _get_concepts_db():
    """Get the shared concepts db."""
    try:
        from app.api.concepts import concepts_db
        return concepts_db
    except ImportError:
        return {}


def _get_analyses_db():
    """Get the shared analyses db."""
    try:
        from app.services.export_service import analyses_db
        return analyses_db
    except ImportError:
        return {}


def _seed_data(data_list: list, concepts_db: dict, analyses_db: dict) -> tuple[list, int]:
    """Helper to seed a list of concepts with their analyses."""
    seeded_concepts = []
    seeded_analyses = 0

    for item in data_list:
        concept_id = item["id"]

        # Add concept with domain metadata
        concepts_db[concept_id] = {
            "id": concept_id,
            "name": item["name"],
            "description": item["description"],
            "domain": item.get("domain"),
            "topic": item.get("topic"),
            "chapter": item.get("chapter"),
            "source_document": item.get("source_document"),
            "knowledge_structure": item.get("knowledge_structure"),
        }
        seeded_concepts.append(item["name"])

        # Add analyses
        analyses_db[concept_id] = item["analyses"]
        seeded_analyses += len(item["analyses"])

    return seeded_concepts, seeded_analyses


@router.post("/cipp-e")
async def seed_cipp_e_data():
    """Seed the database with CIPP/E sample concepts and DSRP analyses."""
    concepts_db = _get_concepts_db()
    analyses_db = _get_analyses_db()

    seeded_concepts, seeded_analyses = _seed_data(CIPP_E_SEED_DATA, concepts_db, analyses_db)

    return {
        "status": "success",
        "domain": "CIPP/E",
        "concepts_seeded": len(seeded_concepts),
        "analyses_seeded": seeded_analyses,
        "concepts": seeded_concepts,
        "message": "CIPP/E sample data loaded!"
    }


@router.post("/cipp-us")
async def seed_cipp_us_data():
    """Seed the database with CIPP/US sample concepts and DSRP analyses."""
    concepts_db = _get_concepts_db()
    analyses_db = _get_analyses_db()

    seeded_concepts, seeded_analyses = _seed_data(CIPP_US_SEED_DATA, concepts_db, analyses_db)

    return {
        "status": "success",
        "domain": "CIPP/US",
        "concepts_seeded": len(seeded_concepts),
        "analyses_seeded": seeded_analyses,
        "concepts": seeded_concepts,
        "message": "CIPP/US sample data loaded!"
    }


@router.post("/cipm")
async def seed_cipm_data():
    """Seed the database with CIPM sample concepts and DSRP analyses."""
    concepts_db = _get_concepts_db()
    analyses_db = _get_analyses_db()

    seeded_concepts, seeded_analyses = _seed_data(CIPM_SEED_DATA, concepts_db, analyses_db)

    return {
        "status": "success",
        "domain": "CIPM",
        "concepts_seeded": len(seeded_concepts),
        "analyses_seeded": seeded_analyses,
        "concepts": seeded_concepts,
        "message": "CIPM sample data loaded!"
    }


@router.post("/all")
async def seed_all_data():
    """Seed the database with ALL domain sample data."""
    concepts_db = _get_concepts_db()
    analyses_db = _get_analyses_db()

    total_concepts = []
    total_analyses = 0
    domains_seeded = []

    # Seed all domains
    for domain_name, data in [
        ("CIPP/E", CIPP_E_SEED_DATA),
        ("CIPP/US", CIPP_US_SEED_DATA),
        ("CIPM", CIPM_SEED_DATA),
    ]:
        concepts, analyses = _seed_data(data, concepts_db, analyses_db)
        total_concepts.extend(concepts)
        total_analyses += analyses
        domains_seeded.append({"domain": domain_name, "concepts": len(concepts), "analyses": analyses})

    return {
        "status": "success",
        "total_concepts": len(total_concepts),
        "total_analyses": total_analyses,
        "domains": domains_seeded,
        "message": "All domain sample data loaded! You can now use the Quiz feature with domain filtering."
    }


@router.get("/status")
async def get_seed_status():
    """Check how many concepts and analyses are in the database."""
    concepts_db = _get_concepts_db()
    analyses_db = _get_analyses_db()

    total_analyses = sum(len(a) for a in analyses_db.values())

    return {
        "concepts_count": len(concepts_db),
        "analyses_count": total_analyses,
        "concepts": list(concepts_db.keys()),
    }


@router.delete("/clear")
async def clear_seed_data():
    """Clear all seeded data from in-memory stores."""
    concepts_db = _get_concepts_db()
    analyses_db = _get_analyses_db()

    concepts_db.clear()
    analyses_db.clear()

    return {"status": "cleared", "message": "All in-memory data cleared"}
