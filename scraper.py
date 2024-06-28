import os
import logging
import numpy as np
import spacy
from sentence_transformers import SentenceTransformer, util
import torch
import fitz  # PyMuPDF
import docx
import pythoncom
import comtypes.client
import sqlite3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load spaCy and sentence transformer models
nlp = spacy.load('en_core_web_sm')
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

DATABASE_FILE = 'database.db'

class ResumeAnalyzer:
    def __init__(self, resume_folder):
        self.resume_folder = resume_folder
        self._setup_database()

    def _setup_database(self):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resumes (
                id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                embedding BLOB NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        logging.info('Database setup successful.')

    def preprocess_and_store_resumes(self):
        file_paths = self._get_resume_paths()
        for file_path in file_paths:
            text = self._extract_text(file_path)
            embedding = self._get_embedding(text)
            self._insert_resume(os.path.basename(file_path), file_path, embedding.tobytes())

    def _insert_resume(self, resume_id, file_path, embedding):
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO resumes (id, file_path, embedding) VALUES (?, ?, ?)',
                           (resume_id, file_path, embedding))
            conn.commit()
            conn.close()
            logging.info(f'Inserted resume {resume_id} into the database successfully.')
        except sqlite3.Error as e:
            logging.error(f'Error inserting resume {resume_id}: {e}')

    def _get_resume_paths(self):
        resume_paths = []
        for root, _, files in os.walk(self.resume_folder):
            for file in files:
                if file.endswith(('.pdf', '.docx', '.doc')):
                    resume_paths.append(os.path.join(root, file))
        return resume_paths

    def _extract_text(self, file_path):
        extension = os.path.splitext(file_path)[1].lower()
        if extension == '.pdf':
            text = self._extract_text_from_pdf(file_path)
        elif extension == '.docx':
            text = self._extract_text_from_docx(file_path)
        elif extension == '.doc':
            text = self._extract_text_from_doc(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")
        return text

    def _extract_text_from_pdf(self, pdf_path):
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text

    def _extract_text_from_docx(self, docx_path):
        doc = docx.Document(docx_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text

    def _extract_text_from_doc(self, doc_path):
        pythoncom.CoInitialize()
        word = comtypes.client.CreateObject('Word.Application')
        word.Visible = False
        doc = word.Documents.Open(doc_path)
        text = doc.Content.Text
        doc.Close()
        word.Quit()
        pythoncom.CoUninitialize()
        return text

    def _get_embedding(self, text):
        return model.encode(text, convert_to_tensor=True)

    def find_matching_resumes(self, job_description, threshold=0.7, top_n=6):
        job_description_embedding = self._get_embedding(job_description)
        resumes = self._fetch_all_resumes()
        matching_resumes = []
        for resume in resumes:
            resume_embedding = torch.tensor(np.frombuffer(resume[2], dtype=np.float32))
            similarity = util.pytorch_cos_sim(job_description_embedding, resume_embedding).item()
            if similarity >= threshold:
                matching_resumes.append((resume[1], similarity * 100))
        matching_resumes = sorted(matching_resumes, key=lambda x: x[1], reverse=True)
        return matching_resumes[:top_n]

    def _fetch_all_resumes(self):
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM resumes')
            resumes = cursor.fetchall()
            conn.close()
            logging.info('Fetched all resumes from the database successfully.')
            return resumes
        except sqlite3.Error as e:
            logging.error(f'Error fetching resumes: {e}')
            return []

def setup_database():
    analyzer = ResumeAnalyzer(resume_folder='')
    analyzer._setup_database()

def fetch_all_resumes():
    analyzer = ResumeAnalyzer(resume_folder='')
    return analyzer._fetch_all_resumes()

# Celery task for asynchronous processing
from celery import Celery

celery = Celery(__name__, broker='pyamqp://guest@localhost//')

@celery.task
def preprocess_and_store_resumes_task():
    logger = preprocess_and_store_resumes_task.get_logger()
    logger.info(f"Starting resume preprocessing task in folder: {os.path.join(os.getcwd(), 'static', 'Res')}")

    analyzer = ResumeAnalyzer(os.path.join(os.getcwd(), 'static', 'Res'))
    analyzer.preprocess_and_store_resumes()
