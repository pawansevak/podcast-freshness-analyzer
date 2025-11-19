import os
from docx import Document

transcript_dir = "transcripts"

for filename in os.listdir(transcript_dir):
    if filename.endswith('.docx'):
        docx_path = os.path.join(transcript_dir, filename)
        txt_filename = filename.replace('.docx', '.txt')
        txt_path = os.path.join(transcript_dir, txt_filename)
        
        # Extract text from docx
        doc = Document(docx_path)
        text = '\n'.join([para.text for para in doc.paragraphs])
        
        # Save as txt
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"✓ Converted: {filename} → {txt_filename}")

print("\n✓ All .docx files converted to .txt")
