# facility_maintenance_chatbots_bot1
Maintenance Tracker: Requestor's Helper Bot

### To run this app locally:
1. Clone this repository
- Create a virtual environment: python -m venv venv
- Activate the virtual environment: . venv/bin/activate
- Install requirements: pip install -r requirements.txt

2. Sign up for an OpenAI API key, Azure OpenAI API key and Databricks LLM serving token
- Paste them into the codes blocks below (In app_bot1_v.py and flask_llm_mpt.py)
- Feel free to tweak the OpenAI model and parameters in app_bot1_v.py to experiment with different conversational AI engines.
- In app_bot2_v.py
~~~~
{
    'model': 'gpt-4-32k',
    'api_key': '',
    "base_url": "",
    "api_type": "azure",
    "api_version": "2023-05-15"
}
~~~~
~~~~
openai_mm_llm = OpenAIMultiModal(
    model="gpt-4-vision-preview", api_key='', max_new_tokens=300
)
~~~~

- In flask_llm_mpt.py
~~~~
API_BASE = ""
ENDPOINT = ""
~~~~

4. The Main Script: app_bot1_v.py.
- Run the app: streamlit run app_bot1_v.py
- The app should now be running on http://localhost:8501

5. At the same time, run the databricks LLM proxy server (flask) api locally or in a server: python flask_llm_mpt.py

6. Image file imported by user will be saved in the 'image' folder

