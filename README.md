# NeuroPath 🧠

An MVP AI-powered application designed to assist students preparing for IT certification exams.

## ✅ Prerequisites

- Python 3.11 or higher
- [Microsoft Azure](https://portal.azure.com/) account
- **Azure AI Foundry Resource**

---

## 🔧 Step-by-Step Setup

### 0. Install Python 3.11+

**Check current version:**
```bash
python --version
```

**If Python < 3.11, install:**

**Windows:**
Download from [python.org/downloads](https://www.python.org/downloads/) (select version 3.11 or higher)

**Linux/WSL:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv
```

**macOS:**
```bash
brew install python@3.11
```

### 1. Create an Azure AI Foundry Resource

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

### 2. Clone the Repository

```bash
git clone https://github.com/igorthebarros-avanade/neuropath.git
cd neuropath
```

### 3. Install Poetry

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

If necessary, include poetry to path with:
```bash
$env:Path += ";$env:APPDATA\Python\Scripts"
```

### 4. Install Dependencies

```bash
poetry install
```

If `pyproject.toml` doesn't exist, initialize Poetry:
```bash
poetry init
poetry add streamlit openai python-dotenv pandas tenacity tabulate
```

If it does, then simply load it:
```bash
poetry env activate # Will automatically use more up to date version of packages
```

### 5. Configure Environment

Create `.env` file in project root:
```bash
cp .env.example .env  # If example exists, otherwise create manually
```

Add your Azure credentials to `.env`:
```env
AZURE_OPENAI_ENDPOINT_TEXT_AUDIO_WHISPER=your_target_uri_here
AZURE_OPENAI_API_KEY_TEXT_AUDIO_WHISPER=your_api_key_here
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_TEXT=your_deployment_name
EXAM_DATA_JSON_PATH=./content/content_updated.json
```

### 6. Run the Application

**CLI Interface:**
```bash
poetry shell
```

On windows, if "poetry shell" doesn't work, try finding the env file location with "poetry env info --path":
```bash
& "$(poetry env info --path)\Scripts\activate.ps1"
```

```bash
python main.py
```

**Streamlit Interface:**
```bash
poetry shell
streamlit run app.py
```

**Or run without activating shell:**
```bash
poetry run python main.py
poetry run streamlit run app.py
```

---

## 📦 Poetry Commands Reference

- **Activate environment**: `poetry env activate`
- **Add package**: `poetry add package_name`
- **Install dependencies**: `poetry install`
- **Update dependencies**: `poetry update`
- **Show dependencies**: `poetry show`
- **Exit environment**: `exit`

📖 [Poetry Documentation](https://python-poetry.org/docs/basic-usage/)

🚀 **You're ready to go!**
