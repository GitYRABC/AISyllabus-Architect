# 🎓 AISyllabus-Architect

**Autonomous AI Study Planner: Generates hyper-fast, personalized, and structured study schedules from raw syllabus input.**
Live at: (https://aisyllabus-architect.onrender.com)

## ⚡ Key Features

| Feature | Description | Benefit |
| :--- | :--- | :--- |
| **Multi-Agent System** | Uses a specialized crew (Analyzer, Architect, Recommender) to break down complex planning tasks. | Ensures comprehensive and specialized outputs (e.g., resource links). |
| **High-Speed Inference** | Powered by the **Groq API** and the Llama 3 model. | Study plans are generated in seconds, not minutes. |
| **Personalized Schedules** | Generates detailed, day-by-day study sessions based on the user's total duration and preferred learning style. | Optimizes time management and academic performance. |
| **Structured Output** | Leverages explicit JSON prompting to ensure all data (subjects, schedules, resources) is reliable and machine-readable. | Seamless data flow to the web frontend and PDF report generation. |
| **PDF Report** | Generates a clean, downloadable PDF report of the complete study schedule. | Easy to print, share, or view offline. |

---

## 🚀 Getting Started

Follow these steps to set up and run the application locally.

### Prerequisites

1.  **Python 3.10+**
2.  A **Groq API Key** (Get one for free at [console.groq.com](https://console.groq.com/)).

### Installation

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/GitYRABC/AISyllabus-Architect.git](https://github.com/GitYRABC/AISyllabus-Architect.git)
    cd AISyllabus-Architect
    ```

2.  **Create and Activate Virtual Environment**
    ```bash
    python -m venv venv
    # macOS/Linux
    source venv/bin/activate
    # Windows
    .\venv\Scripts\activate
    ```

3.  **Install Dependencies**
    The core dependencies for Flask, CrewAI, and Groq are listed in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

Create a file named **`.env`** in the root directory and add your Groq API key:

```env
# Replace 'gsk_...' with your actual Groq API Key
GROQ_API_KEY=gsk_yoursuperlongsecretkeyxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PORT=5000

