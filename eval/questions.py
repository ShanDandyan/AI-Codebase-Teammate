# eval/questions.py

EVAL_QUESTIONS = [
    # --- 1. File Listing & Counts (3) ---
    {
        "id": 1,
        "question": "List all top-level files in ShanDandyan/DocuMind-AI.",
        "expected_tools": ["list_files"],
        "required_facts": ["README.md", "app.py", "requirements.txt"],
    },
    {
        "id": 2,
        "question": "What files exist at the root of octocat/Hello-World?",
        "expected_tools": ["list_files"],
        "required_facts": ["README"],
    },
    {
        "id": 3,
        "question": "How many top-level files are in ShanDandyan/DocuMind-AI?",
        "expected_tools": ["list_files"],
        "required_facts": [["3", "three"]],
    },
    # --- 2. Exact Code & Config Extraction (6) ---
    {
        "id": 4,
        "question": "Which exact HuggingFace embedding model is specified in ShanDandyan/DocuMind-AI's documentation?",
        "expected_tools": ["read_file"],
        "required_facts": ["all-MiniLM-L6-v2"],
    },
    {
        "id": 5,
        "question": "Which Llama model family is referenced in ShanDandyan/DocuMind-AI's README?",
        "expected_tools": ["read_file"],
        "required_facts": ["Llama 3.1"],
    },
    {
        "id": 6,
        "question": "What CLI command is documented to start ShanDandyan/DocuMind-AI locally?",
        "expected_tools": ["read_file"],
        "required_facts": ["streamlit run app.py"],
    },
    {
        "id": 7,
        "question": "Does ShanDandyan/DocuMind-AI retain conversation history across multiple questions? Answer based on the docs.",
        "expected_tools": ["read_file"],
        "required_facts": [["does not", "doesn't", "independently", "no"]],
    },
    {
        "id": 8,
        "question": "What vector similarity library is listed in ShanDandyan/DocuMind-AI's requirements.txt?",
        "expected_tools": ["read_file"],
        "required_facts": ["faiss"],
    },
    {
        "id": 9,
        "question": "Read app.py in ShanDandyan/DocuMind-AI and name the PDF loader or text splitter class imported.",
        "expected_tools": ["read_file"],
        "required_facts": [["PyPDFLoader", "RecursiveCharacterTextSplitter"]],
    },
    # --- 3. Specific Commit History & SHAs (4) ---
    {
        "id": 10,
        "question": "Find the commit in ShanDandyan/DocuMind-AI that fixed the requirements filename. What is its short SHA?",
        "expected_tools": ["get_commit_history"],
        "required_facts": ["0022c4d"],
    },
    {
        "id": 11,
        "question": "In ShanDandyan/DocuMind-AI, what date was commit 0022c4d authored?",
        "expected_tools": ["get_commit_history"],
        "required_facts": ["2026-07-13"],
    },
    {
        "id": 12,
        "question": "Fetch the commit history of octocat/Hello-World and state the author name of the oldest visible commit.",
        "expected_tools": ["get_commit_history"],
        "required_facts": ["cameronmcefee"],
    },
    {
        "id": 13,
        "question": "Check the last 5 commits in ShanDandyan/DocuMind-AI. Was there a commit fixing 'requirements.txt'?",
        "expected_tools": ["get_commit_history"],
        "required_facts": [["yes", "fix filename"]],
    },
    # --- 4. Multi-Step Reasoning (Tool A -> Tool B) (5) ---
    {
        "id": 14,
        "question": "Inspect the repository ShanDandyan/DocuMind-AI, find the main Python application script, and tell me what UI framework it imports.",
        "expected_tools": ["list_files", "read_file"],
        "required_facts": ["streamlit"],
    },
    {
        "id": 15,
        "question": "Check what files exist in ShanDandyan/DocuMind-AI, read the dependency file, and confirm if PyPDF or pypdf is required.",
        "expected_tools": ["list_files", "read_file"],
        "required_facts": ["pypdf"],
    },
    {
        "id": 16,
        "question": "Explore octocat/Hello-World from scratch and tell me the exact sentence written inside its only file.",
        "expected_tools": ["list_files", "read_file"],
        "required_facts": ["Hello World"],
    },
    {
        "id": 17,
        "question": "Find out how users supply their API key in ShanDandyan/DocuMind-AI by checking the repo files and reading the setup guide.",
        "expected_tools": ["list_files", "read_file"],
        "required_facts": [["enter", "own", "groq api key", "console.groq.com"]],
    },
    {
        "id": 18,
        "question": "Look at the files in ShanDandyan/DocuMind-AI and verify whether a Dockerfile exists.",
        "expected_tools": ["list_files"],
        "required_facts": [["no", "does not", "doesn't", "not present"]],
        "forbidden_facts": ["FROM python", "EXPOSE"],
    },
    # --- 5. Traps, Edge Cases & Anti-Hallucination (6) ---
    {
        "id": 19,
        "question": "Read server_config.json in ShanDandyan/DocuMind-AI and list the configured port.",
        "expected_tools": [["read_file", "list_files"]],
        "required_facts": [
            ["does not exist", "doesn't exist", "not found", "could not find", "404", "there is no", "not present"]
        ],
        "forbidden_facts": ["8000", "8080", "5432", "{"],
    },
    {
        "id": 20,
        "question": "Show me the SQL schema inside database_schema.sql in octocat/Hello-World.",
        "expected_tools": [["read_file", "list_files"]],
        "required_facts": [
            ["does not exist", "doesn't exist", "not found", "could not find", "404", "there is no", "not present"]
        ],
        "forbidden_facts": ["CREATE TABLE", "SELECT", "PRIMARY KEY"],
    },
    {
        "id": 21,
        "question": "What is the support email address of the maintainer listed in ShanDandyan/DocuMind-AI?",
        "expected_tools": ["read_file"],
        "required_facts": [
            ["not listed", "no email", "not provided", "does not contain", "not mentioned", "no support email"]
        ],
        "forbidden_facts": ["@gmail.com", "@github.com", "support@"],
    },
    {
        "id": 22,
        "question": "Read the LICENSE file in ShanDandyan/DocuMind-AI and state which open-source license it uses.",
        "expected_tools": [["read_file", "list_files"]],
        "required_facts": [
            ["does not exist", "doesn't exist", "not found", "404", "no license", "there is no"]
        ],
        "forbidden_facts": ["MIT License", "Apache License", "GNU"],
    },
    {
        "id": 23,
        "question": "Try to read the directory 'src' as a file in ShanDandyan/DocuMind-AI.",
        "expected_tools": [["read_file", "list_files"]],
        "required_facts": [
            ["not found", "does not exist", "404", "directory", "not a readable file", "there is no"]
        ],
    },
    {
        "id": 24,
        "question": "What is the chunk_size parameter configured in ShanDandyan/DocuMind-AI's app.py?",
        "expected_tools": ["read_file"],
        "required_facts": [["1000", "500", "chunk_size"]],
    },
]
