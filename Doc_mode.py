# -*- coding: utf-8 -*-
"""Untitled112.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1WWoFBbuRt9zUlvqImcepuDj5jsy6D-dE
"""

# text_analysis.py

# Install required libraries
import pdfplumber
from docx import Document
from transformers import pipeline, T5ForConditionalGeneration, T5Tokenizer
from concurrent.futures import ThreadPoolExecutor

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ''.join(page.extract_text() for page in pdf.pages)
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

# Function to extract text from a DOCX file
def extract_text_from_docx(docx_path):
    try:
        doc = Document(docx_path)
        return '\n'.join(paragraph.text for paragraph in doc.paragraphs)
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return ""

# Load T5 and BERT models concurrently
def load_models():
    with ThreadPoolExecutor() as executor:
        t5_future = executor.submit(load_t5_model)
        qa_future = executor.submit(load_qa_model)
        t5_model, t5_tokenizer = t5_future.result()
        qa_model = qa_future.result()
    return t5_model, t5_tokenizer, qa_model

# Load T5 model for summarization and key point extraction
def load_t5_model():
    model_name = "t5-large"
    model = T5ForConditionalGeneration.from_pretrained(model_name)
    tokenizer = T5Tokenizer.from_pretrained(model_name)
    return model, tokenizer

# Load BERT model for QA
def load_qa_model():
    return pipeline("question-answering", model="bert-large-uncased-whole-word-masking-finetuned-squad")

# Process text using T5 model for summarization or key points
def process_text_with_t5(model, tokenizer, context, task, num_points=5):
    task_prompt = {"summarize": f"summarize: {context}",
                   "keypoints": f"extract {num_points} key points: {context}"}
    prompt = task_prompt.get(task)
    if not prompt:
        return "Invalid task specified."

    inputs = tokenizer.encode(prompt, return_tensors="pt", max_length=1024, truncation=True)
    outputs = model.generate(inputs, max_length=512, num_beams=5, length_penalty=2.0, early_stopping=True)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Answer general queries with the BERT QA model
def answer_query(qa_model, context, query):
    result = qa_model(question=query, context=context)
    return result.get('answer', 'Sorry, I could not find an answer.')

if __name__ == "__main__":
    # Specify your input file paths
    file_path = input("Enter the path of the file (PDF or DOCX): ").strip()

    # Extract text based on file type
    if file_path.endswith(".pdf"):
        context = extract_text_from_pdf(file_path)
    elif file_path.endswith(".docx"):
        context = extract_text_from_docx(file_path)
    else:
        print("Unsupported file format. Please upload a PDF or DOCX file.")
        context = None

    if context:
        print("\nContent extracted successfully. Loading models, please wait...")
        t5_model, t5_tokenizer, qa_model = load_models()
        print("Models loaded successfully! You can now ask questions.")

        while True:
            query = input("\nAsk a question about the content (or type 'exit' to quit): ").strip()
            if query.lower() == "exit":
                print("Exiting. Thank you!")
                break

            if "key points" in query.lower():
                print("\nExtracting 5 key points...")
                keypoints = process_text_with_t5(t5_model, t5_tokenizer, context, task="keypoints", num_points=5)
                print("\nKey Points:")
                for i, point in enumerate(keypoints.split("\n"), 1):
                    print(f"{i}. {point.strip()}")
            elif "summarize" in query.lower():
                print("\nGenerating a summary...")
                summary = process_text_with_t5(t5_model, t5_tokenizer, context, task="summarize")
                print(f"\nSummary:\n{summary}")
            else:
                print("\nAnswering your question...")
                answer = answer_query(qa_model, context, query)
                print(f"Answer: {answer}")
    else:
        print("No content could be extracted from the uploaded file.")