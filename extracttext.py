import pytesseract
from pdf2image import convert_from_path
import os

# Input and output files
pdf_file = r"E:\TOEIC Coach\Content\[sachtoeic.com]Jim's Toeic 1000 LC-10-15.pdf"
output_file = r"E:\TOEIC Coach\Content\[sachtoeic.com]Jim's Toeic 1000 LC-10-15.txt"

# Try to find poppler path
poppler_path = None
possible_paths = [
    r"C:\poppler\Library\bin",
    r"C:\Program Files\poppler\bin",
    r"C:\Program Files (x86)\poppler\bin", 
    r"C:\poppler\bin",
    os.path.join(os.path.dirname(__file__), "poppler", "bin")
]

for path in possible_paths:
    if os.path.exists(path):
        poppler_path = path
        break

print(f"Using poppler path: {poppler_path}")

# Convert PDF pages to images
try:
    if poppler_path:
        pages = convert_from_path(pdf_file, dpi=300, poppler_path=poppler_path)
    else:
        pages = convert_from_path(pdf_file, dpi=300)
except Exception as e:
    print(f"Error converting PDF: {e}")
    print("Please install poppler binaries for Windows:")
    print("1. Download from: https://github.com/oschwartz10612/poppler-windows/releases/")
    print("2. Extract to C:\\poppler")
    print("3. Add C:\\poppler\\bin to your PATH environment variable")
    exit(1)

# Extract text with OCR
text = ""
for i, page in enumerate(pages, start=1):
    text += pytesseract.image_to_string(page) + "\n"
    print(f"Processed page {i}")

# Save text to file
with open(output_file, "w", encoding="utf-8") as f:
    f.write(text)

print(f"✅ OCR text extracted and saved to {output_file}")
