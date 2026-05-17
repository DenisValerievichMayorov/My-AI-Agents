from fpdf import FPDF

def create_clean_contract_pdf(input_text_file, output_pdf):
    with open(input_text_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    
    for line in lines:
        # Убираем возможные не-latin1 символы для Helvetica
        clean_line = line.encode("ascii", "ignore").decode("ascii").strip()
        if clean_line:
            pdf.multi_cell(0, 5, text=clean_line)
        else:
            pdf.ln(5)
    
    pdf.output(output_pdf)
    print(f"Чистый PDF контракта создан: {output_pdf}")

if __name__ == "__main__":
    create_clean_contract_pdf("union-conflict-resolution/evidence/page1_ocr.txt", "union-conflict-resolution/evidence/Contract_Denys_Maiorov_Clean.pdf")
