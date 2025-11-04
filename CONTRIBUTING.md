# 🤝 Contributing to gibr

Thanks for your interest in improving `gibr`!  
We welcome all kinds of contributions — from bug fixes and documentation to new feature implementations.

---

## 🧰 Getting Started

1. **Fork** the repository
1. **Clone** your fork:
   ```bash
   git clone https://github.com/<your-username>/gibr.git
   cd gibr
1.  **Set up your environment**
    ```bash
    uv venv
    source .venv/bin/activate  
    # or on Windows
    source .venv\Scripts\activate 
    uv pip install -e ".[dev,github,gitlab,jira,azure]"
    ````
1. **Run tests**
    ```bash
    pytest
    ```
## 🧪 Code Style & Guidelines
- Use `ruff` for linting and formatting:
    ```bash
    ruff check .
    ruff format .
    ```
- All new features should include unit tests (pytest).
- Keep CLI behavior consistent and user-friendly.
- Follow existing patterns for tracker integration (see github.py, jira.py).
