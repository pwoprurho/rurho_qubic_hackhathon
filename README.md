# 🚀 Q-Gen Agent: The Intelligent Architect for the Qubic Network

**[Project Name]** Q-Gen Agent
**[Track]** Nostromo Launchpad (Infrastructure & Middleware)
**[Status]** Submission Ready

-----

### ⭐ Project Summary

**Q-Gen Agent** is the first AI-powered architect for the Qubic Network. It revolutionizes smart contract development by instantly transforming natural language prompts into secure, verified C++ code. The platform features real-time security auditing, multi-language reports (54+ languages), and cryptographic commitment logging to eliminate the "Blank Canvas" barrier for developers.

-----

### 💡 The Problem: The "Blank Canvas" Barrier

Developing high-performance smart contracts on Qubic's specialized **Execution Flow Interface (EFI)** poses significant challenges:

1.  **High Complexity:** Writing secure C++ code for Qubic's low-level execution environment is daunting for newcomers, creating a massive barrier to entry.
2.  **Security Risks:** Manual code audits are costly and slow. A single, overlooked vulnerability (like reentrancy) can jeopardize an entire contract, making proactive security essential.

### 🎯 The Solution: From Intent to Immutable Code

Q-Gen Agent replaces the manual development struggle with an intelligent, end-to-end workflow. It acts as a **Generative Agent**, streamlining development into three core steps:

1.  **Generation:** User provides intent (e.g., "Create a vesting contract").
2.  **Audit:** The AI automatically performs a security analysis.
3.  **Verification:** The finalized audit log is hashed and committed to a mock ledger for an immutable record.

-----

### ✨ Key Features

| Feature | Description | Value Proposition |
| :--- | :--- | :--- |
| **Generative Agent (Generation Mode)** | Converts natural language prompts into runnable, compliant Qubic C++ code structures, managing EFI details automatically. | **Eliminates coding expertise.** Reduces development time from hours to seconds. |
| **AIOps Security Auditing (Scanning Mode)** | Provides real-time, proactive security audits, detecting vulnerabilities like **Integer Overflow** and **Access Control**. | **Builds security in.** Catches critical flaws before deployment. |
| **Global Translation Service** | Instantly translates complex audit reports into **over 54 languages** (e.g., German, Mandarin, Hausa). | **Democratizes access.** Makes smart contract security transparent for the worldwide community. |
| **Secure Audit Trail** | Every operation generates a **Cryptographic Commitment Fingerprint** (SHA-256) logged to a mock Qubic ledger. | **Ensures Verifiability.** Provides immutable proof that the code was generated/scanned by the agent. |

-----

### 💻 Technical Stack & Architecture

Q-Gen is built on a robust, high-performance **Three-Tier Agentic Framework**:

| Layer | Technology | Role & Purpose |
| :--- | :--- | :--- |
| **Intelligence** | **Gemini 2.5 Flash-Lite** | The core generative agent used for C++ synthesis, compliance checks, and translation logic. |
| **Backend** | **FastAPI & Uvicorn (Python 3.11)** | Provides a lightning-fast ASGI API for request validation and routing, ensuring performance under load. |
| **AIOps/Security** | **Pydantic & Python Hashlib** | Pydantic ensures data input integrity, while SHA-256 hashing creates the immutable audit fingerprint. |
| **Frontend** | **HTML5 / Tailwind CSS** | Provides a simple, responsive, dual-mode user interface for seamless interaction. |

-----

### ▶️ Live Demo & Deployment

The application is deployed as a full-stack service on Render.

**Demo Application URL:**
[https://kusmus-qgen-agent.onrender.com/](https://kusmus-qgen-agent.onrender.com/)

**Demo Video:**
[Link to your submission video]

-----

### ⚙️ Getting Started (Local Setup)

To run the Q-Gen Agent locally for development, follow these steps:

#### 1\. Setup Environment

```bash
# Clone the repository
git clone [YOUR-GITHUB-REPO-LINK]
cd rurho_qubic_hackathon

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install dependencies (requires google-generativeai, fastapi, uvicorn, etc.)
pip install -r requirements.txt
```

#### 2\. Configure API Key

Create a file named **`.env`** in the root directory and add your working Gemini API key(s).

```env
GEMINI_API_KEY_1="AIzaSy...[your working key]"
# GEMINI_API_KEY_2="..."
```

*(**Note:** Ensure this file is added to your `.gitignore` to prevent exposure.)*

#### 3\. Run the Server

Launch the FastAPI backend using Uvicorn:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

#### 4\. Access the Frontend

Open your web browser and navigate to:

```
http://127.0.0.1:8000/
```

The root route will now automatically serve the `index.html` frontend.
