import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from denspa import VectorSearch


BUCKET_NAME = os.environ.get("BUCKET_NAME",None)
BACKEND_ENV = os.environ.get("BACKEND_ENV",None)
IS_PROD = BACKEND_ENV=="prod"
if IS_PROD:
    import boto3
    from langchain_aws import BedrockEmbeddings
    
    s3 = boto3.client("s3")
    bedrock = boto3.client(service_name="bedrock-runtime")
    DB_PATH = "/tmp/store"
    INDEX_PATH = "/tmp/store/index"
    EMBEDDING_FUNCTION = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0",client=bedrock)
else:
    from langchain_huggingface import HuggingFaceEmbeddings
    
    s3 = None
    DB_PATH = "./store"
    INDEX_PATH = "store/index"
    EMBEDDING_FUNCTION = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")   
    
DB_NAME = "adiutor"
INDEX_NAME = "denspa"

if not os.path.exists(INDEX_PATH):
    os.makedirs(INDEX_PATH)
    

Base = declarative_base()

class StoreManager:
    
    db: Session
    denspa: VectorSearch
    
    def __init__(self):
        self.denspa = None
        self.db = None
   
    def load(self):
        self.load_db()
        self.load_denspa()
        
    def save(self):
        self.save_db()
        self.save_denspa()
    
    def load_db(self):
        if self.db is not None:
            return self.db
        
        if IS_PROD:
            try:
                ext = ".db"
                s3.download_file(Bucket=BUCKET_NAME, Key=DB_NAME+ext, Filename=f"{DB_PATH}/{DB_NAME}{ext}")
            except Exception as e:
                print("load_db_from_s3",e)
    
        engine = create_engine(f'sqlite:///{DB_PATH}/{DB_NAME}.db', connect_args={'check_same_thread': False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        
        self.db = SessionLocal()
       
    def save_db(self):
        self.db.commit()
        
        if IS_PROD:
            try:
                ext = ".db"
                s3.upload_file(Bucket=BUCKET_NAME, Key=DB_NAME+ext, Filename=f"{DB_PATH}/{DB_NAME}{ext}")
            except Exception as e:
                print(f"save_db_to_s3",e)
        
    def load_denspa(self):
        if self.denspa is not None:
            return self.denspa

        if IS_PROD:
            self.load_denspa_from_s3(INDEX_PATH, INDEX_NAME)

        self.denspa = VectorSearch(
            folder_path=INDEX_PATH,
            index_name=INDEX_NAME,
            embedding_function=EMBEDDING_FUNCTION,
            bm25_options={"k1": 1.25, "b": 0}
        )

    def save_denspa(self):
        self.denspa.save_local()

        if IS_PROD:
            self.save_denspa_to_s3(INDEX_PATH, INDEX_NAME)

    def save_denspa_to_s3(self, folder_path, key):
        try:
            for ext in [".faiss",".pkl",".bm25.index.pkl",".bm25.doc_store.pkl"]:
                s3.upload_file(Bucket=BUCKET_NAME, Key=key+ext, Filename=f"{folder_path}/{key}{ext}")
        except Exception as e:
            print(f"save_denspa_to_s3",e)


    def load_denspa_from_s3(self, folder_path, key):
        try:
            for ext in [".faiss",".pkl",".bm25.index.pkl",".bm25.doc_store.pkl"]:
                s3.download_file(Bucket=BUCKET_NAME, Key=key+ext, Filename=f"{folder_path}/{key}{ext}")
        except Exception as e:
            print("load_denspa_from_s3",e)
    