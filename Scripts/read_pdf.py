import sys
import os

def try_pypdf(pdf_path):
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages[:5]:  # Get first 5 pages
            text += page.extract_text() or ""
        return text
    except ImportError:
        return None

def try_pdfplumber(pdf_path):
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:5]:
                text += page.extract_text() or ""
        return text
    except ImportError:
        return None

def try_fitz(pdf_path):
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc[:5]:
            text += page.get_text() or ""
        return text
    except ImportError:
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python read_pdf.py <pdf_path>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: File '{pdf_path}' not found.")
        sys.exit(1)

    # Try different engines
    text = try_pypdf(pdf_path)
    if text is None:
        text = try_pdfplumber(pdf_path)
    if text is None:
        text = try_fitz(pdf_path)
        
    if text is None:
        print("❌ Error: No PDF reading libraries found (pypdf, pdfplumber, fitz). Installing pypdf...")
        # Try to install pypdf automatically
        import subprocess
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pypdf"], check=True)
            text = try_pypdf(pdf_path)
        except Exception as e:
            print(f"❌ Failed to install pypdf: {e}")
            sys.exit(1)

    if text:
        print(text.strip())
    else:
        print("⚠️ PDF file is empty or contains no extractable text.")

if __name__ == "__main__":
    main()
