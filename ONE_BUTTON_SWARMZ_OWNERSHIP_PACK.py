#!/usr/bin/env python3
# ONE_BUTTON_SWARMZ_OWNERSHIP_PACK.py
#
# One-button generator: creates ALL folders + files for the SWARMZ AU ownership/IP/options starter pack.
# Additive only: will NOT overwrite existing files.
#
# Run (CMD):        py ONE_BUTTON_SWARMZ_OWNERSHIP_PACK.py
# Run (PowerShell): python .\ONE_BUTTON_SWARMZ_OWNERSHIP_PACK.py

from __future__ import annotations

import re
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.cwd()

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def prompt_default(prompt: str, default: str) -> str:
    try:
        s = input(f"{prompt} [{default}]: ").strip()
    except EOFError:
        s = ""
    return s if s else default

def sanitize_single_line(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"[\r\n\t]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def atomic_write_new(path: Path, content: str) -> bool:
    """
    Write file only if it doesn't exist. Atomic via temp replace.
    Returns True if created, False if skipped.
    """
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8", newline="\n")
    tmp.replace(path)
    return True

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except Exception:
        return str(p)

def main() -> int:
    print("SWARMZ — ONE BUTTON OWNERSHIP PACK (AU Pty Ltd) :: GENERATOR")
    print(f"REPO ROOT: {ROOT}")
    print("MODE: additive only (no overwrites)\n")

    # Minimal inputs (press Enter to accept defaults)
    company_legal_name = sanitize_single_line(prompt_default("Company legal name", "SWARMZ PTY LTD"))
    acn = sanitize_single_line(prompt_default("ACN (if known, else TBA)", "TBA"))
    abn = sanitize_single_line(prompt_default("ABN (if known, else TBA)", "TBA"))
    jurisdiction_state = sanitize_single_line(prompt_default("State/Territory (e.g., VIC/NSW/QLD)", "VIC"))
    registered_address = sanitize_single_line(prompt_default("Registered office address (short)", "TBA"))
    principal_place = sanitize_single_line(prompt_default("Principal place of business (short)", "TBA"))
    director_name = sanitize_single_line(prompt_default("Director full name", "TBA"))
    secretary_name = sanitize_single_line(prompt_default("Secretary full name (or same as director)", director_name if director_name else "TBA"))
    founder_name = sanitize_single_line(prompt_default("Founder full name (owner)", director_name if director_name else "TBA"))
    founder_email = sanitize_single_line(prompt_default("Founder email", "TBA"))
    project_name = sanitize_single_line(prompt_default("Project / repo name", "SWARMZ"))

    stamp = now_utc_iso()

    # Folder plan (ALL created if missing)
    docs_dir = ROOT / "docs" / "ownership"
    legal_templates = ROOT / "legal" / "templates"
    legal_signed = ROOT / "legal" / "signed"
    legal_registers = ROOT / "legal" / "registers"

    ensure_dir(docs_dir)
    ensure_dir(legal_templates)
    ensure_dir(legal_signed)
    ensure_dir(legal_registers)

    created: list[str] = []

    def add(path: Path, content: str) -> None:
        if atomic_write_new(path, content):
            created.append(rel(path))

    # -------- docs/ownership --------
    add(docs_dir / "README_OWNERSHIP_STACK.md", f"""# {project_name} — Ownership Stack v1 (AU)

Generated: {stamp}

This pack exists to make {project_name} a **sellable asset**:
- clean cap table intent
- clean IP chain of title (company owns everything)
- contributor/contractor IP assignment templates
- options plan stub (for later)
- registers/minutes stubs
- data room checklist

## Non-negotiables (control rules)
1) Founder-controlled cap table: founder owns 100% initially.
2) Company owns IP: founder assigns all project IP to company.
3) No equity-for-favours: contractors paid cash; employees get options later (vesting + cliff).
4) Additive paperwork only: minimal surface area.

## Structure
- `legal/templates/`  templates to sign
- `legal/signed/`     signed PDFs live here (you can gitignore it if you want)
- `legal/registers/`  member register + cap table CSV
- `docs/ownership/`   intent + metrics + checklist

## NOTE
These templates are not legal advice. Use them as a starting pack for AU accountant/lawyer review.
""")

    add(docs_dir / "OUTCOME_METRICS.md", """# Outcome Metrics (Ownership → Net Worth Mechanism)

## Target (12 months)
- Paying users: yes
- MRR: $1,000+
- Gross margin: 80%+
- Founder ownership: 80–95% (unless deliberate dilution for high leverage)
- Clean IP chain: 100% assigned to the company
- Minimal financial ledger: income/expenses/subscriptions tracked
- Export/import + backups exist

## Kill conditions (stop wasting equity-time)
- No paying users after 90 days of shipping
- Maintenance burden exceeds operator capacity
- Legal/tax exposure cannot be resolved under current structure
""")

    add(docs_dir / "CAP_TABLE_INTENT.md", f"""# Cap Table Intent (Founder-Controlled)

Company: {company_legal_name}
ACN: {acn}
ABN: {abn}

Generated: {stamp}

## Starting position (recommended)
- Founder holds 100% of ordinary shares initially.
- No early share issues to advisors/contractors.

## Future (only when needed)
- Create an Option Pool (5–15%) for true employees/contributors.
- Options vest over time (typical: 4 years; 1-year cliff).
- Grants happen after revenue traction.

## Rules
- No equity-for-favours.
- No share/option action without board minutes + register updates + cap table update.
""")

    add(docs_dir / "DATA_ROOM_CHECKLIST.md", f"""# Data Room Checklist (Sellable Asset Readiness)

Company: {company_legal_name}
Project: {project_name}

## Corporate
- [ ] ASIC company details export
- [ ] Member register up to date
- [ ] Cap table (fully diluted) up to date
- [ ] Board minutes for any equity actions
- [ ] Constitution OR replaceable rules record

## IP & Legal
- [ ] Founder IP assignment signed
- [ ] Contributor/contractor IP assignment signed (everyone)
- [ ] Open-source license inventory (dependency locks/SBOM)
- [ ] Privacy policy + Terms (if collecting user data)
- [ ] Trademark plan (optional)

## Product & Revenue
- [ ] Pricing / subscription terms
- [ ] Payment provider exports
- [ ] Minimal bookkeeping (income/expenses)
- [ ] Support logs / known issues

## Technical
- [ ] Repo access controls
- [ ] Release process documented
- [ ] Backups + export/import
""")

    add(docs_dir / "SIGNING_CHECKLIST.md", """# Signing Checklist (Do Not Skip)

Before anyone contributes code/design:
- [ ] Contributor/Contractor signs IP assignment
- [ ] Repo access granted only after signing
- [ ] Open-source policy acknowledged

Before any share issue:
- [ ] Board minutes signed
- [ ] Member register updated
- [ ] Cap table updated
- [ ] Accountant review (especially if non-cash consideration)

Before any options grant:
- [ ] Option plan finalised (ESS review)
- [ ] Board approval
- [ ] Grant letter + vesting schedule
- [ ] Cap table updated (fully diluted)
""")

    # -------- legal/templates --------
    add(legal_templates / "FOUNDER_IP_ASSIGNMENT.md", f"""# Founder IP Assignment (Template)

IMPORTANT: Starting template only. Get AU legal review before signing.

## Parties
1) Company: {company_legal_name} (ACN {acn}, ABN {abn}), registered office: {registered_address}
2) Founder/Assignor: {founder_name} ({founder_email})

## Background
A) Founder has created and/or will create IP relating to the project {project_name} ("Project IP").
B) Company requires clear ownership of Project IP.

## 1. Assignment
Founder assigns to the Company all right, title and interest in the Project IP, worldwide (present + future rights).

## 2. Included IP (non-exhaustive)
- source code, scripts, configs, build tooling
- product/UI designs, visual assets, documentation
- brand names, logos, domains (if any)
- inventions, improvements, derivative works
- all related copyright + other IP rights

## 3. Moral Rights (Australia)
Founder consents to acts/omissions by the Company that might otherwise infringe moral rights, to the extent permitted by law.

## 4. Warranties
Founder warrants:
- Founder has the right to assign the Project IP
- Project IP does not knowingly infringe third-party rights
- third-party/open-source components are documented and used per license terms

## 5. Further Assurances
Founder will sign further documents reasonably required to give effect to this assignment.

## 6. Governing Law
Laws of {jurisdiction_state}, Australia.

--- EXECUTION ---

Signed for Company:
Name: _______________________________
Title: Director
Signature: ___________________________
Date: _______________________________

Signed by Founder/Assignor:
Name: {founder_name}
Signature: ___________________________
Date: _______________________________
""")

    add(legal_templates / "CONTRIBUTOR_IP_ASSIGNMENT.md", f"""# Contributor IP Assignment (Template)

IMPORTANT: Starting template only. Get AU legal review.

## Parties
1) Company: {company_legal_name} (ACN {acn})
2) Contributor: ____________________________ (email: ____________________)

## 1. Services / Work
Contributor provides contributions to {project_name} ("Work").

## 2. Assignment
Contributor assigns to the Company all right, title and interest in the Work and any IP created in performing the Work.

## 3. Pre-existing Materials
Contributor must disclose any pre-existing code/assets used.
Contributor grants the Company a perpetual, worldwide, royalty-free license to use any disclosed pre-existing materials incorporated into the Work.

## 4. Moral Rights (Australia)
Contributor consents to acts/omissions by the Company that might otherwise infringe moral rights, to the extent permitted by law.

## 5. Confidentiality
Contributor must keep Company confidential information confidential.

## 6. Warranties
Contributor warrants the Work does not knowingly infringe third-party rights and open-source use complies with licenses.

## 7. Governing Law
Laws of {jurisdiction_state}, Australia.

--- EXECUTION ---

Company:
Name: _______________________________
Title: Director
Signature: ___________________________
Date: _______________________________

Contributor:
Name: _______________________________
Signature: ___________________________
Date: _______________________________
""")

    add(legal_templates / "CONTRACTOR_AGREEMENT_IP_FOCUS.md", f"""# Contractor Agreement (IP-Focus Template)

IMPORTANT: Starting template only. Not a full contractor agreement. Get AU legal review.

## Parties
- Company: {company_legal_name} (ACN {acn})
- Contractor: ____________________________

## Scope / Deliverables
- ___________________________________________
- ___________________________________________

## Fee
- Fixed: $__________ AUD OR Hourly: $_____ AUD/hour
- Payment terms: Net ___ days upon invoice and acceptance.

## IP Ownership
- All deliverables, work product, and IP created under this engagement are assigned to the Company.
- Contractor must sign Contributor IP Assignment (or dedicated contractor IP assignment).

## Confidentiality
Contractor must keep Company information confidential.

## Independent Contractor
Contractor is not an employee; contractor handles their own tax/super/insurance.

## Warranty
Contractor warrants deliverables do not knowingly infringe third-party rights.

## Governing Law
Laws of {jurisdiction_state}, Australia.

--- EXECUTION ---

Company (Director): ___________________  Date: _______________
Contractor: ___________________________  Date: _______________
""")

    add(legal_templates / "OPTION_PLAN_STUB.md", f"""# Employee Option Plan (Stub)

NOT READY TO USE WITHOUT PROFESSIONAL SETUP.
This is a placeholder to define intent.

Company: {company_legal_name}
Project: {project_name}

## Purpose
Grant options to key contributors while preserving founder control.

## Suggested Defaults
- Vesting: 4 years
- Cliff: 12 months
- Vesting schedule: monthly thereafter
- Exercise price: FMV at grant (confirm with accountant)
- Total pool: 5–15% (create only when needed)

## Governance
- No grants without board approval + cap table update
- Every grant includes:
  - grant letter
  - vesting schedule
  - signed IP assignment (if not already)
  - tax review for ESS implications

## Next actions (when revenue exists)
- Engage AU accountant/lawyer for ESS plan + documentation
- Decide pool size + grant bands
""")

    add(legal_templates / "BOARD_MINUTES_SHARE_ISSUE.md", f"""# Board Minutes — Share Issue (Template)

Company: {company_legal_name}
ACN: {acn}

Date: ______________________
Location: ___________________
Present:
- {director_name} (Director)

1) Chair
The Chair noted a quorum was present and declared the meeting open.

2) Share Issue
The Director resolved that the Company issue:
- Class: Ordinary
- Number: ___________
- Issue price: $__________ per share
- Consideration: Cash / Services / Other (specify): ______________________
- Allottee: ______________________

3) Registers and Notifications
The Director resolved to:
- Update the member register
- Prepare any share certificates (if used)
- Lodge any required notices/updates

4) Close
There being no further business, the meeting closed.

Signed:
___________________________
{director_name}
Director
""")

    add(legal_templates / "OPEN_SOURCE_POLICY.md", f"""# Open Source Policy (Minimal)

Project: {project_name}
Company: {company_legal_name}

## Allowed (generally low friction)
- MIT, Apache-2.0, BSD-2/3, ISC

## Needs review
- GPL/AGPL (strong copyleft)
- any license with field-of-use restrictions
- any code copied from non-open sources

## Rules
- dependencies must be lockfile-pinned where possible
- no unlicensed snippets
- if in doubt: treat as blocked until reviewed
""")

    add(legal_templates / "IP_CHAIN_SUMMARY.md", f"""# IP Chain Summary (Fill + keep updated)

Company: {company_legal_name}
Project: {project_name}

## Founder
- Founder IP Assignment signed?  YES / NO
- Date: __________
- Stored at: legal/signed/FOUNDER_IP_ASSIGNMENT.pdf

## Contributors/Contractors
List everyone who touched code/design:
- Name: __________  Role: __________  IP signed: YES/NO  Date: ______  File: ______
- Name: __________  Role: __________  IP signed: YES/NO  Date: ______  File: ______

## Third-party assets
- Fonts: __________  license: __________
- Icons: __________  license: __________
- Images: __________  license: __________

## Accounts / Domains
- Domain registrar: __________  Owner: Company/Personal  Transfer planned: YES/NO
- Payments: __________ owner: Company/Personal
- Git hosting: __________ owner: Company/Personal
""")

    # -------- legal/registers --------
    add(legal_registers / "MEMBER_REGISTER.csv", "MemberName,MemberAddress,Email,ShareClass,Shares,IssueDate,IssuePriceAUD,CertificateNumber,Notes\n")
    add(legal_registers / "CAP_TABLE.csv", "Holder,Instrument,Class,SharesOrOptions,PercentFullyDiluted,Notes\nFounder,Share,Ordinary,100,100.00,Initial issue\nOptionPool,Option,Ordinary,0,0.00,Create only when needed\n")

    # -------- placeholders / notes --------
    add(ROOT / "OWNERSHIP_STACK_NOTE.md", f"""# Ownership Stack Note (Quick)

Company: {company_legal_name}
Project: {project_name}
Generated: {stamp}

This repo now includes:
- docs/ownership/  (intent + metrics + checklists)
- legal/templates/ (templates for IP, contractors, minutes)
- legal/registers/ (cap table + member register)
- legal/signed/    (store signed PDFs here)

Rule: company owns IP; no equity-for-help; options later with vesting after revenue.
""")

    add(legal_signed / ".gitkeep", "")
    add(legal_templates / ".gitkeep", "")
    add(legal_registers / ".gitkeep", "")

    # -------- launchers (one button) --------
    add(ROOT / "SWARMZ_OWNERSHIP_PACK_UP.cmd", """@echo off
setlocal
cd /d %~dp0
py ONE_BUTTON_SWARMZ_OWNERSHIP_PACK.py
echo.
echo DONE. Check: docs\\ownership and legal\\*
endlocal
""")

    add(ROOT / "SWARMZ_OWNERSHIP_PACK_UP.ps1", r"""$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
python .\ONE_BUTTON_SWARMZ_OWNERSHIP_PACK.py
Write-Host ""
Write-Host "DONE. Check: docs\ownership and legal\*"
""")

    # -------- self-check --------
    add(ROOT / "SWARMZ_OWNERSHIP_PACK_SELF_CHECK.py", r"""#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path.cwd()

REQUIRED = [
    Path("docs/ownership/README_OWNERSHIP_STACK.md"),
    Path("docs/ownership/CAP_TABLE_INTENT.md"),
    Path("docs/ownership/OUTCOME_METRICS.md"),
    Path("legal/templates/FOUNDER_IP_ASSIGNMENT.md"),
    Path("legal/templates/CONTRIBUTOR_IP_ASSIGNMENT.md"),
    Path("legal/registers/CAP_TABLE.csv"),
    Path("legal/registers/MEMBER_REGISTER.csv"),
]

missing = [p for p in REQUIRED if not (ROOT / p).exists()]

print("SWARMZ OWNERSHIP PACK — SELF CHECK")
print("Repo:", ROOT)

if missing:
    print("\nMISSING:")
    for p in missing:
        print(" -", p)
    print("\nFix: run ONE_BUTTON_SWARMZ_OWNERSHIP_PACK.py")
    sys.exit(1)

print("\nOK: required files present.")
print("\nNEXT ACTIONS:")
print(" 1) Put signed PDFs in legal/signed/")
print(" 2) Require IP assignment before repo access for any contributor")
print(" 3) Keep cap table founder-controlled; do not issue equity casually")
sys.exit(0)
""")

    # Output
    print("\nCREATED:")
    if created:
        for p in sorted(created):
            print(f" - {p}")
    else:
        print(" (nothing new; files already existed)")

    print("\nRUN LAUNCHERS:")
    print(" CMD:        SWARMZ_OWNERSHIP_PACK_UP.cmd")
    print(" PowerShell: .\\SWARMZ_OWNERSHIP_PACK_UP.ps1")
    print("\nSELF CHECK:")
    print(" CMD:        py SWARMZ_OWNERSHIP_PACK_SELF_CHECK.py")
    print(" PowerShell: python .\\SWARMZ_OWNERSHIP_PACK_SELF_CHECK.py")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
