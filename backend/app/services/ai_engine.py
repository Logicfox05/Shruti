import os
import json
import random
import re
from typing import List, Dict, Any

class AIEngine:
    @staticmethod
    def generate_resume_questions(resume_text: str, detected_skills: List[str], role: str) -> List[Dict[str, Any]]:
        text_lower = resume_text.lower() if resume_text else ""

        # A. AI, COMPUTER VISION & DEEP LEARNING VERIFICATION POOL
        ai_cv_pool = [
            {
                "trigger_words": ["yolo", "object detection", "vision"],
                "category": "Resume Verification: YOLO Object Detection",
                "topic": "IoU & Non-Max Suppression (NMS)",
                "cognitive_level": "Intermediate",
                "question_text": "On your resume you highlighted YOLO object detection. During inference, why is Non-Maximum Suppression (NMS) applied to candidate bounding boxes?",
                "option_a": "To eliminate redundant overlapping bounding boxes and retain only the box with the highest confidence score for each object",
                "option_b": "To increase image resolution by 4x",
                "option_c": "To convert color images to grayscale",
                "option_d": "To calculate financial depreciation of cameras",
                "correct_option": "A",
                "explanation": "NMS filters out redundant bounding boxes based on Intersection over Union (IoU) overlap thresholds."
            },
            {
                "trigger_words": ["cnn", "deep learning", "convolutional", "tensorflow", "pytorch"],
                "category": "Resume Verification: Deep Learning & CNNs",
                "topic": "Convolution Kernels & Feature Extraction",
                "cognitive_level": "Intermediate",
                "question_text": "You listed CNNs and Deep Learning on your resume. In a Convolutional Neural Network, what is the mathematical function of a 3x3 Convolutional Filter (Kernel)?",
                "option_a": "It slides over the input matrix performing element-wise dot products to extract spatial features like edges, textures, and shapes",
                "option_b": "It computes the average selling price of products",
                "option_c": "It deletes negative weights without mathematical calculation",
                "option_d": "It compiles Python code into C++",
                "correct_option": "A",
                "explanation": "Convolution filters perform element-wise multiplication and summation over local receptive fields to detect spatial features."
            },
            {
                "trigger_words": ["opencv", "cv2", "image processing"],
                "category": "Resume Verification: OpenCV Processing",
                "topic": "OpenCV BGR vs RGB Color Order",
                "cognitive_level": "Basic",
                "question_text": "Regarding OpenCV image processing on your resume: When reading an image via `cv2.imread()`, what is the default color channel ordering in OpenCV?",
                "option_a": "BGR (Blue, Green, Red)",
                "option_b": "RGB (Red, Green, Blue)",
                "option_c": "CMYK (Cyan, Magenta, Yellow, Black)",
                "option_d": "Grayscale only",
                "correct_option": "A",
                "explanation": "OpenCV natively reads image arrays in BGR order rather than standard RGB."
            },
            {
                "trigger_words": ["tensorflow", "keras", "backpropagation", "loss"],
                "category": "Resume Verification: TensorFlow & Neural Training",
                "topic": "Loss Functions & Backpropagation",
                "cognitive_level": "Intermediate",
                "question_text": "In TensorFlow model training: How do optimizers (such as Adam or SGD) update neural network weights during backpropagation?",
                "option_a": "By computing gradients of the loss function with respect to weights using the Chain Rule of Calculus",
                "option_b": "By randomly assigning new numbers until accuracy reaches 100%",
                "option_c": "By increasing learning rate exponentially after every step",
                "option_d": "By filing statutory tax returns",
                "correct_option": "A",
                "explanation": "Backpropagation computes the gradient of the loss function with respect to each weight via the calculus chain rule."
            },
            {
                "trigger_words": ["python", "python3"],
                "category": "Resume Verification: Python Architecture",
                "topic": "Python Memory Management & GIL",
                "cognitive_level": "Intermediate",
                "question_text": "In Python programming on your resume: What is the primary role of the Global Interpreter Lock (GIL) in CPython?",
                "option_a": "It ensures thread safety by allowing only one native thread to execute Python bytecode at any given moment",
                "option_b": "It converts Python scripts into standalone Android APKs",
                "option_c": "It automatically balances double-entry financial ledgers",
                "option_d": "It deletes all unused variables instantly from disk",
                "correct_option": "A",
                "explanation": "The GIL is a mutex in CPython that prevents multiple native threads from executing Python bytecodes concurrently."
            },
            {
                "trigger_words": ["sql", "databases", "postgresql", "mysql"],
                "category": "Resume Verification: Database Engineering",
                "topic": "SQL Indexing & Query Performance",
                "cognitive_level": "Intermediate",
                "question_text": "You claimed SQL and database expertise. Why does a B-Tree Index dramatically accelerate query search performance on large tables?",
                "option_a": "It reduces search lookup time complexity from O(N) full-table scans to O(log N) balanced tree traversals",
                "option_b": "It encrypts table columns automatically",
                "option_c": "It eliminates foreign key constraints",
                "option_d": "It turns relational tables into HTML files",
                "correct_option": "A",
                "explanation": "B-Tree indexes enable O(log N) binary search lookup instead of scanning all N rows."
            },
            {
                "trigger_words": ["computer vision", "pixel", "normalization"],
                "category": "Resume Verification: Computer Vision Pipeline",
                "topic": "Pixel Value Normalization",
                "cognitive_level": "Basic",
                "question_text": "Why are image pixel arrays (0 to 255) typically divided by 255.0 before feeding them into deep neural network models?",
                "option_a": "To normalize input feature values into the range [0.0, 1.0], preventing gradient explosion and accelerating convergence",
                "option_b": "To compress image file size on the hard drive",
                "option_c": "To convert the image to high-definition 4K",
                "option_d": "To calculate bank interest rates",
                "correct_option": "A",
                "explanation": "Scaling pixel values to [0, 1] standardizes input distributions, stabilizing gradient descent during neural training."
            },
            {
                "trigger_words": ["machine learning", "scikit", "pandas", "numpy"],
                "category": "Resume Verification: Machine Learning",
                "topic": "Precision vs Recall Trade-Off",
                "cognitive_level": "Intermediate",
                "question_text": "In predictive model evaluation: What does high Precision (98%) but low Recall (45%) signify in an object detection or classification system?",
                "option_a": "When the model predicts a positive detection it is almost always correct, but it fails to detect more than half of the actual objects present (high false negatives)",
                "option_b": "The model has 100% perfect detection across all categories",
                "option_c": "The model is underfitting and guessing randomly",
                "option_d": "Precision and Recall are always identical numbers",
                "correct_option": "A",
                "explanation": "High precision means low false positives, but low recall indicates a high rate of missed positive instances (false negatives)."
            },
            {
                "trigger_words": ["git", "github", "gitlab"],
                "category": "Resume Verification: Version Control",
                "topic": "Git Merge vs Git Rebase",
                "cognitive_level": "Intermediate",
                "question_text": "In your Git experience: What is the fundamental difference between `git merge` and `git rebase`?",
                "option_a": "Merge preserves complete branching history via a merge commit; Rebase reapplies feature commits linearly on top of the base branch",
                "option_b": "Rebase deletes all commits from the repository",
                "option_c": "Merge only works on remote repositories",
                "option_d": "There is no difference between merge and rebase",
                "correct_option": "A",
                "explanation": "git merge preserves branch history with a diamond commit; git rebase rewrites commit history into a single linear sequence."
            },
            {
                "trigger_words": ["java", "javascript", "web", "oop"],
                "category": "Resume Verification: Programming Fundamentals",
                "topic": "Object-Oriented Encapsulation",
                "cognitive_level": "Basic",
                "question_text": "In object-oriented software engineering: What is the primary purpose of Encapsulation?",
                "option_a": "To bundle data and methods operating on that data within a class while restricting direct external access to internal state",
                "option_b": "To convert Java bytecode into JavaScript",
                "option_c": "To run unit tests automatically in CI/CD",
                "option_d": "To calculate invoice tax totals",
                "correct_option": "A",
                "explanation": "Encapsulation hides internal object state and requires all interaction to occur through defined public methods."
            },
            {
                "trigger_words": ["python", "python3", "pandas", "numpy"],
                "category": "Resume Verification: Python Programming",
                "topic": "Mutable vs Immutable Types",
                "cognitive_level": "Intermediate",
                "question_text": "You listed Python on your resume. Which of these built-in types is IMMUTABLE?",
                "option_a": "tuple",
                "option_b": "list",
                "option_c": "dict",
                "option_d": "set",
                "correct_option": "A",
                "explanation": "Tuples are immutable; lists, dicts and sets can be modified in place after creation."
            },
            {
                "trigger_words": ["sql", "postgresql", "mysql", "database", "query"],
                "category": "Resume Verification: SQL & Databases",
                "topic": "INNER JOIN Semantics",
                "cognitive_level": "Intermediate",
                "question_text": "Your resume claims SQL experience. What does an INNER JOIN between two tables return?",
                "option_a": "Only the rows that have matching keys in both tables",
                "option_b": "All rows from both tables regardless of matches",
                "option_c": "Only rows from the left table",
                "option_d": "Only rows that exist in neither table",
                "correct_option": "A",
                "explanation": "INNER JOIN returns the intersection: rows whose join key exists in both tables."
            },
            {
                "trigger_words": ["rest api", "restful", "fastapi", "flask", "django", "http"],
                "category": "Resume Verification: REST APIs",
                "topic": "HTTP Idempotency",
                "cognitive_level": "Intermediate",
                "question_text": "You listed REST API development. Which HTTP method is expected to be idempotent (same effect whether called once or many times)?",
                "option_a": "PUT",
                "option_b": "POST",
                "option_c": "PATCH (in the general case)",
                "option_d": "CONNECT",
                "correct_option": "A",
                "explanation": "PUT replaces a resource with the same payload each time, so repeated calls leave the same state; POST typically creates a new resource each call."
            },
            {
                "trigger_words": ["docker", "kubernetes", "container", "devops"],
                "category": "Resume Verification: Docker & Containers",
                "topic": "Image vs Container",
                "cognitive_level": "Basic",
                "question_text": "Your resume mentions Docker. What is the relationship between a Docker image and a Docker container?",
                "option_a": "A container is a running instance of an image",
                "option_b": "An image is a running instance of a container",
                "option_c": "They are two words for exactly the same thing",
                "option_d": "A container can only be built from source code, never from an image",
                "correct_option": "A",
                "explanation": "An image is the read-only template; a container is a live, running instance created from that image."
            },
            {
                "trigger_words": ["machine learning", "scikit-learn", "model", "overfitting"],
                "category": "Resume Verification: Machine Learning",
                "topic": "Overfitting",
                "cognitive_level": "Intermediate",
                "question_text": "You claim machine-learning experience. A model scores 99% on training data but 60% on unseen test data. What is this called?",
                "option_a": "Overfitting - the model memorised training noise and fails to generalise",
                "option_b": "Underfitting - the model is too simple",
                "option_c": "Perfect generalisation",
                "option_d": "Data leakage from the test set into production",
                "correct_option": "A",
                "explanation": "A large gap between high training accuracy and low test accuracy is the classic signature of overfitting."
            },
            {
                "trigger_words": ["aws", "azure", "gcp", "cloud", "ec2", "s3"],
                "category": "Resume Verification: Cloud Platforms",
                "topic": "Object Storage",
                "cognitive_level": "Basic",
                "question_text": "Your resume mentions cloud experience. Which AWS service is designed primarily for scalable object storage (files, backups, static assets)?",
                "option_a": "Amazon S3",
                "option_b": "Amazon EC2",
                "option_c": "Amazon RDS",
                "option_d": "AWS Lambda",
                "correct_option": "A",
                "explanation": "Amazon S3 (Simple Storage Service) is AWS's object storage; EC2 is compute, RDS is managed databases, Lambda is serverless functions."
            }
        ]

        # B. FINANCE & ACCOUNTING VERIFICATION POOL
        fin_pool = [
            {
                "trigger_words": ["gst", "gstr-3b", "gstr-1", "itc"],
                "category": "Resume Verification: GST Compliance",
                "topic": "Rule 37 180-Day ITC Reversal",
                "cognitive_level": "Intermediate",
                "question_text": "On your resume you highlighted GST reconciliation experience. Under CGST Rule 37, if payment is not made to a vendor within 180 days from invoice date, what is the mandatory action?",
                "option_a": "ITC availed must be reversed in GSTR-3B along with 18% annual interest",
                "option_b": "ITC can be retained permanently without interest",
                "option_c": "The vendor\'s GSTIN is automatically cancelled by the portal",
                "option_d": "The invoice amount must be transferred directly to the government escrow account",
                "correct_option": "A",
                "explanation": "Under Rule 37, failure to pay supplier within 180 days mandates ITC reversal with interest @ 18% p.a."
            },
            {
                "trigger_words": ["tds", "194q", "206c", "tcs"],
                "category": "Resume Verification: TDS Compliance",
                "topic": "Section 194Q vs 206C(1H) Priority",
                "cognitive_level": "Intermediate",
                "question_text": "Your profile claims experience handling TDS on purchase of goods. If both Section 194Q (buyer TDS) and Section 206C(1H) (seller TCS) apply on a transaction exceeding Rs 50 Lakhs, which takes statutory precedence?",
                "option_a": "Section 194Q takes precedence, and the seller shall not collect TCS",
                "option_b": "Section 206C(1H) overrides Section 194Q",
                "option_c": "Both TDS @ 0.1% and TCS @ 0.1% must be charged simultaneously",
                "option_d": "Neither applies if the buyer is a private limited company",
                "correct_option": "A",
                "explanation": "Under Section 194Q(5), if buyer is liable to deduct TDS under 194Q, seller shall not collect TCS under 206C(1H)."
            },
            {
                "trigger_words": ["accounts payable", "p2p", "3-way match", "grn"],
                "category": "Resume Verification: Accounts Payable",
                "topic": "3-Way Matching Verification",
                "cognitive_level": "Intermediate",
                "question_text": "You listed Accounts Payable on your resume. Before approving an invoice for payment, what does the 3-Way Match verify?",
                "option_a": "Purchase Order prices, Physical Goods Receipt Note (GRN) quantities, and Vendor Invoice billed amounts",
                "option_b": "Customer Credit Limit, Sales Order, and Dispatch Slip",
                "option_c": "Bank Balance, Cheque Counterfoil, and Cash Book",
                "option_d": "Employee Timesheet and Attendance Log",
                "correct_option": "A",
                "explanation": "3-Way matching compares the Purchase Order, Goods Receipt Note, and Vendor Invoice to verify quantity and pricing."
            },
            {
                "trigger_words": ["brs", "bank reconciliation", "banking"],
                "category": "Resume Verification: Treasury & Banking",
                "topic": "Unpresented Cheques & Timing Differences",
                "cognitive_level": "Basic",
                "question_text": "You noted Bank Reconciliation (BRS) experience. If a vendor cheque of Rs 4,50,000 was issued on 29th March but presented to the bank on 4th April, how is this handled in the March 31 BRS starting from Cash Book balance?",
                "option_a": "Added to Cash Book balance to arrive at Bank Passbook balance",
                "option_b": "Deducted from Cash Book balance",
                "option_c": "No adjustment required in BRS",
                "option_d": "Written off as a bad debt",
                "correct_option": "A",
                "explanation": "Cheques issued but not yet presented reduce the cash book; thus to reconcile to the passbook balance, they must be added back."
            },
            {
                "trigger_words": ["accounts receivable", "o2c", "billing", "debtors", "credit note"],
                "category": "Resume Verification: Accounts Receivable",
                "topic": "Credit Note Treatment in O2C",
                "cognitive_level": "Intermediate",
                "question_text": "You listed Accounts Receivable / O2C experience. A customer returns goods worth Rs 1,00,000 (plus 18% GST) after the tax invoice was raised. What is the correct document and effect?",
                "option_a": "Issue a GST credit note reducing both the receivable and the output GST liability",
                "option_b": "Issue a fresh sales invoice to the customer for the returned goods",
                "option_c": "Debit the customer account and increase revenue",
                "option_d": "No accounting entry is required until the next financial year",
                "correct_option": "A",
                "explanation": "Sales returns are recorded via a GST credit note, which lowers the debtor balance and reverses the proportionate output tax."
            },
            {
                "trigger_words": ["tally", "erp", "zoho", "quickbooks", "sap"],
                "category": "Resume Verification: Accounting Software",
                "topic": "Ledger Grouping in Tally",
                "cognitive_level": "Basic",
                "question_text": "Your resume mentions Tally / ERP experience. Under which default group should 'Sundry Creditors' be classified?",
                "option_a": "Current Liabilities",
                "option_b": "Current Assets",
                "option_c": "Direct Expenses",
                "option_d": "Fixed Assets",
                "correct_option": "A",
                "explanation": "Sundry Creditors (amounts owed to suppliers) are current liabilities in the balance sheet."
            },
            {
                "trigger_words": ["excel", "vlookup", "pivot", "spreadsheet"],
                "category": "Resume Verification: Excel Proficiency",
                "topic": "VLOOKUP Exact Match",
                "cognitive_level": "Basic",
                "question_text": "You highlighted advanced Excel skills. To fetch a vendor's PAN from a master sheet using VLOOKUP, what must the fourth argument (range_lookup) be for a reliable exact match?",
                "option_a": "FALSE (or 0), to force an exact match",
                "option_b": "TRUE (or 1), to allow an approximate match",
                "option_c": "The column index number",
                "option_d": "It must be left blank for text lookups",
                "correct_option": "A",
                "explanation": "range_lookup = FALSE returns an exact match; TRUE assumes the lookup column is sorted and returns approximate matches."
            },
            {
                "trigger_words": ["inventory", "stock", "costing", "valuation", "fifo"],
                "category": "Resume Verification: Inventory & Costing",
                "topic": "Inventory Valuation (AS 2 / Ind AS 2)",
                "cognitive_level": "Intermediate",
                "question_text": "Your profile claims inventory/costing work. Under AS 2, at what value should closing stock of finished goods normally be carried?",
                "option_a": "Lower of cost or net realisable value (NRV)",
                "option_b": "Always at the latest market selling price",
                "option_c": "Always at historical purchase cost regardless of NRV",
                "option_d": "At cost plus a standard 20% profit margin",
                "correct_option": "A",
                "explanation": "AS 2 requires inventory to be valued at the lower of cost and net realisable value."
            },
            {
                "trigger_words": ["depreciation", "fixed asset", "wdv", "slm"],
                "category": "Resume Verification: Fixed Assets",
                "topic": "Straight Line Depreciation",
                "cognitive_level": "Basic",
                "question_text": "You noted fixed-asset accounting experience. A machine costing Rs 5,00,000 with a 5-year useful life and nil residual value is depreciated on SLM. What is the annual depreciation?",
                "option_a": "Rs 1,00,000",
                "option_b": "Rs 50,000",
                "option_c": "Rs 2,00,000",
                "option_d": "Rs 25,000",
                "correct_option": "A",
                "explanation": "SLM depreciation = (Cost - Residual) / Useful Life = 5,00,000 / 5 = Rs 1,00,000 per year."
            },
            {
                "trigger_words": ["financial reporting", "accrual", "provision", "gaap", "ind as"],
                "category": "Resume Verification: Financial Reporting",
                "topic": "Accrual Concept",
                "cognitive_level": "Intermediate",
                "question_text": "You listed financial reporting experience. Under the accrual concept, when should electricity expense for March (bill received in April) be recognised?",
                "option_a": "In March, by creating an expense provision / accrual",
                "option_b": "In April, when the bill is physically received",
                "option_c": "In April, only when the payment is actually made",
                "option_d": "Split equally between March and April",
                "correct_option": "A",
                "explanation": "Accrual accounting recognises expenses in the period they are incurred, regardless of when the bill is received or paid."
            },
            {
                "trigger_words": ["e-way bill", "eway", "gst", "logistics"],
                "category": "Resume Verification: GST Compliance",
                "topic": "E-Way Bill Threshold",
                "cognitive_level": "Basic",
                "question_text": "Your resume claims GST logistics experience. For inter-state movement of goods, above what consignment value is an e-way bill generally mandatory?",
                "option_a": "Rs 50,000",
                "option_b": "Rs 10,000",
                "option_c": "Rs 1,00,000",
                "option_d": "Rs 2,50,000",
                "correct_option": "A",
                "explanation": "An e-way bill is generally required when the consignment value exceeds Rs 50,000."
            },
            {
                "trigger_words": ["tds", "194c", "contractor", "form 26q"],
                "category": "Resume Verification: TDS Compliance",
                "topic": "Section 194C Contractor TDS",
                "cognitive_level": "Intermediate",
                "question_text": "You claim TDS compliance experience. What is the TDS rate under Section 194C on a payment to a resident contractor that is a partnership firm (PAN available)?",
                "option_a": "2%",
                "option_b": "1%",
                "option_c": "10%",
                "option_d": "5%",
                "correct_option": "A",
                "explanation": "Under 194C, TDS is 1% for individuals/HUF and 2% for other entities such as firms and companies (PAN available)."
            },
            {
                "trigger_words": ["payroll", "pf", "esi", "salary", "provident"],
                "category": "Resume Verification: Payroll & Statutory",
                "topic": "Provident Fund Contribution",
                "cognitive_level": "Basic",
                "question_text": "Your resume mentions payroll processing. What is the standard employee Provident Fund (EPF) contribution rate on basic wages plus DA?",
                "option_a": "12%",
                "option_b": "6%",
                "option_c": "18%",
                "option_d": "10%",
                "correct_option": "A",
                "explanation": "The statutory EPF contribution is 12% of basic wages plus dearness allowance for both employee and employer."
            },
            {
                "trigger_words": ["cash flow", "cash flow statement", "treasury", "working capital"],
                "category": "Resume Verification: Cash Flow & MIS",
                "topic": "Operating vs Net Profit",
                "cognitive_level": "Advanced",
                "question_text": "You listed MIS / cash-flow reporting. A company reports healthy net profit but negative operating cash flow. What is the most likely explanation?",
                "option_a": "Profits are locked in rising receivables and inventory that have not yet converted to cash",
                "option_b": "The company has no expenses at all",
                "option_c": "Net profit and operating cash flow are always identical",
                "option_d": "Depreciation was never charged in the accounts",
                "correct_option": "A",
                "explanation": "Accrual profit can be positive while cash is tied up in working capital (debtors and stock), producing negative operating cash flow."
            },
            {
                "trigger_words": ["reconciliation", "ledger", "journal", "double entry", "bookkeeping"],
                "category": "Resume Verification: Bookkeeping",
                "topic": "Golden Rules of Accounting",
                "cognitive_level": "Basic",
                "question_text": "You listed core bookkeeping skills. When a business pays rent by cheque, what is the correct journal entry?",
                "option_a": "Debit Rent Expense, Credit Bank",
                "option_b": "Debit Bank, Credit Rent Expense",
                "option_c": "Debit Rent Expense, Credit Capital",
                "option_d": "Debit Cash, Credit Rent Expense",
                "correct_option": "A",
                "explanation": "Rent is a nominal account (debit all expenses) and payment reduces the bank asset (credit what goes out)."
            },
            {
                "trigger_words": ["ratio", "analysis", "current ratio", "liquidity", "mis"],
                "category": "Resume Verification: Financial Analysis",
                "topic": "Current Ratio",
                "cognitive_level": "Intermediate",
                "question_text": "You listed financial analysis / MIS on your resume. If current assets are Rs 8,00,000 and current liabilities are Rs 4,00,000, what is the current ratio?",
                "option_a": "2:1",
                "option_b": "1:2",
                "option_c": "4:1",
                "option_d": "1:1",
                "correct_option": "A",
                "explanation": "Current ratio = Current Assets / Current Liabilities = 8,00,000 / 4,00,000 = 2:1."
            }
        ]

        # Domain matching logic. Word-boundary matching avoids false positives such as
        # "git" inside "digital" or "sql" inside a longer token, which previously routed
        # finance candidates into deep-learning questions.
        tech_signals = [
            r"\bpython\b", r"\byolo\b", r"\byolov[0-9]+\b", r"\bopencv\b", r"\btensorflow\b",
            r"\bpytorch\b", r"\bkeras\b", r"\bcnn\b", r"\brnn\b", r"\blstm\b",
            r"\bdeep learning\b", r"\bcomputer vision\b", r"\bmachine learning\b",
            r"\bdata science\b", r"\bb\.?\s?tech\b", r"\bsql\b", r"\bgit(?:hub)?\b",
            r"\bjava\b", r"\bjavascript\b", r"\bdjango\b", r"\bflask\b", r"\bfastapi\b",
            r"\bdocker\b", r"\bkubernetes\b", r"\bnlp\b", r"\bpandas\b", r"\bnumpy\b",
        ]
        is_tech = any(re.search(p, text_lower) for p in tech_signals)

        primary_pool = ai_cv_pool if is_tech else fin_pool
        secondary_pool = fin_pool if is_tech else ai_cv_pool

        # Assemble 16 DISTINCT questions: trigger-matched first (verifies specific
        # claims), then the rest of the primary pool, then the secondary pool if the
        # primary runs short. Never repeat a question -- repeats would distort the score.
        selected = []
        seen_texts = set()

        def _add(q):
            key = q["question_text"]
            if key not in seen_texts:
                seen_texts.add(key)
                selected.append(q)

        for q in primary_pool:
            if len(selected) >= 16:
                break
            if any(tw in text_lower for tw in q["trigger_words"]):
                _add(q)
        for q in primary_pool:
            if len(selected) >= 16:
                break
            _add(q)
        for q in secondary_pool:
            if len(selected) >= 16:
                break
            _add(q)

        return selected[:16]

    @staticmethod
    def generate_hiring_report(candidate: Any, session: Any, questions: List[Any], proctoring_events: List[Any]) -> Dict[str, Any]:
        total_questions = len(questions)
        correct_count = sum(1 for q in questions if q.is_correct)
        percentage = round((correct_count / total_questions * 100), 1) if total_questions > 0 else 0.0

        levels_map = {"Basic": {"total": 0, "correct": 0}, "Intermediate": {"total": 0, "correct": 0}, "Advanced": {"total": 0, "correct": 0}}
        for q in questions:
            lvl = q.cognitive_level or "Intermediate"
            if lvl not in levels_map:
                lvl = "Intermediate"
            levels_map[lvl]["total"] += 1
            if q.is_correct:
                levels_map[lvl]["correct"] += 1

        basic_pct = round((levels_map["Basic"]["correct"] / levels_map["Basic"]["total"] * 100), 1) if levels_map["Basic"]["total"] > 0 else 0.0
        inter_pct = round((levels_map["Intermediate"]["correct"] / levels_map["Intermediate"]["total"] * 100), 1) if levels_map["Intermediate"]["total"] > 0 else 0.0
        adv_pct = round((levels_map["Advanced"]["correct"] / levels_map["Advanced"]["total"] * 100), 1) if levels_map["Advanced"]["total"] > 0 else 0.0

        cognitive_summary = {
            "basic": {
                "score": basic_pct,
                "correct": levels_map["Basic"]["correct"],
                "total": levels_map["Basic"]["total"],
                "label": "Basic Tier (Foundations & Daily Tasks)",
                "status": "Mastered" if basic_pct >= 75 else ("Competent" if basic_pct >= 55 else "Needs Improvement")
            },
            "intermediate": {
                "score": inter_pct,
                "correct": levels_map["Intermediate"]["correct"],
                "total": levels_map["Intermediate"]["total"],
                "label": "Intermediate Tier (Operational & Core Technical)",
                "status": "Mastered" if inter_pct >= 75 else ("Competent" if inter_pct >= 55 else "Needs Improvement")
            },
            "advanced": {
                "score": adv_pct,
                "correct": levels_map["Advanced"]["correct"],
                "total": levels_map["Advanced"]["total"],
                "label": "Advanced Tier (Strategy, Controls & Architecture)",
                "status": "Mastered" if adv_pct >= 70 else ("Competent" if adv_pct >= 50 else "Underqualified")
            }
        }

        # Multi-Tier Placement Advice (verdict text only). The role-fit percentages are
        # computed from actual tier performance below, so they always track the score.
        if basic_pct >= 75 and inter_pct >= 70 and adv_pct >= 70:
            recommended_role = "Finance Manager"
            placement_verdict_title = "Great Fit for Finance Manager (Strategic Leadership & Controls)"
            placement_advice = f"Candidate achieved high mastery across ALL 3 TIERS (Basic: {basic_pct}%, Intermediate: {inter_pct}%, Advanced: {adv_pct}%). Demonstrates both strong operational accuracy and advanced control capability. Highly recommended for the Finance Manager role."
            verdict_badge = "success"
        elif basic_pct >= 70 and inter_pct >= 60:
            recommended_role = "Senior Accountant" if inter_pct >= 70 else "Accountant"
            placement_verdict_title = f"Hired for {recommended_role} (Not Ready for Finance Manager)"
            placement_advice = f"Candidate performed well in Basic ({basic_pct}%) and Intermediate ({inter_pct}%) tiers, proving strong day-to-day accuracy and operational competency. However, performance in the Advanced tier was {adv_pct}%. Recommended to hire in Accountant or Senior Accountant role, but NOT ready for Manager responsibilities."
            verdict_badge = "primary"
        elif basic_pct >= 60:
            recommended_role = "Accountant (Junior)"
            placement_verdict_title = "Hired as Junior / Entry-Level"
            placement_advice = f"Candidate has solid understanding of baseline tasks ({basic_pct}%), but showed notable gaps in intermediate problem solving ({inter_pct}%) and advanced strategy ({adv_pct}%). Best suited for an entry-level role under senior supervision."
            verdict_badge = "warning"
        else:
            recommended_role = "Do Not Hire"
            placement_verdict_title = "Do Not Hire (Fundamental Gaps Identified)"
            placement_advice = f"Candidate scored below baseline benchmarks ({basic_pct}% Basic, {inter_pct}% Intermediate). Not recommended for hiring."
            verdict_badge = "secondary"

        # Role fit derived from actual tier performance, weighted by what each role depends
        # on: Accountant leans on foundations (Basic), Senior on operational (Intermediate),
        # Manager on advanced strategy/controls. A low overall score therefore yields low fit
        # across every role, and a high score yields high fit.
        def _clamp(v):
            return round(max(0.0, min(100.0, v)), 1)

        basic_total = levels_map["Basic"]["total"]
        inter_total = levels_map["Intermediate"]["total"]
        adv_total = levels_map["Advanced"]["total"]

        # A higher tier only counts toward a role's fit if it was genuinely sampled
        # (>=3 questions AND scored above 0). This stops a single stray question from
        # crediting a candidate for a tier they never really demonstrated.
        inter_ok = inter_total >= 3 and inter_pct > 0
        adv_ok = adv_total >= 3 and adv_pct > 0

        accountant_fit = _clamp(0.70 * basic_pct + (0.30 * inter_pct if inter_ok else 0.0))
        senior_accountant_fit = _clamp(
            0.30 * basic_pct
            + (0.50 * inter_pct if inter_ok else 0.0)
            + (0.20 * adv_pct if adv_ok else 0.0)
        )
        # Finance Manager is gated on advanced ability: with no demonstrated advanced
        # performance the fit is 0 (never a small number inflated by the basic score).
        if adv_ok:
            manager_fit = _clamp(0.20 * basic_pct + (0.30 * inter_pct if inter_ok else 0.0) + 0.50 * adv_pct)
        else:
            manager_fit = 0.0

        def _fit_status(fit):
            if fit >= 85: return "Strong Fit"
            if fit >= 70: return "Good Fit"
            if fit >= 50: return "Moderate Fit"
            if fit >= 25: return "Developing"
            return "Not a Fit"

        # Score-based colour only (never an alarming red for a role the candidate did not apply to).
        def _fit_badge(fit):
            return "success" if fit >= 70 else ("warning" if fit >= 50 else "secondary")

        applied_role_name = (candidate.applied_role or "").strip()

        role_suitability = {
            "accountant": {
                "role_name": "Accountant (Junior)",
                "fit_percentage": accountant_fit,
                "status": _fit_status(accountant_fit),
                "badge": _fit_badge(accountant_fit),
                "applied": applied_role_name == "Accountant",
            },
            "senior_accountant": {
                "role_name": "Senior Accountant (Mid-Level)",
                "fit_percentage": senior_accountant_fit,
                "status": _fit_status(senior_accountant_fit),
                "badge": _fit_badge(senior_accountant_fit),
                "applied": applied_role_name == "Senior Accountant",
            },
            "finance_manager": {
                "role_name": "Finance Manager (Lead)",
                "fit_percentage": manager_fit,
                "status": _fit_status(manager_fit),
                "badge": _fit_badge(manager_fit),
                "applied": applied_role_name == "Finance Manager",
            },
        }

        # Topic Breakdown
        topic_stats = {}
        for q in questions:
            cat = q.category
            if cat not in topic_stats:
                topic_stats[cat] = {"total": 0, "correct": 0}
            topic_stats[cat]["total"] += 1
            if q.is_correct:
                topic_stats[cat]["correct"] += 1

        topic_breakdown = []
        for cat, data in topic_stats.items():
            pct = round((data["correct"] / data["total"] * 100), 1) if data["total"] > 0 else 0
            topic_breakdown.append({
                "category": cat,
                "total": data["total"],
                "correct": data["correct"],
                "percentage": pct
            })

        radar_categories = {
            "Accounts Payable & P2P": ["Payable", "Purchasing", "P2P", "GRN", "Vendor"],
            "Accounts Receivable & O2C": ["Receivable", "Billing", "O2C", "Sales", "Customer", "Challan"],
            "GST, TDS & Taxation": ["GST", "Taxation", "GSTR", "ITC", "RCM", "TDS", "TCS", "194", "206"],
            "Plant & Inventory": ["Inventory", "Stock", "Plant", "Stores", "Material"],
            "Banking, BRS & MIS": ["Banking", "BRS", "Treasury", "Reporting", "Bookkeeping", "Cash"],
            "IQ, Tech & Adaptability": ["IQ", "Analytical", "Numerical", "Reasoning", "Logic", "Adaptability", "YOLO", "Vision", "Deep Learning", "TensorFlow", "OpenCV", "Python", "SQL", "Git"]
        }

        radar_scores = {}
        for pillar, keywords in radar_categories.items():
            p_total = 0
            p_correct = 0
            for q in questions:
                if any(kw.lower() in q.category.lower() or kw.lower() in q.topic.lower() for kw in keywords):
                    p_total += 1
                    if q.is_correct:
                        p_correct += 1
            radar_scores[pillar] = round((p_correct / p_total * 100), 1) if p_total > 0 else percentage

        resume_questions = [q for q in questions if q.is_resume_based]
        resume_total = len(resume_questions)
        resume_correct = sum(1 for q in resume_questions if q.is_correct)
        resume_score_pct = round((resume_correct / resume_total * 100), 1) if resume_total > 0 else 0.0

        resume_audit = []
        for rq in resume_questions[:8]:
            status = "Verified Genuine" if rq.is_correct else "Exaggeration / Skill Gap"
            clean_claimed = rq.category.replace("Resume Verification: ", "")
            resume_audit.append({
                "claimed_area": clean_claimed,
                "tested_concept": rq.topic,
                "result": "Passed" if rq.is_correct else "Failed",
                "status": status,
                "explanation": rq.explanation
            })

        tab_switches = sum(1 for e in proctoring_events if e.event_type in ["tab_switch", "window_blur"])
        fullscreen_exits = sum(1 for e in proctoring_events if e.event_type == "fullscreen_exit")
        paste_attempts = sum(1 for e in proctoring_events if e.event_type == "copy_paste_attempt")
        idle_count = sum(1 for e in proctoring_events if e.event_type == "idle")

        integrity_penalty = (tab_switches * 8) + (fullscreen_exits * 10) + (paste_attempts * 15)
        integrity_score = max(0, 100 - integrity_penalty)

        # Suggested in-person follow-up questions are chosen purely from the role the
        # candidate APPLIED FOR (not from random mistakes), so the panel probes the
        # competencies that role actually requires.
        role_interviews = {
            "Accountant": [
                {"domain": "Accounts Payable / P2P", "topic": "3-Way Match",
                 "suggested_question": "Walk us through the 3-way match you perform before releasing a vendor payment, and how you handle a quantity or price mismatch.",
                 "key_focus": "Purchase Order vs GRN vs Vendor Invoice matching; escalation and hold process on mismatches."},
                {"domain": "GST", "topic": "GSTR-2B / ITC",
                 "suggested_question": "How do you reconcile GSTR-2B with the purchase register before claiming Input Tax Credit each month?",
                 "key_focus": "Invoice matching, treatment of missing/mismatched invoices, eligible vs blocked ITC."},
                {"domain": "Banking", "topic": "Bank Reconciliation",
                 "suggested_question": "Describe the steps you follow to prepare a monthly Bank Reconciliation Statement.",
                 "key_focus": "Unpresented cheques, deposits in transit, bank charges/interest, correcting the cash book."},
                {"domain": "TDS", "topic": "Vendor TDS",
                 "suggested_question": "Which TDS sections do you commonly apply on vendor payments, and how do you deposit and file them on time?",
                 "key_focus": "194C / 194J / 194I applicability, deposit due date (7th), Form 26Q filing."},
            ],
            "Senior Accountant": [
                {"domain": "GST", "topic": "Rule 37 ITC Reversal",
                 "suggested_question": "How do you handle ITC reversal under Rule 37 when a vendor remains unpaid beyond 180 days, and the later re-claim?",
                 "key_focus": "Reversal in GSTR-3B with 18% interest; re-availment on payment."},
                {"domain": "Financial Reporting", "topic": "Month-End Close",
                 "suggested_question": "Describe your month-end close process and the key reconciliations and schedules you own.",
                 "key_focus": "Provisions/accruals, inter-company, ledger schedules, review controls, close calendar."},
                {"domain": "Inventory / Costing", "topic": "AS 2 Valuation",
                 "suggested_question": "How do you value closing inventory and treat abnormal losses at period end?",
                 "key_focus": "Lower of cost and NRV; exclusion of abnormal waste; consistency of method."},
                {"domain": "TDS / TCS", "topic": "194Q vs 206C(1H)",
                 "suggested_question": "On a large purchase where both 194Q and 206C(1H) could apply, how do you decide which prevails?",
                 "key_focus": "194Q buyer-TDS precedence, Rs 50 lakh thresholds, avoiding double deduction."},
            ],
            "Finance Manager": [
                {"domain": "Internal Controls", "topic": "P2P Controls",
                 "suggested_question": "How would you design internal controls over the procure-to-pay cycle to prevent duplicate or fraudulent payments?",
                 "key_focus": "Segregation of duties, approval matrix, automated 3-way match, vendor master controls."},
                {"domain": "MIS / Analysis", "topic": "Cash Flow vs Profit",
                 "suggested_question": "A unit reports healthy profit but negative operating cash flow. How do you investigate and present this to leadership?",
                 "key_focus": "Working-capital drag (receivables/inventory build-up), cash conversion cycle, corrective levers."},
                {"domain": "Budgeting", "topic": "Budget & Variance",
                 "suggested_question": "How do you build the annual budget and run monthly variance analysis with the operating teams?",
                 "key_focus": "Flexible budgeting, variance drivers, accountability and corrective action."},
                {"domain": "Compliance & Strategy", "topic": "Statutory Governance",
                 "suggested_question": "How do you ensure end-to-end statutory compliance (GST, TDS, Companies Act) across the finance function?",
                 "key_focus": "Compliance calendar, maker-checker review, audit readiness, risk escalation."},
            ],
        }
        interview_questions = role_interviews.get(applied_role_name, role_interviews["Accountant"])

        return {
            "candidate_name": candidate.full_name,
            "applied_role": candidate.applied_role,
            "years_of_experience": candidate.years_of_experience,
            "current_company": candidate.current_company or "N/A",
            "overall_score": percentage,
            "total_questions": total_questions,
            "correct_answers": correct_count,
            "hiring_verdict": placement_verdict_title,
            "verdict_badge": verdict_badge,
            "recommended_role": recommended_role,
            "placement_advice": placement_advice,
            "summary_rationale": placement_advice,
            "cognitive_summary": cognitive_summary,
            "role_suitability": role_suitability,
            "integrity_score": integrity_score,
            "proctoring_summary": {
                "tab_switches": tab_switches,
                "fullscreen_exits": fullscreen_exits,
                "paste_attempts": paste_attempts,
                "idle_count": idle_count
            },
            "radar_scores": radar_scores,
            "topic_breakdown": topic_breakdown,
            "resume_audit": {
                "score_pct": resume_score_pct,
                "items": resume_audit
            },
            "suggested_interview_questions": interview_questions
        }
