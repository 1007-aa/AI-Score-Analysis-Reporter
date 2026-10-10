"""
PDF and TXT file text extraction utilities for syllabus and question papers.
"""
import io


def extract_text_from_file(filepath, filename):
    """
    Extract plain text from an uploaded file.
    Supports: .pdf, .txt, .md
    Returns extracted text string or empty string on failure.
    """
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    if ext == 'txt' or ext == 'md':
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            return ''

    elif ext == 'pdf':
        try:
            import PyPDF2
            text_parts = []
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            return '\n'.join(text_parts)
        except ImportError:
            return '[PyPDF2 not installed — install it with: pip install pypdf2]'
        except Exception as e:
            return f'[Could not extract PDF text: {str(e)}]'

    return ''
