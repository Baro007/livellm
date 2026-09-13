# Contributing to LiveLLM

Thank you for your interest in contributing to **LiveLLM**! We are building an open-source, community-driven, $0-cost public observatory for large language models.

---

## How You Can Contribute

1. **Add New Models:**
   - Modify `livellm/benchmarks/datasets.py` or register a new provider gateway in `livellm/core/open_providers.py`.
   - Any zero-cost free-tier endpoint (`:free`, Groq, Google AI Studio, GitHub Models) is especially welcome!

2. **Contribute Uncontaminated Benchmark Tasks:**
   - **Tier 1 (Pulse Tasks):** Lightweight JSON/arithmetic prompts testing strict negative constraints.
   - **Tier 2 (Reasoning Tasks):** Competition-level math problems with `\boxed{...}` ground truths parseable by **SymPy**, or Python algorithms with isolated assertions.

3. **Report a Suspected Nerf Incident:**
   - Open a [Nerf Incident Report](https://github.com/Baro007/livellm/issues/new?template=nerf_incident_report.md) with exact prompts, model versions, timestamps, and observed regressions.

4. **Run a Citizen Telemetry Probe Node:**
   - Open the web dashboard at `http://localhost:8000` and enable the **"Dağıtık Topluluk Gözlemcisi (Citizen Telemetry)"** toggle. Your browser will contribute real ISP latency measurements from your region at zero cost.

---

## Development Workflow

### 1. Clone & Setup
```bash
git clone https://github.com/Baro007/livellm.git
cd livellm
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Tests
Ensure all 15+ automated tests pass:
```bash
pytest -v tests/
```

### 3. Launch Development Server
```bash
./run.sh
```

### 4. Pull Requests
- Keep PRs focused and atomic.
- Follow conventional commits (`feat:`, `fix:`, `docs:`, `test:`).
- Always include automated test cases for new evaluators or providers.
