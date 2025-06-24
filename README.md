# NeuroPath 🧠

An MVP AI-powered application designed to assist students preparing for IT certification exams.

## ✅ Prerequisites

- Python 3.11 or higher
- [Microsoft Azure](https://portal.azure.com/) account
- **Azure AI Foundry Resource**

---

## 🔧 Step-by-Step Setup

### 0. Create an Azure AI Foundry Resource

Before cloning and running the application, configure an Azure AI Foundry resource.

**Have Azure access?**
- ✅ Yes: Go to https://portal.azure.com/
- ⚠️ No: Go to https://my.visualstudio.com/ and request access

1. Search for "Resource Group" in Azure portal
2. Create new resource named `neuropath-project`
3. Deploy the resource
4. Click "Go to Azure AI Foundry portal"
5. Navigate to "Models + endpoints" in right sidebar
6. Deploy new base model (gpt-4o or gpt-4)
7. Copy the endpoint's **API key** and **Target URI**

---

### 1. Clone the Repository

```bash
git clone https://github.com/igorthebarros-avanade/neuropath.git
cd neuropath
```

### 2. Install Poetry

**Linux/WSL:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Windows (PowerShell):**
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

Restart your terminal and verify installation:
```bash
poetry --version
```

#### 📦 Poetry Commands Reference
- **Activate environment**: `poetry env activate`
- **Add package**: `poetry add package_name`
- **Install dependencies**: `poetry install`
- **Update dependencies**: `poetry update`
- **Show dependencies**: `poetry show`
- **Exit environment**: `exit` or `deactivate`
- **[Poetry's official documentaiton guide](https://python-poetry.org/docs/basic-usage/)**

### 3. Install Dependencies

Create virtual environment and install packages:
```bash
poetry install
```

If `pyproject.toml` doesn't exist yet, initialize Poetry and add dependencies:
```bash
poetry init
poetry add streamlit openai python-dotenv pandas pathlib tenacity tabulate # Example in-line specification of multiple modules
```

### 4. Configure Environment

Create `.env` file in project root:
```bash
cp .env.example .env  # If example exists, otherwise create manually
```

Add your Azure credentials to `.env`:
```
AZURE_OPENAI_ENDPOINT_TEXT_AUDIO_WHISPER=your_target_uri_here
AZURE_OPENAI_API_KEY_TEXT_AUDIO_WHISPER=your_api_key_here
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_TEXT=your_deployment_name
EXAM_DATA_JSON_PATH=./content/content_updated.json
```

### 5. Run the Application

Activate Poetry environment and run:
```bash
poetry env activate
poetry run python main.py
```

Alternatively, run without activating shell:
```bash
poetry run python main.py
```

---

🚀 **You're ready to go!**