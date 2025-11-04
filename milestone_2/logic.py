# import libraries
from IPython.display import display
from transformers import pipeline
from PIL import Image
import pytesseract
import re
import os

# load image
image_path = "/content/test.jpg"  # image path
image = Image.open(image_path)

# Perform OCR
ocr_text = pytesseract.image_to_string(image)
ocr_text_clean = re.sub(r'[\n\f]+', ' ', ocr_text).strip() # clean text

# Summarization using transformers pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=0)
summary = summarizer(ocr_text_clean, max_length=160, min_length=20, do_sample=False)[0]['summary_text']

display(image)
print("📝 OCR Output:\n")
print(ocr_text)
print("\n🔍 Summary:\n")
print(summary)