import docx

def read_docx(file_path):
    print(f"Чтение файла: {file_path}\n")
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    print("\n".join(full_text))

if __name__ == "__main__":
    read_docx("union-conflict-resolution/evidence/Aanvraag ouderschapsverlof (27.04.2026 - 03.05.2026).docx")
