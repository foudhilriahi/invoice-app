																										Invoices App

Overview

This is an invoice processing application built to extract and manage data from invoice documents. The app supports multiple languages and utilizes various libraries for PDF processing, OCR, and data handling.

Prerequisites

Before running the application, ensure you have the following installed:


Python 3.x (latest stable version recommended)
Poppler for Windows (for PDF processing)
Download version 24.08.0-0 from official Poppler releases or a trusted source.
Extract to C:\poppler-24.08.0\bin.
Add C:\poppler-24.08.0\bin to your system PATH.
Tesseract OCR (for text extraction from images)
Download the installer tesseract-ocr-w64-setup-v5.3.0.20230810.exe from UB Mannheim.
Install it (default path is C:\Program Files\Tesseract-OCR).
Add C:\Program Files\Tesseract-OCR to your system PATH.


Installation
Clone the repository:

git clone <repository-URL>
cd invoice app



Install the required Python packages:

pip install -r requirements.txt

The requirements.txt file includes:
pillow
pdf2image
pytesseract
python-dotenv
requests
langdetect
pandas
openpyxl


Set up environment variables:

Create a .env file in the project root and add your API keys (e.g., DEEPSEEK_API_KEY, OPENROUTER_API_KEY) as shown in the .env example.






Run the application:

python main.py



Follow the on-screen instructions to process invoices or manage data.

Supported Languages

English (en)

French (fr)

German (de)

Spanish (es)

Italian (it)

Portuguese (pt)

Dutch (nl)

Japanese (ja)

Korean (ko)
