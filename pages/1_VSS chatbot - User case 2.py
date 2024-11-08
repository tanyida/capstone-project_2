import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.document_loaders import PyPDFLoader

# Set up Streamlit page
st.set_page_config(page_title="VSS FAQ Chatbot", page_icon="📄")
st.title("Use Case 2: 📹👀 Video Surveillance System (VSS) FAQ Chatbot 🏗🚧")

# Load document from backend
pdf_path = 'https://www.mom.gov.sg/-/media/mom/documents/safety-health/faqs-for-vss.pdf'  # Update with the actual file path
loader = PyPDFLoader(pdf_path)
pages = loader.load_and_split()

st.markdown("""
            
## Do you require Video Surveillance System in your Construction Workplace?
            
From 1 June 2024, all construction worksites with a contract value of $5 million and above are required to install VSS.
            
### What is VSS?
The VSS is a network of cameras, monitors or display units, and recorders used for:
- Surveillance
- Identification of workplace safety and health (WSH) risks
- Facilitation of incident investigation and corrective actions
- Deterrence of unsafe workplace behaviours
            
### Am I required to install VSS in my construction worksite?
VSS is required at construction worksites with a contract value of $5 million and above.

### Still unsure or have further questions on the locations and specifications of the VSS? Type in your questions in the chatbot below!

""")


# Displaying PDF processing message
with st.spinner("Processing the document..."):
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(pages)

    # Set up embeddings and FAISS index
    embeddings = OpenAIEmbeddings()
    faiss_index = FAISS.from_documents(docs, embeddings)
    retriever = faiss_index.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    # Set up OpenAI LLM with RetrievalQA
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )

st.success("Document processing complete! You may now ask questions.")

# User query input
query = st.text_input("Ask a question about the VSS requirements:")

if query:
    # Retrieve and generate answer
    with st.spinner("Generating response..."):
        result = qa_chain({"query": query})
        answer = result["result"]
        sources = result["source_documents"]

        # Display answer
        st.write("### Answer:")
        st.write(answer)

        # Display sources
        st.write("### Sources:")
        for source in sources:
            st.write(f"- Page: {source.metadata['page']}")
