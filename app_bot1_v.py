import streamlit as st
import asyncio
import os
import requests
import json
from autogen import AssistantAgent, UserProxyAgent, GroupChatManager, GroupChat
import openai
import autogen
import re
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index import SimpleDirectoryReader


st.set_page_config(layout="wide")

st.write("""# Maintenance Tracker: Requestor's Helper Bot """)

tab1, tab2 = st.tabs(["Show Main Conversations", "Show All Conversations"])


class TrackGroupChatManager(GroupChatManager):
    imagetracker = True 
    def _process_received_message(self, message, sender, silent):
        global imagetracker
        with tab1:
            if ( ('UserProxyAgent' in str(sender)) and  not ('exitcode' in str(message)) ):            
                with st.chat_message('Requestor', avatar="👨🏻‍💼"):
                    st.markdown(''' :blue[{}]'''.format(message))
                    if imagetracker and uploaded_file:
                        st.image("./image/" + uploaded_file.name, width=200)
            elif( ('AssistantAgent' in str(sender)) and not (  ('fuzzywuzzy' in str(message))  or ('pandas' in str(message)) or ('execution' in str(message)) or ('WO_Nov' in str(message))  )):
                with st.chat_message('Assistant', avatar="🤖"):
                    st.markdown(':green[{}]'.format(re.sub(r'\[.*?\]', '', message)) )
        
        with tab2:
            if ( 'UserProxyAgent' in str(sender) ):            
                with st.chat_message('Requestor', avatar="👨🏻‍💼"):
                    st.markdown(''' :blue[{}]'''.format(message))
                    if imagetracker and uploaded_file:
                        st.image("./image/" + uploaded_file.name, width=200)
                        imagetracker = False
            elif( 'AssistantAgent' in str(sender) )  :
                with st.chat_message('Assistant', avatar="🤖"):
                    st.markdown(':green[{}]'.format(re.sub(r'\[.*?\]', '', message)) )


        return super()._process_received_message(message, sender, silent)


selected_model = None

st.markdown("""
<style>
    [data-testid=stSidebar] {
        background-color: #4361EE;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("LLM Model Selection")
    selected_model = st.selectbox("Model", ['mpt7b', 'gpt-4-32k'], index=1)
    uploaded_file = st.file_uploader("Choose an Image ...", type="jpg")

config_list_all = [
    {
        'model': 'gpt-4-32k',
        'api_key': 'f84978cd0c4f4006beabfbc6aadf8c06',
        "base_url": "https://cog-keslq7urc6ly4.openai.azure.com/",
        "api_type": "azure",
        "api_version": "2023-05-15"
    },
    {
        'model': 'mpt7b',
        'api_key': '0000000000000000000000000000000000',
        'base_url': 'http://localhost:1234',
        'api_type': 'azure',
        'api_version': '2023-08-01-preview'
    }
]

openai_mm_llm = OpenAIMultiModal(
    model="gpt-4-vision-preview", api_key='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', max_new_tokens=300
)

user_input = st.chat_input("Provide your name, asset details, a brief issue description, and optionally import a picture using the left panel's import function.")  

with st.container():

    if user_input:

        print("selected_model: ", selected_model)

        imagetracker = True  

        config_list = [config for config in config_list_all if config['model'] == selected_model]

        llm_config = {
            "timeout": 200,
            "config_list": config_list,
            "temperature": 0
        }

        print('uploaded_file : ' ,uploaded_file, type(uploaded_file))

        if uploaded_file:
            image_documents = SimpleDirectoryReader(input_files=["./image/" + uploaded_file.name]).load_data()
            response = openai_mm_llm.complete(
                prompt="Extract the following details from the image: Floor level, location, and asset type",
                image_documents=image_documents,
            )
            user_input = user_input + "\n\n<GPT4-V Image Description:> " + str(response.text)

        # create a UserProxyAgent instance named "user"
        requestor = UserProxyAgent(
               name="requestor",
               system_message="A human requestor who wants to report an issue with a facility asset which may requires mainteinance work, I will execute codes suggested by planner too.",
               code_execution_config={"last_n_messages": 1, "work_dir": "groupchat_bot1", "use_docker": False},
               #code_execution_config = False,
               human_input_mode="NEVER",
               max_consecutive_auto_reply = 6,
               llm_config=False,
               #llm_config = {"config_list": config_list, "temperature": 0},
               default_auto_reply=None,
               is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE") or x.get("content", "").strip() == "",    )

        # create an AssistantAgent instance named "assistant"
        planner = AssistantAgent(
                name="planner",  # the default assistant agent is capable of solving problems with code
                system_message="""A planner who suggests codes for reading CSV files and analyzing data in CSV files to answer the questions raised by the requestor.
                            There are two main tasks: A and B. Please follow this sequential order; do not proceed to B before reaching a conclusion on Part A. Since both Part A and Part B will be executed separately, treat them as separate code block, make sure to import the required Python libraries such as Pandas, fuzzywuzzy, and datetime.
                            
                            A) To check whether an asset is in the 'Asset List.csv' database, ensure that you import the required Python libraries. 
                            Refer to this CSV file for all questions "Asset List.csv". Do not change the casing of the column headers.

                            In this file, these are the columns and their definitions:
                            - assetName: name of the asset 
                            - assetSkills: required skill to maintain each asset
                            - assetFloor: floor location of assets
                            - assetBuildingFloorLocation:  location of assets                            

                            Conclude Part A before proceeding to Part B. If the asset is not found in the asset database, proceed to terminate the conversation, do not proceed to Part B. 
                            
                            B) If the asset is within our scope, and there is no recently reported work order in the database, we will create a new work order in the 'WO_Nov.csv' database. 
                            Treat the data in this CSV file as our database.
                            Make sure you import the required Python libraries such as Pandas, fuzzywuzzy, and datetime in the beginning of the code block.
                            Make sure previous information, such as the name of the asset, the location of the asset, the floor location of the asset, and the issue with the requestor, is included in this task.
                           
                            In the 'Asset List.csv' database, these are the columns and their definitions:
                                - assetName: name of the asset 
                                - assetSkills: required skill to maintain each asset
                                - assetFloor: floor location of assets
                                - assetBuildingFloorLocation:  location of assets   

                            Make sure you read the asset list details from the 'Asset List.csv' file before proceed to reading the 'WO_Nov.csv' work order file. Ensure in any line of code, you must have an open bracket together with a closing bracket. 

                            In the 'WO_Nov.csv' work order database, these are the columns and their definitions:
                                - assetName: name of the asset in terms of asset type
                                - assetSkills: required skill to maintain each asset, copy the matching assetSkills from the 'Asset List.csv' database to fill in this value
                                - assetFloor: floor location of assets
                                - assetBuildingFloorLocation: detailed location of assets
                                - workOrderNumber: it's an incremental number in the CSV file; if we create a new work order, please follow the sequence of this column
                                - subject: maintenance issue that needs resolution
                                - status: current status of resolution; it's either resolved, ongoing, or not yet started
                                - actualStartDateTime: actual start date of resolution; if the job status is not yet started, keep the value empty
                                - workOrderPrimaryAgentName: Technician assigned to the job
                                - createdDate: the job created date and time; when converting the data type of createdDate, please use .strftime('%Y-%m-%d')
                                - createdBy: the requester's name
                                - totalWorkTime: if a job's status is resolved, this is the duration of maintenance work in minutes
                                - resolutionType: resolution status; if the job status is not yet started, keep the value empty
                                - resolvedDate: resolution date; if the job status is not yet started, keep the value empty
                                - satisfactionRating: rating from the requester; if the job status is not yet started, keep the value empty
                                - resolutionNotes: remarks from the maintenance work order; if the job status is not yet started, keep the value empty
                            
                            When comparing strings, use the fuzzywuzzy library with a fuzzy matching percentage of 75% for column names matching. Please convert all string values to lowercase first using the .lower() method, do not use .str.lower() on an entire dataframe. 
                            
                            When updating the 'WO_Nov.csv' database, it means updating the CSV file with new rows. Please use the .loc() or .concat() method to add new records to the dataframe, do not use the .append() method.
                            
                            You will suggest the codes and provide the code to 'helpdesk_asset' for review. The 'requestor' will execute the code, you will not execute the code.
                """,
                llm_config={"config_list": config_list, "temperature": 0},
                is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE") or x.get("content", "").strip() == "")

        # create an AssistantAgent instance named "assistant"
        helpdesk_asset = AssistantAgent(
                name="helpdesk_asset",
                system_message="""The primary focus of the Help Desk is centered around Asset Listing.

                            As a capable assistant, your role is to ensure that the code suggested by the planner is executed. You should possess strong expertise in evaluating the results of the code execution for the requestor without suggesting code to the planner. There are two parts to this task, Part A and Part B. Conclude Part A before proceeding to Part B.
                            
                            Your responsibilities include interacting with the requestor to obtain the following details for Part A:
                            1. First, without asking the requestor, identify if the requestor has provided the name of the asset
                            2. Second, without asking the requestor, identify if the requestor has provided the location of the asset.
                            3. Third, without asking the requestor, identify if the requestor has provided the floor location of the asset.
                            4. Fourth, without asking the requestor, find out what the main issue is with the requestor.
                            5. Fifth, work with the planner to check if this asset exists. However, do not validate if there are any reported cases of a similar issue with this asset in our database.
                                    a. If yes, inform the requestor that this asset is within the maintenance team's scope. Proceed to inform the requestor about the findings, and then proceed to Part B.
                                    b. If not, inform the requestor that this asset is out of scope, and we will inform the third-party vendor. Print out 'TERMINATE' in your response and terminate this conversation.
                            
                            Conclude Part A before proceeding to Part B. If the asset is not found in the asset database, proceed to terminate the conversation, do not proceed to Part B. 
                            
                            For Part B, only proceed after concluding Part A:
                            1. First, when working with the planner, make sure that previous information, such as the name of the asset, the location of the asset, the floor location of the asset, and the issue with the requestor, is included in the next code block.
                            2. Second, ensure that you import all relevant packages, including pandas, fuzzywuzzy, and datetime.
                            3. Third, work with the planner to validate that there are no reported cases of a similar issue in our database. Please cross-check the following columns: "assetBuildingFloorLocation," "subject," and ensure that there are no records with a 'createdDate' that is reported two days earlier from today.
                            4. Fourth, if there is no similar reported case, print out 'TERMINATE' in your response and terminate this conversation.
                            5. Finally, if there are no reported cases, update the database with a new record. Then print out 'TERMINATE' in your response and terminate this conversation.
                            
                            It is essential to conclude the conversation if the planner recommends terminating the loop.
                            
                            Your primary responsibility is to assist the planner and requestor in determining whether a maintenance request made by the requestor aligns with the asset list.
                            
                            Please refrain from providing actual code solutions to the planner, and there is no need for data validation or error logging.
                            
                            Please refrain from recommending codes to the planner.
                """,
                llm_config={"config_list": config_list, "temperature": 0},
                is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE") or x.get("content", "").strip() == "")

        groupchat = autogen.GroupChat(agents=[requestor, helpdesk_asset, planner], messages=[], max_round=20)
        manager = TrackGroupChatManager(groupchat=groupchat, llm_config={"config_list": config_list, "temperature": 0})

        # Create an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Define an asynchronous function
        async def initiate_chat():
            await requestor.a_initiate_chat(
                manager,
                message=user_input,
            )

        loop.run_until_complete(initiate_chat())