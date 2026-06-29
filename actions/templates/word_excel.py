"""
actions/templates/word_excel.py
================================
Word document content and Excel spreadsheet templates used by office.py.
"""

import random
from datetime import datetime


def get_word_content() -> str:
    """Return a random Word document body."""
    today = datetime.now().strftime("%d %B %Y")
    contents = [
        f"Weekly Status Update — {today}\n\n"
        "Project Alpha is progressing on schedule. All Q2 milestones have been completed. "
        "The team will present results in the Friday meeting.\n\n"
        "Action items:\n"
        "- Review the deployment checklist\n"
        "- Update the risk register\n"
        "- Confirm stakeholder sign-off",

        f"Meeting Notes — Infrastructure Review\nDate: {today}\n\n"
        "Attendees: Development team, DevOps, Management\n\n"
        "Decisions:\n"
        "1. Upgrade server OS to Ubuntu 22.04 LTS by end of month\n"
        "2. Enable automatic backups on all production databases\n"
        "3. Schedule penetration test for Q3\n\n"
        "Next meeting: same time next week",

        f"Incident Report\nDate: {today}\nSeverity: Medium\n\n"
        "Summary: Network switch firmware update caused a temporary port reset.\n"
        "Duration: approximately 45 minutes\n"
        "Root cause: unplanned firmware push during business hours\n"
        "Resolution: switch rebooted, all services restored\n"
        "Prevention: all maintenance windows to be scheduled outside business hours",

        f"Project Proposal — Q3 Infrastructure Upgrade\nDate: {today}\n\n"
        "Objective: Modernise the on-premise server infrastructure to improve reliability and performance.\n\n"
        "Scope:\n"
        "- Replace three ageing servers with new hardware\n"
        "- Migrate services to containerised deployments\n"
        "- Implement centralised log management\n\n"
        "Estimated timeline: 6 weeks\n"
        "Estimated budget: to be confirmed pending vendor quotes",

        f"Budget Report — Q2 Summary\nDate: {today}\n\n"
        "Total allocated: $48,000\n"
        "Total spent:     $41,350\n"
        "Remaining:       $6,650\n\n"
        "Key expenditures:\n"
        "- Software licences:   $12,400\n"
        "- Hardware purchases:  $18,900\n"
        "- Training:             $5,200\n"
        "- Miscellaneous:        $4,850\n\n"
        "Note: underspend to be carried forward to Q3",

        f"Risk Assessment — Production Environment\nDate: {today}\n\n"
        "Risk 1: Single point of failure on primary database server\n"
        "Likelihood: Medium | Impact: High | Mitigation: deploy standby replica\n\n"
        "Risk 2: Outdated SSL certificates on web-facing services\n"
        "Likelihood: High | Impact: Medium | Mitigation: automate renewal via certbot\n\n"
        "Risk 3: Insufficient backup retention for compliance requirements\n"
        "Likelihood: Low | Impact: High | Mitigation: extend retention to 90 days",

        f"Change Request — CR-{random.randint(1000,9999)}\nDate: {today}\n\n"
        "Title: Firewall rule update for third-party integration\n"
        "Requested by: IT Security\n"
        "Priority: Medium\n\n"
        "Description: Add inbound rule to allow traffic from vendor IP range on port 443.\n\n"
        "Risk assessment: Low — traffic is TLS-encrypted and source IPs are whitelisted\n"
        "Rollback plan: revert firewall rule via management console\n"
        "Scheduled window: Saturday 02:00–04:00",

        f"Technical Specification — API Gateway\nDate: {today}\n\n"
        "Version: 1.2\nAuthor: Infrastructure Team\n\n"
        "Overview: This document describes the configuration and behaviour of the internal API gateway.\n\n"
        "Authentication: Bearer token (JWT, RS256)\n"
        "Rate limiting: 1000 requests/minute per client\n"
        "Timeout: 30 seconds\n"
        "Retry policy: 3 attempts with exponential backoff\n\n"
        "Endpoints documented in Appendix A",

        f"Security Audit Findings\nDate: {today}\nAudit scope: internal network\n\n"
        "Critical findings: 0\n"
        "High findings:     2\n"
        "Medium findings:   5\n"
        "Low findings:      9\n\n"
        "High finding 1: Default credentials on management console — remediated\n"
        "High finding 2: Unpatched vulnerability in web server — patch scheduled\n\n"
        "Full report distributed to security team",

        f"Deployment Checklist — Release v{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,9)}\nDate: {today}\n\n"
        "Pre-deployment:\n"
        "[x] Code review approved\n"
        "[x] All tests passing\n"
        "[x] Staging environment validated\n"
        "[x] Database migration scripts reviewed\n"
        "[ ] Stakeholder sign-off received\n\n"
        "Deployment steps:\n"
        "1. Take database snapshot\n"
        "2. Deploy application containers\n"
        "3. Run smoke tests\n"
        "4. Monitor error rates for 30 minutes",

        f"Quarterly Business Review — Q2\nDate: {today}\n\n"
        "Highlights:\n"
        "- System uptime: 99.7% (target: 99.5%)\n"
        "- Support tickets resolved: 214 of 231 (92.6%)\n"
        "- Mean time to resolve: 4.2 hours\n"
        "- Zero critical incidents this quarter\n\n"
        "Areas for improvement:\n"
        "- Response time on P3 tickets exceeded SLA on 12 occasions\n"
        "- Documentation coverage below target at 68%\n\n"
        "Q3 priorities: automation, documentation, capacity planning",

        f"Vendor Evaluation Report\nDate: {today}\n\n"
        "Vendor: TechCorp Solutions\nProduct: Endpoint Detection & Response\n\n"
        "Evaluation criteria:\n"
        "Detection rate:      9/10\n"
        "False positive rate: 7/10\n"
        "Management console:  8/10\n"
        "Pricing:             6/10\n"
        "Support quality:     9/10\n\n"
        "Overall score: 39/50\n"
        "Recommendation: Proceed to procurement with negotiation on pricing",

        f"IT Policy Update — Acceptable Use Policy\nDate: {today}\nVersion: 3.1\n\n"
        "Summary of changes:\n"
        "- Section 4.2: Cloud storage restricted to approved platforms only\n"
        "- Section 6.1: Remote access now requires MFA for all staff\n"
        "- Section 8.3: Personal devices prohibited from connecting to internal network\n\n"
        "Effective date: first of next month\n"
        "All staff must acknowledge receipt via the HR portal",

        f"Employee Training Plan — H2 {datetime.now().year}\nDate: {today}\n\n"
        "Mandatory training:\n"
        "- Security awareness (all staff)       — July\n"
        "- GDPR refresher (all staff)           — August\n"
        "- Incident response (IT team)          — September\n\n"
        "Optional training:\n"
        "- Cloud architecture fundamentals      — October\n"
        "- Python scripting for administrators  — November\n\n"
        "Completion to be tracked in the HR learning management system",

        f"End of Day Report — {today}\n\n"
        "Tasks completed:\n"
        "- Reviewed and responded to 18 support tickets\n"
        "- Deployed hotfix to production environment\n"
        "- Attended architecture review meeting\n"
        "- Updated infrastructure documentation\n\n"
        "Pending:\n"
        "- Awaiting vendor response on licence renewal\n"
        "- Database migration scheduled for tomorrow\n\n"
        "Notes: no critical issues outstanding",
    ]
    return random.choice(contents)


def get_excel_template() -> dict:
    """Return a random Excel spreadsheet template."""
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%B %Y")
    templates = [
        {
            "sheet": "Project Tracker",
            "headers": ["Project", "Owner", "Status", "Due Date", "Progress %"],
            "rows": [
                ["Alpha Migration",    "J. Smith",  "In Progress", "2026-07-15",  65],
                ["Beta Deployment",    "A. Jones",  "On Hold",     "2026-08-01",  20],
                ["Security Hardening", "R. Patel",  "Complete",    "2026-06-30", 100],
                ["DR Testing",         "M. Brown",  "Not Started", "2026-09-01",   0],
                ["Cloud Onboarding",   "L. Chen",   "In Progress", "2026-07-30",  40],
            ]
        },
        {
            "sheet": "Monthly Budget",
            "headers": ["Category", "Allocated", "Spent", "Remaining", "Variance %"],
            "rows": [
                ["Software Licences", 12000, 11450,  550,  4.6],
                ["Hardware",          18000, 19200, -1200, -6.7],
                ["Training",           5000,  4200,  800, 16.0],
                ["Cloud Services",     8000,  7850,  150,  1.9],
                ["Miscellaneous",      2000,  1340,  660, 33.0],
            ]
        },
        {
            "sheet": "IT Asset Inventory",
            "headers": ["Asset ID", "Type", "Model", "Assigned To", "Status", "Last Updated"],
            "rows": [
                ["AST-001", "Laptop",  "Dell XPS 15",        "J. Smith",  "Active", today],
                ["AST-002", "Desktop", "HP EliteDesk 800",   "A. Jones",  "Active", today],
                ["AST-003", "Server",  "Dell PowerEdge R740", "IT Dept",  "Active", today],
                ["AST-004", "Laptop",  "Lenovo ThinkPad X1", "M. Brown",  "Repair", today],
                ["AST-005", "Switch",  "Cisco Catalyst 2960", "IT Dept",  "Active", today],
            ]
        },
        {
            "sheet": "Incident Log",
            "headers": ["Ticket ID", "Date", "Severity", "Description", "Status", "Resolver"],
            "rows": [
                ["INC-1041", today, "High",   "VPN service unavailable",    "Resolved",    "R. Patel"],
                ["INC-1042", today, "Medium", "Email sync delay reported",   "Resolved",    "A. Jones"],
                ["INC-1043", today, "Low",    "Printer offline — 3rd floor", "Closed",      "J. Smith"],
                ["INC-1044", today, "High",   "Database connection timeout",  "In Progress", "M. Brown"],
                ["INC-1045", today, "Low",    "Password reset request",       "Closed",      "L. Chen"],
            ]
        },
        {
            "sheet": "Attendance",
            "headers": ["Employee", "Department", "Days Present", "Days Absent", "Leave Taken", "Month"],
            "rows": [
                ["J. Smith",  "IT",         21, 0, 1, month],
                ["A. Jones",  "HR",         19, 2, 0, month],
                ["R. Patel",  "Finance",    20, 1, 2, month],
                ["M. Brown",  "IT",         22, 0, 0, month],
                ["L. Chen",   "Operations", 18, 3, 1, month],
            ]
        },
        {
            "sheet": "Network Performance",
            "headers": ["Date", "Uptime %", "Avg Latency ms", "Packet Loss %", "Bandwidth Mbps"],
            "rows": [
                [today, 99.9, 12, 0.01, 842],
                [today, 99.7, 14, 0.02, 798],
                [today, 100,  11, 0.00, 910],
                [today, 98.5, 23, 0.15, 650],
                [today, 99.8, 13, 0.01, 880],
            ]
        },
        {
            "sheet": "Software Licences",
            "headers": ["Software", "Vendor", "Licences", "In Use", "Expiry", "Cost/yr"],
            "rows": [
                ["Windows 11 Pro",  "Microsoft", 50, 47, "2027-01-15", 4500],
                ["Office 365",      "Microsoft", 50, 49, "2026-12-31", 9800],
                ["Adobe Acrobat",   "Adobe",     10,  8, "2026-09-30", 2400],
                ["Antivirus Suite", "Sophos",    50, 50, "2026-11-01", 3200],
                ["Backup Software", "Veeam",      5,  5, "2027-03-15", 1800],
            ]
        },
        {
            "sheet": "Patch Status",
            "headers": ["System", "OS", "Last Patched", "Patch Level", "Reboot Required", "Owner"],
            "rows": [
                ["SRV-PROD-01", "Windows Server 2022", today, "Current",   "No",  "IT Ops"],
                ["SRV-PROD-02", "Ubuntu 22.04",        today, "Current",   "No",  "IT Ops"],
                ["SRV-DB-01",   "Windows Server 2019", today, "1 pending", "Yes", "DBA Team"],
                ["WKS-IT-01",   "Windows 11",          today, "Current",   "No",  "IT Ops"],
                ["SRV-BACKUP",  "Ubuntu 20.04",        today, "3 pending", "Yes", "IT Ops"],
            ]
        },
        {
            "sheet": "Department Expenses",
            "headers": ["Department", "Q1 Budget", "Q1 Actual", "Q2 Budget", "Q2 Actual", "YTD Variance"],
            "rows": [
                ["IT",         45000, 43200, 45000, 41800,  5000],
                ["HR",         12000, 11500, 12000, 12800,  -300],
                ["Finance",    18000, 17200, 18000, 16900,  1900],
                ["Operations", 30000, 31200, 30000, 29400,  -600],
                ["Management", 25000, 24100, 25000, 25600,  -700],
            ]
        },
        {
            "sheet": "Task Tracker",
            "headers": ["Task", "Assignee", "Priority", "Due Date", "Status", "Notes"],
            "rows": [
                ["Update firewall rules",    "R. Patel", "High",   "2026-06-10", "In Progress", "Awaiting change approval"],
                ["Renew SSL certificates",   "A. Jones", "High",   "2026-06-15", "Not Started", "Auto-renewal configured"],
                ["Quarterly backup test",    "M. Brown", "Medium", "2026-06-30", "In Progress", "50% complete"],
                ["Document DR procedures",   "J. Smith", "Low",    "2026-07-01", "Not Started", "Template shared"],
                ["Audit user access rights", "L. Chen",  "Medium", "2026-06-20", "Complete",    "Report submitted"],
            ]
        },
        {
            "sheet": "Server Uptime",
            "headers": ["Server", "Role", "Uptime %", "Last Reboot", "Incidents", "SLA Target %"],
            "rows": [
                ["SRV-PROD-01", "Web Server",    99.95, "2026-05-01", 0, 99.9],
                ["SRV-PROD-02", "App Server",    99.80, "2026-05-15", 1, 99.9],
                ["SRV-DB-01",   "Database",      99.99, "2026-04-20", 0, 99.9],
                ["SRV-MAIL",    "Mail Server",   99.70, "2026-05-28", 2, 99.5],
                ["SRV-BACKUP",  "Backup Server", 100.0, "2026-03-10", 0, 99.0],
            ]
        },
        {
            "sheet": "Change Log",
            "headers": ["Change ID", "Date", "Type", "Description", "Implemented By", "Status"],
            "rows": [
                ["CHG-501", today, "Standard",  "Updated antivirus definitions",    "R. Patel", "Complete"],
                ["CHG-502", today, "Normal",    "New firewall rule for vendor VPN",  "A. Jones", "Approved"],
                ["CHG-503", today, "Emergency", "Rolled back web server update",     "J. Smith", "Complete"],
                ["CHG-504", today, "Standard",  "User account provisioning x5",      "L. Chen",  "Complete"],
                ["CHG-505", today, "Normal",    "Database index optimisation",        "M. Brown", "Pending"],
            ]
        },
        {
            "sheet": "Vendor Contacts",
            "headers": ["Vendor", "Product", "Account Manager", "Support Email", "Contract Expiry", "Annual Value"],
            "rows": [
                ["Microsoft", "M365 / Windows",    "T. Williams", "support@microsoft.com", "2026-12-31", 14300],
                ["Cisco",     "Network Hardware",   "K. Nguyen",   "support@cisco.com",    "2027-06-30", 22000],
                ["Veeam",     "Backup Software",    "P. Davis",    "support@veeam.com",    "2027-03-15",  1800],
                ["Sophos",    "Endpoint Security",  "S. Lee",      "support@sophos.com",   "2026-11-01",  3200],
                ["Dell",      "Server Hardware",    "M. Harris",   "support@dell.com",     "2028-01-01",  8500],
            ]
        },
        {
            "sheet": "Training Completion",
            "headers": ["Employee", "Security Awareness", "GDPR", "IT Policy", "Fire Safety", "Completion %"],
            "rows": [
                ["J. Smith",  "Complete", "Complete", "Complete", "Complete", 100],
                ["A. Jones",  "Complete", "Complete", "Pending",  "Complete",  75],
                ["R. Patel",  "Complete", "Pending",  "Complete", "Complete",  75],
                ["M. Brown",  "Pending",  "Complete", "Complete", "Complete",  75],
                ["L. Chen",   "Complete", "Complete", "Complete", "Pending",   75],
            ]
        },
        {
            "sheet": "Sales Pipeline",
            "headers": ["Opportunity", "Client", "Value", "Stage", "Close Date", "Owner"],
            "rows": [
                ["Network Upgrade",  "Acme Corp",   85000, "Proposal",    "2026-07-31", "J. Smith"],
                ["Security Audit",   "GlobalTech",  32000, "Negotiation", "2026-06-30", "A. Jones"],
                ["Cloud Migration",  "StartupXYZ",  54000, "Discovery",   "2026-09-15", "R. Patel"],
                ["DR Solution",      "MegaBank",   120000, "Proposal",    "2026-08-01", "M. Brown"],
                ["Managed Services", "RetailCo",    48000, "Closed Won",  "2026-06-01", "L. Chen"],
            ]
        },
    ]
    return random.choice(templates)