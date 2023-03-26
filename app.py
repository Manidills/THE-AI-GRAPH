import streamlit as st
from revChatGPT.V3 import Chatbot
import pandas as pd
import string
import re
from utils.the_graph import post_query, parse_results
from utils.prompts import protocol_selection_prompt, query_prompt
from utils.urls import URLS
from utils.schemas import SCHEMAS

IMAGE = "https://media.tenor.com/Rooi8rhW1CkAAAAi/web3-crypto.gif"

st.set_page_config(layout="wide")
access_token = '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'



if 'protocol' not in st.session_state:
    st.session_state.protocol = ''

if 'query' not in st.session_state:
    st.session_state.query = ''

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

if 'df_exists' not in st.session_state:
    st.session_state.df_exists = False

def reset_data():
    st.session_state.protocol = ''
    st.session_state.query = ''
    st.session_state.df = pd.DataFrame()
    st.session_state.df_exists = False

a, b = st.columns([1,9])
a.image(IMAGE, width=110)
b.title("THE AI GRAPH\nEasy accessable by anyone without graphql queries, Here it support :red[AAVE], :blue[DECENTRALAND], :red[BALANCER] and :blue[UNISWAP] requests")

st.markdown('##')

@st.experimental_memo
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')

col1, col2 = st.columns([4,6])
with col2:
    examples = st.radio("Examples:", [
        'show me the latest 50 balancer sales.',
        'show me the latest 50 flashloans on aave.',
        'show the price of the 10 latest sales on decentraland.',
        'Try out custom sentences'
    ], index=3)

    if examples ==  'I want to write myself':
        input_example = ""
    else:
        input_example = examples
with col1:
    with st.form(key='query_form'):
        user_input = st.text_input("What do you want?", input_example)
        submit_button_1 = st.form_submit_button(
            label='Submit',
            on_click=reset_data
        )

if st.session_state.df_exists or (user_input and submit_button_1):
    chatbot = Chatbot(api_key=st.secrets["api"])
    if not st.session_state.protocol:
        with st.spinner(text='Detecting the protocol...'):
            protocol = list(chatbot.ask(
                protocol_selection_prompt%(user_input)
            ))
            st.info(''.join(protocol))

        # # for char in string.punctuation:
        # #     protocol = protocol.replace(char, '')
        #re.sub('[^A-Za-z0-9]+', '', string)

        protocol = ''.join(filter(str.isalnum, protocol)).lower()
        st.session_state.protocol = protocol

    schema = SCHEMAS[st.session_state.protocol]

    chatbot = Chatbot(api_key= st.secrets["api"])
    if not st.session_state.query:
        with st.spinner(text='Writing the query...'):
            query = chatbot.ask(
                query_prompt%(st.session_state.protocol, user_input, schema)
            )
            st.info(query)

        st.session_state.query = query[query.find('{'): query.rfind('}') + 1]
    with st.expander(':scroll: Query'):
        st.text(st.session_state.query)

    if not st.session_state.df_exists:
        with st.spinner(text='Sending the request...'):
            results = post_query(
                URLS[st.session_state.protocol],
                st.session_state.query
                )
            if 'data' in results:
                for key, value in results['data'].items():
                    st.session_state.df = pd.DataFrame(parse_results(value))
                st.session_state.df_exists = True
            else:
                st.text(results)

    with st.expander(':scroll: Dataframe', expanded=True):
        st.dataframe(st.session_state.df)
        data = convert_df(st.session_state.df)
        st.download_button(
        "Press to Download",
        data,
        "file.csv",
        "text/csv",
        key='download-csv'
        )

    st.markdown('#')
    with st.form(key='chart_form'):
        a, b, c = st.columns([4, 5, 5])
        chart_types = ['Line chart', 'Bar chart']
        chart_type = a.radio('Select one of the following chart types:', chart_types)
        columns = b.multiselect('Select the columns for your plot:', st.session_state.df.columns)
        submit_button_2 = st.form_submit_button(label='Submit')

    st.markdown('#')

    if submit_button_2:
        if columns[0].lower() == 'timestamp':
            st.session_state.df[columns[0]] = pd.to_datetime(st.session_state.df[columns[0]], unit='s')
        display_df = st.session_state.df.set_index(columns[0])
        display_df = display_df[columns[1:]]
        for col in display_df.columns:
            display_df[col] = display_df[col].astype(float)
        if chart_type == 'Line chart':
            st.line_chart(display_df)

        if chart_type == 'Bar chart':
            st.bar_chart(display_df)
