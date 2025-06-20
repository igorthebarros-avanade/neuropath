# NeuroPath 🧠

An MVP AI-powered application designed to assist students that want to apply for IT exams and get certifications.

## ✅ Prerequisites

Before getting started, make sure you have:

- Python 3.9 or higher installed
- A [Microsoft Azure](https://portal.azure.com/) account
- An **Azure AI Foundry Resource** created

---

## 🔧 Step-by-Step Setup

### 0. Create an Azure AI Foundry Resource

Before cloning the application and running it, you shall configure a Azure AI Foundry resource group.

Do you have requested access to Azure?

✅ Yes: Go to https://portal.azure.com/
⚠️ No: Go to https://my.visualstudio.com/ and request access

0. At Azure portal, search for Resource Group.

1. Create a new resource giving the name neuropath-project.

2. Deploy the resource.

3. After is deployed, you can click on the button that says "Go to Azure AI Foundry portal".

4. Once inside the Foundry portal, look at the right side bar for "Models + endpoints".

5. Deploy a new base model based on gpt-4.1.

6. After deployed, make sure to copy the endpoint's **API key** and **Target URI**.

---

### 1. Clone the Repository

git clone https://github.com/igorthebarros-avanade/neuropath.git
cd neuro-path

0. On .env file, add the previous copied data and add to AZURE_OPENAI_ENDPOINT_TEXT_AUDIO_WHISPER and AZURE_OPENAI_API_KEY_TEXT_AUDIO_WHISPER.

1. Get the path, from the git cloned project directory, that points to NeuroPath/content/content.json and add to the EXAM_DATA_JSON_PATH on .env file.

🗒️Note: At this point, you should be able to connect to Azure AI Foundry and test the application on your resource at Azure.

---

### 2. Install Dependencies with pip

Make sure `pip` is installed by running:

pip --version

Then, install all required packages:

pip install -r req.txt

📝 Note: It's recommended to use a virtual environment:

python -m venv venv
soruce venv\Scripts\activate

---

### 3. Run the application

To start the application, execute the main Python file:

python main.py

🚀 Congratulations! You are now ready to go!