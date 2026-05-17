from fpdf import FPDF

def create_letter_pdf(text_file, output_pdf):
    with open(text_file, "r", encoding="utf-8") as f:
        content = f.read()

    pdf = FPDF()
    pdf.add_page()
    # Использование стандартного шрифта (только для латиницы/нидерландского)
    pdf.set_font("Helvetica", size=12)
    
    # Разбиваем текст на строки для корректного отображения
    for line in content.split("\n"):
        # Очистка от Markdown заголовков для PDF
        clean_line = line.replace("# ", "").replace("**", "")
        pdf.multi_cell(0, 10, txt=clean_line)
    
    pdf.output(output_pdf)
    print(f"PDF создан: {output_pdf}")

if __name__ == "__main__":
    create_letter_pdf("union-conflict-resolution/drafts/2026-05-14_union_letter_nl.md", "union-conflict-resolution/drafts/Vakbond_Brief_NL.pdf")
