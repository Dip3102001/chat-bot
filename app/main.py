from flask import Flask, request, jsonify
import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader, JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

app = Flask(__name__)

# Initialize the RAG system
def initialize_rag_system(api_key):
    os.environ["GOOGLE_API_KEY"] = api_key
    
    # Load documents
    loader = DirectoryLoader(
        path="./data",  # Change this to your data directory
        glob="*.txt",
        loader_cls=TextLoader
    )
    
    json_loader = JSONLoader(
        file_path="./data/experience.json",  # Change this to your JSON file path
        jq_schema='.[]',
        content_key="message"
    )
    
    documents = loader.load()
    
    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=5000,
        chunk_overlap=100
    )
    splits = text_splitter.split_documents(documents)
    
    # Create embeddings and vector store
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=os.environ["GOOGLE_API_KEY"],
        temperature=0.2
    )
    
    # Create prompt template
    template = """
    You are an AI assistant designed to answer recruiter questions based on Dip's background.
    
    Use only the provided context to generate responses. If direct information is unavailable, infer relevant details logically.
    Be concise, professional, and respectful, ensuring responses highlight Dip's strengths relevant to the question.
    Maintaining clarity and specificity.
    Use third-person pronouns when referring to Dip.
    For moral or opinion-based questions, identify positive aspects from the context and present an encouraging response.
    
    Context: {context}
    Recruiter's Question: {question}
    
    Response:
    """
    prompt = ChatPromptTemplate.from_template(template)
    
    # Helper function for formatting documents
    def format_docs(docs):
        return "\n\n".join([doc.page_content for doc in docs])
    
    # Create RAG chain
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain

# Initialize RAG system on startup
@app.before_request
def before_first_request():
    global rag_chain
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    rag_chain = initialize_rag_system(api_key)

# API endpoint for answering recruiter questions
@app.route('/api/answer', methods=['POST'])
def answer_question():
    data = request.json
    if not data or 'question' not in data:
        return jsonify({"error": "Please provide a question in the request body"}), 400
    
    question = data['question']
    try:
        response = rag_chain.invoke(question)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})


if __name__ == '__main__':
    # For newer Flask versions, use before_first_request differently
    # Initialize the RAG system before starting the app
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    rag_chain = initialize_rag_system(api_key)
    
    app.run(host='0.0.0.0', port=5000, debug=True)