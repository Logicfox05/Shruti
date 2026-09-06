import os
import re
from typing import Dict, Any, List
from pypdf import PdfReader
from docx import Document

class ResumeParser:
    @staticmethod
    def extract_text(file_path: str) -> str:
        text = ""
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == ".pdf":
                reader = PdfReader(file_path)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            elif ext in [".docx", ".doc"]:
                doc = Document(file_path)
                for para in doc.paragraphs:
                    text += para.text + "\n"
            else:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
        except Exception as e:
            text = f"Error reading resume file: {str(e)}"
        return text.strip()

    @staticmethod
    def analyze_resume(text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # 1. Extract Email
        email = ""
        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
        if email_match:
            email = email_match.group(0).strip().lower()

        # 2. Extract Phone — Indian mobile first, then a general international/US fallback
        phone = ""
        in_match = re.search(r'(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}', text)
        if in_match:
            phone = in_match.group(0).strip()
        else:
            for cand in re.findall(r'[\+\(]?\d[\d\s().\-]{7,}\d', text):
                digits = re.sub(r'\D', '', cand)
                if 10 <= len(digits) <= 13:
                    phone = cand.strip()
                    break

        # 3. Extract Full Name (Top non-empty line before email/phone)
        full_name = ""
        for line in lines[:5]:
            clean_l = re.sub(r'[^a-zA-Z\s]', '', line).strip()
            if len(clean_l.split()) in [2, 3, 4] and not any(k in clean_l.lower() for k in ["curriculum", "resume", "profile", "summary", "contact", "email", "phone", "engineer"]):
                full_name = clean_l.title()
                break

        # 4. Comprehensive, precise skill extraction.
        # Each entry: (skill label, domain, [word-boundary patterns]). Finance/accounting
        # is covered in depth (phrases, abbreviations and tools) since that is the hiring
        # focus, alongside AI and software so any resume is classified correctly.
        skill_defs = [
            # ---- Finance & Accounting ----
            ("Financial Statements & Reporting", "finance", [r"\bfinancial statements?\b", r"\bfinancial reporting\b", r"\bbalance sheet\b", r"\bprofit (and|&) loss\b", r"\bp&l\b", r"\bincome statement\b"]),
            ("Month-End Close", "finance", [r"\bmonth[- ]?end close\b", r"\bmonthly close\b", r"\bperiod[- ]?end close\b", r"\bfinancial close\b", r"\bclose calendar\b"]),
            ("Budgeting & Forecasting", "finance", [r"\bbudget(ing|s)?\b", r"\bforecast(ing|s)?\b", r"\bvariance analysis\b"]),
            ("Cash Flow & Treasury", "finance", [r"\bcash[- ]?flow\b", r"\bcash management\b", r"\bcash forecasting\b", r"\btreasury\b", r"\bworking capital\b"]),
            ("Internal Controls", "finance", [r"\binternal controls?\b", r"\bsox\b", r"\bcontrols? framework\b"]),
            ("Audit & Assurance", "finance", [r"\baudit(s|ing)?\b", r"\bstatutory audit\b", r"\binternal audit\b", r"\baudit preparation\b"]),
            ("Accounts Payable (AP / P2P)", "finance", [r"\baccounts payable\b", r"\bap\b", r"\bp2p\b", r"\bvendor payments?\b", r"\b3-?way match\b", r"\bgrn\b"]),
            ("Accounts Receivable (AR / O2C)", "finance", [r"\baccounts receivable\b", r"\bar\b", r"\bo2c\b", r"\bbilling\b", r"\bcollections?\b", r"\bdebtors\b", r"\bcredit notes?\b"]),
            ("Payroll & Statutory", "finance", [r"\bpayroll\b", r"\bsalary processing\b", r"\bprovident fund\b", r"\bpf\b", r"\besi\b", r"\bgratuity\b"]),
            ("General Ledger & Bookkeeping", "finance", [r"\bgeneral ledger\b", r"\bgl\b", r"\bjournal entr(y|ies)\b", r"\bbookkeeping\b", r"\bchart of accounts\b"]),
            ("Bank Reconciliation", "finance", [r"\bbank reconciliation\b", r"\bbrs\b", r"\breconciliations?\b", r"\breconcil"]),
            ("Fixed Assets & Depreciation", "finance", [r"\bfixed assets?\b", r"\bdepreciation\b", r"\bcapex\b", r"\bcapital expenditure\b"]),
            ("GST Compliance", "finance", [r"\bgst\b", r"\bgstr[- ]?\d?[a-z]?\b", r"\bitc\b", r"\be-?way bill\b"]),
            ("TDS / Direct Taxation", "finance", [r"\btds\b", r"\btcs\b", r"\b194[a-z]?\b", r"\bincome tax\b", r"\bform 26q\b", r"\bwithholding tax\b"]),
            ("GAAP / IFRS / Ind AS", "finance", [r"\bgaap\b", r"\bus gaap\b", r"\bifrs\b", r"\bind as\b", r"\baccounting standards?\b"]),
            ("Financial Analysis & MIS", "finance", [r"\bfinancial analysis\b", r"\bmis\b", r"\bratio analysis\b", r"\bmanagement (reporting|analysis)\b", r"\bprofitability analysis\b", r"\bkpis?\b", r"\bdashboards?\b"]),
            ("Cost Accounting", "finance", [r"\bcost accounting\b", r"\bcosting\b", r"\bstandard costing\b", r"\bcost control\b", r"\bmarginal costing\b"]),
            ("Team Leadership", "finance", [r"\bteam (lead|leadership|development|management)\b", r"\bleading\b", r"\bsupervis(e|ing|ion)\b", r"\bmentor(ed|ing|s)?\b", r"\bpeople management\b"]),
            ("Tally / Tally Prime", "finance", [r"\btally\b"]),
            ("SAP (FICO / B1)", "finance", [r"\bsap\b"]),
            ("QuickBooks", "finance", [r"\bquickbooks\b"]),
            ("NetSuite", "finance", [r"\bnetsuite\b"]),
            ("Zoho Books", "finance", [r"\bzoho\b"]),
            ("Oracle Financials", "finance", [r"\boracle\b"]),
            ("Microsoft Excel (Advanced)", "finance", [r"\bexcel\b", r"\bvlookup\b", r"\bpivot tables?\b", r"\bspreadsheets?\b"]),

            # ---- AI & Machine Learning ----
            ("Computer Vision & YOLO", "ai", [r"\bcomputer vision\b", r"\byolo\b", r"\byolov[0-9]+\b", r"\bobject detection\b"]),
            ("Deep Learning & CNNs", "ai", [r"\bdeep learning\b", r"\bcnns?\b", r"\bconvolutional\b", r"\brnn\b", r"\blstm\b"]),
            ("TensorFlow & Keras", "ai", [r"\btensorflow\b", r"\bkeras\b"]),
            ("PyTorch", "ai", [r"\bpytorch\b"]),
            ("OpenCV", "ai", [r"\bopencv\b", r"\bcv2\b", r"\bimage processing\b"]),
            ("Machine Learning", "ai", [r"\bmachine learning\b", r"\bscikit-learn\b"]),
            ("Data Science (Pandas/NumPy)", "ai", [r"\bpandas\b", r"\bnumpy\b", r"\bdata science\b"]),
            ("Natural Language Processing", "ai", [r"\bnlp\b", r"\btransformers\b", r"\bhugging ?face\b", r"\bbert\b", r"\bllm\b"]),

            # ---- Software Engineering ----
            ("Python", "software", [r"\bpython3?\b"]),
            ("SQL & Databases", "software", [r"\bsql\b", r"\bpostgresql\b", r"\bmysql\b", r"\bsqlite\b", r"\bmongodb\b"]),
            ("Java", "software", [r"\bjava\b", r"\bspring boot\b"]),
            ("JavaScript & Web", "software", [r"\bjavascript\b", r"\btypescript\b", r"\breact\b", r"\bnode\.?js\b", r"\bhtml5?\b", r"\bcss3?\b"]),
            ("C / C++", "software", [r"\bc\+\+\b", r"\bc programming\b"]),
            ("REST APIs & Frameworks", "software", [r"\brest api\b", r"\brestful\b", r"\bfastapi\b", r"\bflask\b", r"\bdjango\b"]),
            ("Git & Version Control", "software", [r"\bgit\b", r"\bgithub\b", r"\bgitlab\b"]),
            ("Cloud (AWS/Azure/GCP)", "software", [r"\baws\b", r"\bamazon web services\b", r"\bazure\b", r"\bgcp\b", r"\bec2\b", r"\bs3\b"]),
            ("Docker & Kubernetes", "software", [r"\bdocker\b", r"\bkubernetes\b"]),
        ]

        detected_skills = []
        domain_scores = {"ai": 0, "software": 0, "finance": 0}
        for label, domain, patterns in skill_defs:
            if any(re.search(pat, text_lower) for pat in patterns):
                detected_skills.append(label)
                domain_scores[domain] += 2 if domain in ("finance", "ai") else 1

        _domain_names = {
            "ai": "AI & Machine Learning",
            "software": "Software Engineering",
            "finance": "Finance & Accounting",
        }
        primary_key = max(domain_scores, key=domain_scores.get)
        primary_domain = _domain_names[primary_key] if domain_scores[primary_key] > 0 else "General Professional"

        # 5. Extract Degrees & CGPA
        degrees = []
        degree_patterns = {
            "B.Tech Computer Engineering (AI)": r"\bb\.?tech.*(?:artificial intelligence|computer|ai)\b",
            "B.Tech / B.E.": r"\b(b\.?tech|b\.?e\.|bachelor of technology|bachelor of engineering)\b",
            "M.Tech / M.E.": r"\b(m\.?tech|m\.?e\.|master of technology)\b",
            "BCA / MCA": r"\b(bca|mca|bachelor of computer applications)\b",
            "B.Com / M.Com": r"\b(b\.?com|m\.?com|bachelor of commerce)\b",
            "MBA": r"\b(mba|master of business administration)\b",
            "Chartered Accountant (CA)": r"\b(chartered accountant|ca inter|ca final)\b"
        }
        for deg_name, deg_pat in degree_patterns.items():
            if re.search(deg_pat, text_lower):
                degrees.append(deg_name)
                break

        cgpa_match = re.search(r'(?:cgpa|gpa|score)\s*[:=]?\s*(\d+(?:\.\d+)?(?:\s*\/\s*10)?)', text_lower)
        cgpa = cgpa_match.group(0).upper() if cgpa_match else ""

        exp_years = 0.0
        exp_match = re.search(r'(\d+(?:\.\d+)?)\s*\+?\s*years?(?:\s+of)?\s+experience', text_lower)
        if exp_match:
            try:
                exp_years = float(exp_match.group(1))
            except:
                pass

        return {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "primary_domain": primary_domain,
            "detected_skills": detected_skills,
            "detected_degrees": degrees,
            "cgpa": cgpa,
            "estimated_years": exp_years,
            "raw_length": len(text)
        }
