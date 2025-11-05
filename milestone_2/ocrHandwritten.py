# Install dependencies
# !pip install chandra-ocr transformers torch pillow

# Import libraries
import re
from PIL import Image
from transformers import pipeline
from IPython.display import display
from chandra.model import InferenceManager
from chandra.model.schema import BatchInputItem
from transformers import BartTokenizer, BartForConditionalGeneration

# Load image
image_path = "/content/WhatsApp Image 2025-11-04 at 18.19.36.jpeg"
image = Image.open(image_path).convert("RGB")

# Use Chandra to do OCR/layout extraction
manager = InferenceManager(method="hf")
batch_item = BatchInputItem(image=image, prompt_type="ocr_layout")
result = manager.generate([batch_item])[0]

ocr_markdown = result.markdown

# Clean the extracted text (strip markdown/tags if needed)
ocr_text = re.sub(r'<[^>]+>', '', ocr_markdown)
ocr_text_clean = re.sub(r'[\n\f]+', ' ', ocr_text).strip()

# Tokenize the input text and count the number of tokens
# This helps to set max_length dynamically for the summarization model
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-xsum")

input_tokens = tokenizer.encode(ocr_text_clean, return_tensors="pt")
num_input_tokens = input_tokens.shape[1]
print("Number of input tokens:", num_input_tokens)

# Summarization pipeline (on CPU)
summarizer = pipeline("summarization", model="facebook/bart-large-xsum", device=-1)
# Summarize
summary = summarizer(ocr_text_clean, max_length=num_input_tokens, min_length=20, do_sample=False)[0]['summary_text']

# Display result
display(image)
print("\n📝 OCR Output:\n", ocr_text_clean)
print("\n🔍 Summary:\n", summary)