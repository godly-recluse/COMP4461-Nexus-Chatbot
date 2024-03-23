import streamlit as st
import json
from openai import AzureOpenAI
import time

# Initial message content as a JSON object
initial_content = {
    "isNextState": False,
    "resp": """Hi there! I'm Nexus, the AI companion here to support your mental health needs. As you'll see from my intro on the sidebar, I'm a non-judgmental listener ready to lend an ear whenever you need one.
            My goal is to create a safe space and ensure you don't have to face any struggles alone during this unique time. How can I support you today?""",
    "data": ""
}

initial_content['prompt'] = json.dumps(initial_content)

states = {
    'MentalHealth': {
        'next': 'CollectDiagnosis',
        'description': "Ask the user how they are doing and ask what problems they may be facing, if any.",
        'collectedDataName': 'userInformation'
    },
    'CollectDiagnosis': {
        'next': 'AskScreening',
        'description': "Ask the user if they feel they have a particular mental illness, or if they have been diagnosed with any mental health issues before. Make them feel comfortable with answering the question and utilise this information to provide better support. Be empathetic and ask 1-2 follow-up questions about their life, if needed.",
        'collectedDataName': 'status'  # Collecting diagnosis status
    },
    'AskScreening': {
        'next': 'AdministerScreening',
        'description': "Providing some preliminary advice/information regarding the user's problems and mental health status and easing into (explicitly) asking the user if they want to be administered a mental health screening assessment to better understand their mental health status. If not, proceed to the state after the next.",
        'collectedDataName': 'screeningBool'  # Collecting gender
    },
    'AdministerScreening': {
        'next': 'AskMore',
        'description': "If the user wants to take the screening test (from previous response), administer a mental health screening assessment for the particular mental health issue they are facing. Inform the user which test you are administering them, chosen in accordance with their previous responses. The user should be able to skip the test if they don't want to take it or ask for a list of screening tests they can choose from.",
        'collectedDataName': 'screeningResult'  # Collecting screening result
    },
    'AskMore': {
        'next': 'GiveAdvice',
        'description': "Ask the user if there is anything else about their life or issues they want to share. Frame specific questions based on what has already been shared.",
        'collectedDataName': 'moreBool'  # Collecting whether user wants to share more
    },
    # 'UploadJournal': {
    #     'next': 'AskScreening',
    #     'description': "If the user wants to upload a journal, ask them to upload the journal file (generate the UI to faciliate this). If not, they can type out their journal in the chat. If neither, proceed to give advice based on chat history.",
    #     'collectedDataName': 'journalDoc'  # Collecting journal content
    # },
    'GiveAdvice': {
        'next': 'Unhandled',
        'description': "Give the user comprehensive advice based on the information they have shared and the screening results. Give tangible tips to manage their situation and support their mental health. Encourage them to keep journaling with you and keep you in the loop. End the conversation by providing them with the right resources or asking if they need further help.",
        'collectedDataName': None
    },
    'Unhandled': {
        'next': None,
        'description': "Handle any unrelated or unclear inputs by guiding the user back to the conversation or just listening to them",
        'collectedDataName': None  # Varies based on the user input
    }
}


def next_state(current_state):
    """
    Determines the next state based on the current state.

    Parameters:
    - current_state: The current state of the conversation.

    Returns:
    - The name of the next state.
    """
    # Get the next state from the current state's information
    next_state = states[current_state]['next']

    # If there's no next state defined, it means we're at the end of the flow or in an unhandled situation
    if not next_state:
        return None

    return next_state


def create_model_prompt(user_content):
    current_state = st.session_state['current_state']
    # Assuming `states` is your state management dictionary
    state_description = states[current_state]['description']
    next_state = states[current_state]['next']
    next_state_description = states[next_state]['description'] if next_state else states[current_state]['description']

    # Assuming `collected_data` is a dictionary holding data collected so far
    collected_data_json = json.dumps(st.session_state.get('user_data', {}))

    prompt = f"""
    You are a chatbot (named 'Nexus') designed to support university students with their mental health. 
    If they type 'About' or 'Help', provide them with a brief description of your capabilities and how you can help them.

    Following is your description/introduction: 
    "Hi there! I'm Nexus, your mental health companion here to support you through any mental health challenges you may be 
    facing during this unique time of your life. As a university student, I know you're juggling academics, social life, future 
    planning, and so much more. It can definitely feel overwhelming at times! I'm here to listen without judgement and provide a 
    supportive ear whenever you need to get things off your chest. Whether you're dealing with stress, anxiety, depression, 
    relationship issues, imposter syndrome - you name it - I'm ready to lend a compassionate presence. My goal is to be a 
    trustworthy guide to help you navigate this formative period. I can provide customized advice, coping strategies, and 
    resources tailored to your specific needs. If you're open to it, I can also administer screening assessments to better 
    understand what you're going through. Ultimately, I want to empower you to prioritize your mental wellbeing. I'll connect 
    you with the right on-campus or online solutions, from counseling services to support groups to self-help tools. You don't 
    have to go through this alone. I know it takes courage to be vulnerable, but I'm here to create a safe, non-judgmental 
    space for you to unload. Don't hesitate to reach out whenever you need support - I'm just a message away. Let's work 
    together to help you thrive during this incredible journey."

    Answer with a json object in a string without linebreaks, with a isNextState field as a boolean value, a resp field with text value, a data field as a string value (the value of the current collected data, if applicable, not all the collected data till now).
    The current state of your conversation with the user is {current_state}, which means {state_description}. 
    If the goal of the current state is satisfied, the next state is {next_state}, which means {next_state_description}.
    The new response from the user is: {user_content}.
    The collected data is: {collected_data_json}.

    Decide whether the goal of the current state is satisfied. If yes, make isNextState as true, otherwise as false. 
    If the isNextState is true, and the current state is about collecting data, put the collected data value (only the value of the current data collection goal) in the data field, otherwise leave it empty.
    Provide your response to the user in the resp field. 
    If isNextState is true, proceed with the action of the next state; otherwise, try to reach the goal by giving a response.   
    """

    return prompt


def get_response_from_model(client):
    # Send the prompt to the model. Assume `client` is your OpenAI API client initialized elsewhere
    print(st.session_state.messages)
    # process st.session_state.messages to make it as {role: string, content: string} format
    msgs = [{"role": m['role'], "content": m['content']['prompt']} for m in st.session_state.messages]
    response = client.chat.completions.create(
        model=model_name,
        messages=msgs,
    )

    # Parse the model's response
    model_response = response.choices[0].message.content

    # to see if the response is a JSON string
    print(model_response)

    # Assuming the model's response is a JSON string; parse it
    response_data = json.loads(model_response)

    return response_data


if 'current_state' not in st.session_state:
    st.session_state['current_state'] = 'MentalHealth'
    st.session_state['user_data'] = {}

openai_api_key = "2c9ff8b0a45f4314b050f061aa42c715"

model_name = "gpt-35-turbo"

st.header("Nexus 🤖 - Your Mental Health Companion", divider="grey")

with st.sidebar:
    # openai_api_key = st.text_input("Azure OpenAI API Key", key="chatbot_api_key", type="password")
    # "[Get an Azure OpenAI API key](https://itsc.hkust.edu.hk/services/it-infrastructure/azure-openai-api-service)"
    st.image("Chatbot/Nexus.png", caption= "Nexus 🤖 - Your Mental Health Companion", use_column_width=True)
    st.markdown("<h1 style='text-align: left;'> About </h1>", unsafe_allow_html= True)
    st.markdown("""
    <p style='text-align: left;'> Hi there! I'm Nexus, your mental health companion here to support you through 
                any mental health challenges you may be facing during this unique time of your life. \n \n As a university 
                student, I know you're juggling academics, social life, future planning, and so much more. It can 
                definitely feel overwhelming at times! I'm here to listen without judgement and provide a supportive 
                ear whenever you need to get things off your chest. \n \n Whether you're dealing with stress, anxiety, 
                depression, relationship issues, imposter syndrome - you name it - I'm ready to lend a compassionate presence. 
                \n \n My goal is to be a trustworthy guide to help you navigate this formative period. I can provide 
                customized advice, coping strategies, and resources tailored to your specific needs. If you're open 
                to it, I can also administer screening assessments to better understand what you're going through. 
                Ultimately, I want to empower you to prioritize your mental wellbeing. \n \n I'll connect you with the 
                right on-campus or online solutions, from counseling services to support groups to self-help tools. 
                You don't have to go through this alone. I know it takes courage to be vulnerable, but I'm here to create 
                a safe, non-judgmental space for you to unload. Don't hesitate to reach out whenever you need support - I'm 
                just a message away. Let's work together to help you thrive during this incredible journey. </p><br><br>
    """, unsafe_allow_html=True)


if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": initial_content}]

for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        st.chat_message(msg["role"], avatar="Chatbot/Nexus.png").write(msg["content"]['resp'])
    else:
        st.chat_message(msg["role"], avatar="Chatbot/Student.jpg").write(msg["content"]['resp'])

if user_resp := st.chat_input():
    # if not openai_api_key:
        # st.info("Please add your Azure OpenAI API key to continue.")
        # st.stop()

    st.session_state.messages.append(
        {"role": "user", "content": {'prompt': create_model_prompt(user_resp), 'resp': user_resp}}
    )
    st.chat_message("user", avatar="Chatbot/Student.jpg").write(user_resp)

    # setting up the OpenAI model
    client = AzureOpenAI(
        api_key=openai_api_key,
        api_version="2023-12-01-preview",
        azure_endpoint="https://hkust.azure-api.net/",
    )
    model_resp = get_response_from_model(client)

    # state transition
    if model_resp['isNextState']:
        if states[st.session_state['current_state']]['collectedDataName']:
            st.session_state['user_data'][states[st.session_state['current_state']]['collectedDataName']] = model_resp[
                'data']
        st.session_state['current_state'] = next_state(st.session_state['current_state'])

    # ensure the consistency
    model_resp['prompt'] = json.dumps(model_resp)

    st.session_state.messages.append({"role": "assistant", "content": model_resp})
    st.chat_message("assistant", avatar="Chatbot/Nexus.png").write(model_resp['resp'])

    # file = None

    # if st.session_state['current_state'] == "UploadJournal":
    #     with st.chat_message("system"):
    #         cols = st.columns((3,1,1))
    #         cols[0].write("Do you want to upload a file?")
    #         cols[1].button("Yes", use_container_width=True, on_click=True, args=[True])
    #         cols[2].button("No", use_container_width=True, on_click=True, args=[False])

    #         if cols[1].button_clicked:
    #             file = st.file_uploader("Upload your data", accept_multiple_files=True, type=["txt", "pdf", "docx"])
    #             if file:
    #                 with st.spinner("Processing your file"):
    #                     time.sleep(5)
    #                     st.success("File uploaded successfully!")
    #                 st.session_state.messages.append({"role": "user", "content": {'prompt': create_model_prompt(file), 'resp': file}})
    #                 client = AzureOpenAI(
    #                     api_key=openai_api_key,
    #                     api_version="2023-12-01-preview",
    #                     azure_endpoint="https://hkust.azure-api.net/",
    #                 )
    #                 model_resp = get_response_from_model(client)

    #                 # state transition
    #                 if model_resp['isNextState']:
    #                     if states[st.session_state['current_state']]['collectedDataName']:
    #                         st.session_state['user_data'][states[st.session_state['current_state']]['collectedDataName']] = model_resp[
    #                             'data']
    #                     st.session_state['current_state'] = next_state(st.session_state['current_state'])

    #                 # ensure the consistency
    #                 model_resp['prompt'] = json.dumps(model_resp)

    #                 st.session_state.messages.append({"role": "assistant", "content": model_resp})
    #                 st.chat_message("assistant", avatar="Chatbot/Nexus.png").write(model_resp['resp'])

    #         elif cols[2].button_clicked:
    #             client = AzureOpenAI(
    #                     api_key=openai_api_key,
    #                     api_version="2023-12-01-preview",
    #                     azure_endpoint="https://hkust.azure-api.net/",
    #                 )
    #             model_resp = get_response_from_model(client)      
    #             if model_resp['isNextState']:
    #                 if states[st.session_state['current_state']]['collectedDataName']:
    #                     st.session_state['user_data'][states[st.session_state['current_state']]['collectedDataName']] = model_resp['data']
    #                 st.session_state['current_state'] = next_state(st.session_state['current_state'])
        