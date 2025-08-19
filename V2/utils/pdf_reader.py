from PyPDF2 import PdfReader

def extract_app_names_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    app_names = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            # Split by newline if each app is on a new line. Adjust if needed.
            names = [line.strip() for line in text.split('\n') if line.strip()]
            app_names.extend(names)
    return app_names
