# Open AI
import openai

# PDF processing
from PyPDF2 import PdfReader

# Chunk
from langchain.text_splitter import CharacterTextSplitter

# Embedding
from langchain_community.vectorstores import FAISS # Facebook AI Similarity Search
from langchain_openai import OpenAIEmbeddings # 1536 dim

# GPT
from langchain_openai import ChatOpenAI
from langchain_community.callbacks import get_openai_callback
from langchain.chains.question_answering import load_qa_chain
from langchain.docstore.document import Document

# datatype
from streamlit.runtime.uploaded_file_manager import UploadedFile


class InquirePDF:

    def __init__(self):
        self.pdfs = []
        self.open_ai_api_key = ''

    @property
    def open_ai_api_key(self):
        return self._open_ai_api_key

    @open_ai_api_key.setter
    def open_ai_api_key(self, value):
        self._open_ai_api_key = value

    @property
    def pdfs(self):
        return self._pdfs
    
    @pdfs.setter
    def pdfs(self, value):
        self._pdfs = value

    def process_pdf(self):
        if not hasattr(self, 'knowledge_base'):
        
            self._extract_text_from_pdfs()
            self._split_text_in_chunks()
            self._build_knowledge_base()

        return self.knowledge_base
        
    def answer_question(self, prompt):

        llm = ChatOpenAI(temperature=0,
                         openai_api_key=self.open_ai_api_key,
                         max_tokens=3000,
                         model_name='gpt-3.5-turbo',
                         request_timeout=120
                         )
        
        with get_openai_callback() as cb:
            chain = load_qa_chain(llm, chain_type='stuff')

            knowledge_base = self.process_pdf()
            docs = knowledge_base.similarity_search(prompt)
            response = chain.invoke({'input_documents':docs, 'question':prompt})

            print(cb)

        source_pages = [(doc.metadata['source'], doc.metadata['page']) for doc in docs]
        source_pages = sorted(list(set(source_pages)))

        return response['output_text'], source_pages

    def _extract_text_from_pdfs(self):

        if not hasattr(self, 'text_by_title'):

            def _extract_text_from_pdf(pdf):

                text_from_pdf = ''
                text_by_page = {}

                pdf_reader = PdfReader(pdf)

                if isinstance(pdf, UploadedFile):
                    filename = pdf.name
                else:
                    filename = pdf

                for page_num, page in enumerate(pdf_reader.pages, start=1):

                    text_from_page = page.extract_text()

                    text_by_page[page_num] = text_from_page
                    
                    text_from_pdf += text_from_page
                
                return {filename: {'text_by_page':text_by_page, 'text':text_from_pdf}}

            pdfs = self.pdfs

            text = ''
            text_by_title = {}

            for pdf in pdfs:
                extracted_info = _extract_text_from_pdf(pdf)
                text += extracted_info[list(extracted_info.keys())[0]]['text']
                text_by_title.update(extracted_info)

            self.text = text
            self.text_by_title = text_by_title
            self.no_of_pdf = len(pdfs)
        
        return self.text_by_title

    def _split_text_in_chunks(self,
                              chunk_size=1000, 
                              chunk_overlap=200):
        
        if not hasattr(self, 'data'):
            text_by_title = self._extract_text_from_pdfs()

            text_splitter = CharacterTextSplitter(
                separator='\n',
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len
                )

            for title, info in text_by_title.items():
                text = info['text']
                text_by_page = info['text_by_page']

                chunks = text_splitter.split_text(text)

                current_page = 1
                chunk_to_page = {}
                for i, chunk in enumerate(chunks, start=1):
                    for page_num, page_text in text_by_page.items():
                        if page_num >= current_page:
                            if chunk[:50].strip() in page_text:
                                current_page = page_num
                                chunk_to_page[i] = page_num
                                break

                text_by_title[title]['chunks'] = chunks
                text_by_title[title]['chunk_to_page'] = chunk_to_page
            
            self.data = text_by_title

        return self.data

    def _build_knowledge_base(self):
        
        if not hasattr(self, 'knowledge_base'):

            data = self._split_text_in_chunks()

            embeddings = OpenAIEmbeddings(openai_api_key=self.open_ai_api_key)

            docs = []

            for title, info in data.items():
                chunks = info['chunks']
                chunk_to_page = info['chunk_to_page']

                for i, chunk in enumerate(chunks, start=1):
                    doc = Document(page_content = chunk,
                                   metadata = {'page': chunk_to_page[i], 
                                               'source': title,
                                               'idx': i})
                    docs.append(doc)

            try:
                knowledge_base = FAISS.from_documents(docs, embeddings)
            
            except openai.AuthenticationError:
                error_msg = ('Please enter a valid OpenAI API key.'
                             ' You can find your API key at https://platform.openai.com/account/api-keys.')
                raise ValueError(error_msg)
            
            self.knowledge_base = knowledge_base

        return self.knowledge_base
    

if __name__ == '__main__':

    example_pdf1 = 'example_data/ssa200.pdf'
    example_pdf2 = 'example_data/ssa300.pdf'

    self = InquirePDF()

    self.pdfs = [example_pdf1, example_pdf2]

    self.open_ai_api_key = 'YOUR_API_KEY'

    self.process_pdf()
    
    self.answer_question(prompt='What is Professional Scepticism in auditing?')
