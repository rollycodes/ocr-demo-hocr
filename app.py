from flask import Flask, render_template, send_file
import os
from PIL import Image
import pytesseract
import pdfkit
from PIL import ImageDraw
from langdetect import detect
from PIL import ImageFont
from bs4 import BeautifulSoup
from googletrans import Translator

lang_map = {
    'en': 'eng',
    'ar': 'ara',
    # add other languages as needed
}


app = Flask(__name__)

@app.route('/')
def index():
    files = [f for f in os.listdir('raw') if f.endswith('.tif')]
    return render_template('index.html', files=files)

@app.route('/generate_ocr/<filename>')
def generate_ocr(filename):
    image_path = os.path.join('raw', filename)
    image = Image.open(image_path)


    # Extract a small portion of text for language detection
    sample_text = pytesseract.image_to_string(image, lang='en+ara')
    detected_lang = detect(sample_text)

    # Map to Tesseract language code
    tesseract_lang = lang_map.get(detected_lang, detected_lang)

    print(tesseract_lang)

    hocr_data = pytesseract.image_to_pdf_or_hocr(image, extension='hocr', lang=tesseract_lang)
    output_hocr_path = os.path.join('outputs', f"{filename.split('.')[0]}_hocr.html")
    output_pdf_path = os.path.join('outputs', f"{filename.split('.')[0]}_hocr.pdf")
    
    with open(output_hocr_path, 'wb') as f:
        f.write(hocr_data)
    
    # Convert HOCR to PDF
    pdfkit.from_file(output_hocr_path, output_pdf_path)
    
    return send_file(output_pdf_path, as_attachment=True)


@app.route('/generate_ocr_translated/<filename>')
def generate_ocr_translated(filename):
    image_path = os.path.join('raw', filename)
    image = Image.open(image_path)

    # Extract a small portion of text for language detection
    sample_text = pytesseract.image_to_string(image, lang='en+ara')
    detected_lang = detect(sample_text)

    # Map to Tesseract language code
    tesseract_lang = lang_map.get(detected_lang, detected_lang)

    # Generate HOCR data
    hocr_data = pytesseract.image_to_pdf_or_hocr(image, extension='hocr', lang=tesseract_lang)
    output_hocr_path = os.path.join('outputs', f"{filename.split('.')[0]}_translated_hocr.html")
    output_pdf_path = os.path.join('outputs', f"{filename.split('.')[0]}_translated_hocr.pdf")

    with open(output_hocr_path, 'wb') as f:
        f.write(hocr_data)

    # Load HOCR data and extract text
    with open(output_hocr_path, 'r', encoding='utf-8') as f:
        hocr_content = f.read()

    # Parse HOCR content with BeautifulSoup
    soup = BeautifulSoup(hocr_content, 'html.parser')

    # Translate the text to English
    translator = Translator()
    for word in soup.find_all(class_='ocrx_word'):
        if word.string:
            try:
                print("Original Text: ", word.string)  # Debug print
                translation = translator.translate(word.string,  src=detected_lang, dest='en')
                print("Translated Text: ", translation.text)  # Debug print
                word.string.replace_with(translation.text)
            except Exception as e:
                print(f"Translation failed for text '{word.string}' with error: {e}")
        
    # Save modified HOCR content
    with open(output_hocr_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    # Convert HOCR to PDF
    pdfkit.from_file(output_hocr_path, output_pdf_path)

    return send_file(output_pdf_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
