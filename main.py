from dotenv import load_dotenv
import streamlit as st
import time
from PyPDF2 import PdfReader
from streamlit_extras.add_vertical_space import add_vertical_space
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from langchain.callbacks import get_openai_callback
from helper_functions.utility import check_password  

# Check if the password is correct.  
if not check_password():  
    st.stop()
    
# Sidebar contents
with st.sidebar:
    st.title("I am your WSH Regulations Info Retriever Assistant.")
    
    st.markdown("""

Step 1) Upload the relevant document for WSH Regulations that you wish to evaluate. 
Step 2) Type in the applicant's response at the right and I can help to assess if the responses are correct.

""")

st.expander("""
IMPORTANT NOTICE: This web application is a prototype developed for educational purposes only. The information provided here is NOT intended for real-world usage and should not be relied upon for making any decisions, especially those related to financial, legal, or healthcare matters.

Furthermore, please be aware that the LLM may generate inaccurate or incorrect information. You assume full responsibility for how you use any generated output.

Always consult with qualified professionals for accurate and personalized advice.

""")

def main():
    load_dotenv()

    #Main Content
    st.header("Use Case 1: Assistant for Workplace Safety and Health Officer (WSHO) Applicants")

    # upload file
    pdf = st.file_uploader("Upload the document for WSH regulations and input the applicants' responses.", type="pdf")
    
    # extract the text
    if pdf is not None:
      pdf_reader = PdfReader(pdf)
      text = ""
      for page in pdf_reader.pages:
        text += page.extract_text()
        
      # split into chunks
      text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
      )
      chunks = text_splitter.split_text(text)
      
      # create embeddings
      embeddings = OpenAIEmbeddings()
      knowledge_base = FAISS.from_texts(chunks, embeddings)
      
      # show user input
      with st.chat_message("user"):
        st.write("Document uploaded successfuly!")
      user_question = st.text_input("Please ask a question below:")
      if user_question:
        docs = knowledge_base.similarity_search(user_question)
        
        llm = OpenAI()
        chain = load_qa_chain(llm, chain_type="stuff")
        with get_openai_callback() as cb:
          response = chain.run(input_documents=docs, question=user_question)
          print(cb)
           
        st.write(response)

if __name__ == '__main__':
    main()

# Disclaimer section explaining that the app is for educational purposes only
# Uses an expander so users can expand/collapse the disclaimer
with st.expander("Disclaimer"):
    # Display the disclaimer text within a markdown block
    st.markdown(f"""
        **IMPORTANT NOTICE:** This web application is a prototype developed for educational purposes only. The information provided here is NOT intended for real-world usage and should not be relied upon for making any decisions, especially those related to financial, legal, or healthcare matters.
        
        Furthermore, please be aware that the LLM may generate inaccurate or incorrect information. You assume full responsibility for how you use any generated output.

        Always consult with qualified professionals for accurate and personalized advice.
    """)