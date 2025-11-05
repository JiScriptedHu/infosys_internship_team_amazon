# Install necessary packages
# !apt-get update
# !apt-get install -y tesseract-ocr
# !pip install pytesseract pillow
# !pip install transformers torch

# import libraries
from transformers import BartTokenizer, BartForConditionalGeneration
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

# Tokenize the input text and count the number of tokens
# This helps to set max_length dynamically for the summarization model
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")

input_tokens = tokenizer.encode(ocr_text_clean, return_tensors="pt")
num_input_tokens = input_tokens.shape[1]
print("Number of input tokens:", num_input_tokens)

#Summarize
summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=0)

summary = summarizer(ocr_text_clean, max_length=num_input_tokens, min_length=20, do_sample=False)[0]['summary_text']

# Display result
display(image)
print("\n📝 OCR Output:\n")
print(ocr_text)
print("\n🔍 Summary:\n")
print(summary)