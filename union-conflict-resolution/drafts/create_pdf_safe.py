from fpdf import FPDF

def create_letter_pdf(text_file, output_pdf):
    with open(text_file, "r", encoding="utf-8") as f:
        content = f.read()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    
    # Очистка текста от всего, что не латиница/пунктуация
    for line in content.split("\n"):
        if line.startswith("#"):
            pdf.set_font("Helvetica", style="B", size=14)
            clean_line = line.replace("#", "").strip()
        else:
            pdf.set_font("Helvetica", size=12)
            clean_line = line.replace("**", "").strip()
        
        # Оставляем только символы, которые точно есть в Latin-1
        safe_line = "".join([c for c in clean_line if ord(c) < 256])
        if safe_line:
            pdf.multi_cell(0, 10, text=safe_line)
        else:
            pdf.ln(5)
    
    pdf.output(output_pdf)
    print(f"PDF создан: {output_pdf}")

if __name__ == "__main__":
    create_letter_pdf("union-conflict-resolution/drafts/2026-05-14_union_letter_nl.md", "union-conflict-resolution/drafts/Vakbond_Brief_NL.pdf")
