# 🏥 MediQuery AI — Natural Language to SQL for Healthcare Data

> **Portfolio Project** by Rinkesh Patel  
> Demonstrates LLM integration, SQL generation, healthcare domain knowledge, and Streamlit deployment

---

## What It Does

MediQuery AI lets anyone ask questions about a healthcare database in plain English.
The app uses Claude (Anthropic's LLM) to convert the question into SQL, runs it against
a realistic simulated Ontario patient database, and returns results with an AI-generated
clinical insight.

**Example queries:**
- *"Which patients over 65 have both diabetes and abnormal kidney function?"*
- *"What is the average age of patients with Heart Failure by gender?"*
- *"Which doctor has prescribed Metformin the most?"*

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Anthropic Claude (claude-sonnet) |
| Backend | Python, SQLite |
| Frontend | Streamlit |
| Data | 200 simulated Ontario patients, 5 tables |

---

## Database Schema

```
patients       — demographics, insurance, city
diagnoses      — ICD codes, conditions, severity
medications    — drugs, dosage, prescribing doctor
lab_results    — test values, reference ranges, status
appointments   — department, doctor, type, status
```

---

## Setup & Run

```bash
# 1. Clone repo
git clone https://github.com/YOUR_USERNAME/mediquery-ai
cd mediquery-ai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

Enter your [Anthropic API key](https://console.anthropic.com/) in the sidebar when prompted.

---

## Key Features

- **Zero-shot NL→SQL** using Claude with schema-aware prompting
- **Simulated realistic data** — 200 Ontario patients, 5 related tables
- **AI-generated clinical insights** for every result set
- **CSV export** of query results
- **One-click example queries** to explore the system


## Skills Demonstrated

`LLM Integration` `Prompt Engineering` `SQL` `Python` `Streamlit` `Healthcare Domain` `API Development` `Data Modeling`
