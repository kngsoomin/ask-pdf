# Streamlit
import streamlit as st

# InquireGPT
from ask_pdf import InquirePDF

def main():

    # Initialize session state
    api = InquirePDF()
    st.session_state['InquireGPT'] = api

    if 'API_KEY' not in st.session_state:
        st.session_state['API_KEY'] = ''
    if 'file_uploaded' not in st.session_state:
        st.session_state['file_uploaded'] = False
    if 'trained' not in st.session_state:
        st.session_state['trained'] = False
    if 'api' not in st.session_state:
        st.session_state['api'] = False

    # Page config
    st.set_page_config(
        page_title='AskPDF',
        layout='wide'
    )

    st.title('AskPDF :fire:')

    # Create sidebar
    with st.sidebar:
        openai_api_key = st.text_input(
            label='OPENAI API KEY',
            value='',
            placeholder='Enter Your API Key',
            type='password'
        )

        if openai_api_key:
            st.session_state['API_KEY'] = openai_api_key
    
    st.header('Ask & Receive: GPT-Powered PDF Inquiry Assistant', 
              divider='rainbow')
    
    st.markdown('###') # padding

    # Step 1
    st.markdown(':game_die: **Step 1:** Provide your API Key on the sidebar')

    st.markdown('###') # padding

    # Step 2
    st.markdown(':mag: **Step 2:** Upload PDF file')
    uploaded_pdf = st.file_uploader(label="Click 'Browse Files' to upload PDF file", 
                                    type='pdf', 
                                    accept_multiple_files=True,
                                    label_visibility='visible')
    if uploaded_pdf:
        st.session_state['file_uploaded'] = True
    else:
        # clear session state
        st.session_state['file_uploaded'] = False
        st.session_state['trained'] = False
    
    st.markdown('###') # padding

    # Step 3
    st.markdown(':electric_plug: **Step 3:** Train the model with your PDF file')

    if st.session_state.trained:
        st.session_state.train_button_disabled = True
        st.session_state.train_button_text = 'Trained'
    else:
        st.session_state.train_button_disabled = False
        st.session_state.train_button_text = 'Train'

    train_button = st.button(st.session_state.train_button_text, 
                             disabled=st.session_state.train_button_disabled, 
                             type='primary')
    if train_button:
        if not st.session_state.file_uploaded:
            st.write(':red[Please upload a PDF file first]')
        
        elif not st.session_state.API_KEY:
            st.write(':red[Please enter your API key first]')

        elif not st.session_state.trained:
            api.open_ai_api_key = st.session_state.API_KEY
            
            with st.spinner('Uploading in progress. Please wait..'):
                api.pdfs = uploaded_pdf

                try:
                    api.process_pdf()

                except ValueError as e:
                    st.session_state['API_KEY'] = ''
                    message = f':red[{str(e)}]'
                    
                except Exception as e:
                    st.error(str(e))
                    message = f':red[{str(e)}]'

                else:
                    st.session_state['api'] = api
                    st.session_state['trained'] = True
                    message = ':green[Training completed]'
            
            st.write(message)

        else:
            pass

    st.markdown('###') # padding

    st.markdown(':speech_balloon: **Step 4:** Ask your question')

    prompt = st.text_area(label='Answers will be generated based on the provided PDF.',
                          value='What is Professional Skepticism in auditing?',
                          placeholder='What is Professional Skepticism in auditing?',
                          max_chars=300)

    if st.button('Ask Question', type='primary'):

        if not prompt:
            st.error('Please enter your question.')

        if ('API_KEY' in st.session_state) & (st.session_state['trained']):
            api = st.session_state.api
            response, source_pages = api.answer_question(prompt=prompt)

            with st.container():
                st.write(response)
                
                page_dict = dict()
                for filename, page in source_pages:
                    page_dict.setdefault(filename, []).append(page)

                temp = [f"{filename} (page {', '.join([str(page) for page in pages])})" 
                        for filename, pages 
                        in page_dict.items()]
                
                source_page_info = f"Sources: {', '.join(temp)}"
                st.write(source_page_info)
        else:
            st.error('Please ensure that you have provided an API key, uploaded a PDF file and trained the model.')


if __name__=='__main__':
    
    main()
    