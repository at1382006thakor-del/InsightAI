# 📊 InsightAI — AI Sales Dashboard & Business Intelligence Platform

InsightAI is an advanced, AI-powered Business Intelligence (BI) and sales analytics dashboard. The platform transforms raw transaction datasets into interactive visual insights, automatically flags operational risks, predicts future sales using machine learning, and compiles executive-level PDF/PPTX strategy reports. It also features an integrated AI Sales Assistant powered by Google Gemini to query your sales database in natural language.

---

## ✨ Key Features

*   **📈 Interactive Analytics Dashboard**: Deep-dive sales performance reports featuring dynamic metrics (Revenue, Profit, Order count, Discount margins) and visual charts (Timeseries trends, product categories distribution, regional comparisons) built with **Recharts**.
*   **🧹 Automated Data Cleaning**: Upload custom CSV sales tables, execute schema variable mapping, automatically handle missing or duplicate values, and score dataset quality.
*   **🔮 ML Sales Forecasting & Anomaly Detection**: Predicts next-quarter sales trends and confidence intervals using built-in Machine Learning models (XGBoost / ARIMA) and flags potential operational risks or spikes.
*   **🤖 AI Sales Assistant**: An conversational chat interface integrated with **Google Gemini** allowing you to query your sales DB using natural language and dynamically generate reports or charts right in the chat.
*   **📄 Executive Strategy Reports**: Instantly compile quarterly and monthly strategy updates into high-fidelity PDF documents (using ReportLab) and PowerPoint decks.
*   **🔒 Multi-Role Authentication**: Fully secure JWT authentication system with separate operational accesses for Executive Admins and Sales Analysts.

---

## 🛠️ Technology Stack

*   **Frontend**: Next.js 15 (App Router), TypeScript, Tailwind CSS v4, TanStack React Query, Axios, Recharts, Framer Motion.
*   **Backend**: FastAPI (Python 3.12), Uvicorn, SQLAlchemy ORM.
*   **Database**: SQLite (for local development) & PostgreSQL (for production).
*   **AI Integration**: Google Gemini API.
*   **PDF/PPTX Generators**: ReportLab & Python-pptx.

---

## 🚀 Getting Started (Local Development)

Ensure you have **Python 3.10+** and **Node.js 18+** installed on your system.

### 1. Set Up and Launch the Backend API
Navigate to the project root directory and follow these steps:

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the virtual environment:
   * **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   * **macOS / Linux**:
     ```bash
     source venv/bin/activate
     ```
3. Install the backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Start the FastAPI backend server:
   ```bash
   python backend/run.py
   ```
   * **API URL**: `http://localhost:8000`
   * **Interactive Swagger Docs**: `http://localhost:8000/docs`
   * **Automatic DB Seeding**: On the first startup, the backend automatically creates `insightai.db` (SQLite) and generates `datasets/sample_sales.csv` with 2,500 sample transactions to populate your dashboard immediately!

---

### 2. Set Up and Launch the Next.js Frontend
Open a new terminal window or tab, navigate to the `frontend` folder, and complete the following:

1. Install the required Node packages:
   ```bash
   cd frontend
   npm install
   ```
2. Start the Next.js development server:
   * **Windows (PowerShell - to bypass script execution policies)**:
     ```powershell
     npm.cmd run dev
     ```
   * **macOS / Linux / Command Prompt**:
     ```bash
     npm run dev
     ```
   * **Frontend URL**: `http://localhost:3000`

---

## 🐳 Docker Compose Deployment (Recommended)

To run the entire platform locally with a production-grade PostgreSQL database, FastAPI backend, and Next.js frontend containers, simply run:

1. **Start Services**:
   ```bash
   docker compose up --build
   ```
2. **Exposed Ports**:
   * **Frontend Dashboard**: `http://localhost:3000`
   * **Backend REST API**: `http://localhost:8000`
   * **PostgreSQL Database**: `localhost:5432`
3. **Database Auto-Seeding**: The postgres container initializes and seeds the database automatically on startup.

---

## 🔑 Workspace Access Credentials

To explore the dashboard right away, log in with one of these pre-seeded accounts:

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Executive Administrator** | `admin@insightai.com` | `admin123` | Upload/clean datasets, retrain ML models, manage users, full access. |
| **Standard Sales Analyst** | `user@insightai.com` | `user123` | View charts, run forecast, chat with AI, compile reports. |

---

## ⚙️ Environment Variables

### Backend Configuration (`backend/.env`)
Copy `backend/.env.example` to `backend/.env` (or configure these in your cloud provider):
```ini
DATABASE_URL=sqlite:///./insightai.db # Set postgresql://... for production
SECRET_KEY=your-secure-jwt-secret-key-phrase
GEMINI_API_KEY=your-google-gemini-api-key
```

### Frontend Configuration (`frontend/.env.local`)
Copy `frontend/.env.example` to `frontend/.env.local`:
```ini
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

---

## 📁 Project Directory Structure

```text
InsightAI/
├── .github/workflows/       # GitHub CI/CD build validation pipelines
├── backend/                 # FastAPI Backend Application
│   ├── app/
│   │   ├── api/            # API endpoints (Auth, Datasets, Chat, KPIs, Forecast, Reports, Settings)
│   │   ├── database/       # SQLAlchemy Connection & SQLite/Postgres seeding scripts
│   │   ├── ml/             # Forecast models training (XGBoost/ARIMA) & anomaly metrics
│   │   ├── reports/        # ReportLab PDF & PowerPoint pptx file generators
│   │   └── services/       # Google Gemini AI assistant wrapper & data cleaning scripts
│   ├── Dockerfile          # Backend Docker build specs
│   ├── requirements.txt    # Python dependencies
│   └── run.py              # Backend entrypoint launcher
│
├── datasets/                # Storage for default transaction sales CSV datasets
├── frontend/                # Next.js 15 Frontend Client
│   ├── src/
│   │   ├── app/            # App Router pages (Dashboard, Upload, Reports, Chat, Forecast, Admin)
│   │   ├── components/     # UI components (collapsible SideNav, Navbar, LayoutFrame)
│   │   ├── context/        # React context (AuthGuard, API Context wrappers)
│   │   └── services/       # Axios API client definition
│   ├── Dockerfile          # Frontend production stage Docker specs
│   └── package.json        # Frontend package manifest
│
├── docker-compose.yml       # Production environment Docker Compose runner
├── .gitignore               # Excludes virtual environments, SQLite DBs, Next builds, and keys
└── README.md                # Project documentation (This file)
```
