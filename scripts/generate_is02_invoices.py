import os
import json
import random
from faker import Faker
from fpdf import FPDF

fake = Faker('es_CO')
Faker.seed(42)
random.seed(42)

os.makedirs("documents/sample_invoices", exist_ok=True)

SUPPLIERS = [
    ("AWS", "saas_minimalist", "USD"),
    ("Microsoft", "saas_minimalist", "USD"),
    ("Suministros Tech SAS", "latam_formal", "COP"),
    ("Papeleria El Centro", "small_vendor", "COP"),
    ("Transportes Rapido Ltda", "transport_slip", "COP"),
    ("Global Freight Inc", "international", "USD"),
    ("Office Depot Colombia", "retail_receipt", "COP"),
    ("Telecomunicaciones del Valle", "telco_statement", "COP"),
    ("ProClean Servicios", "handwritten_sim", "COP"),
    ("ProClean Servicios", "handwritten_sim", "COP"),
]

manifest = []
invoice_num = 1


def fmt_money(amount, currency):
    if currency == "COP":
        return f"$ {amount:,.0f} COP"
    return f"USD {amount:,.2f}"


def make_saas_minimalist(pdf, supplier, inv_id, currency):
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, supplier, ln=True)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 6, f"Invoice #{inv_id}", ln=True)
    pdf.cell(0, 6, f"Date: {fake.date_between('-60d', 'today')}", ln=True)
    pdf.ln(6)
    amount = round(random.uniform(200, 5000), 2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(120, 8, "Description")
    pdf.cell(0, 8, "Amount", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    pdf.cell(120, 7, "Cloud Services - Monthly Subscription")
    pdf.cell(0, 7, fmt_money(amount, currency), ln=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(120, 7, "Total Due")
    pdf.cell(0, 7, fmt_money(amount, currency), ln=True)
    pdf.cell(0, 6, "No tax applied (B2B cross-border)", ln=True)


def make_latam_formal(pdf, supplier, inv_id, currency):
    pdf.add_page()
    pdf.set_fill_color(0, 70, 127)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 14, f"  {supplier}", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=10)
    nit = f"NIT {random.randint(800000000,999999999)}-{random.randint(0,9)}"
    pdf.cell(0, 6, nit, ln=True)
    pdf.cell(0, 6, f"Factura No: {inv_id}  |  Fecha: {fake.date_between('-60d','today')}", ln=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(90, 7, "Descripcion", border=1)
    pdf.cell(40, 7, "Cant.", border=1)
    pdf.cell(60, 7, "Valor", border=1, ln=True)
    pdf.set_font("Helvetica", size=10)
    total = 0
    for _ in range(random.randint(2, 4)):
        desc = fake.bs().capitalize()[:40]
        qty = random.randint(1, 10)
        price = random.randint(50000, 500000)
        subtotal = qty * price
        total += subtotal
        pdf.cell(90, 6, desc, border=1)
        pdf.cell(40, 6, str(qty), border=1)
        pdf.cell(60, 6, fmt_money(subtotal, currency), border=1, ln=True)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(130, 7, "TOTAL", border=1)
    pdf.cell(60, 7, fmt_money(total, currency), border=1, ln=True)


def make_small_vendor(pdf, supplier, inv_id, currency):
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 7, supplier, ln=True)
    pdf.cell(0, 7, fake.address().replace("\n", ", "), ln=True)
    pdf.cell(0, 7, f"Tel: {fake.phone_number()}", ln=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, f"Factura #{inv_id}  -  {fake.date_between('-60d','today')}", ln=True)
    pdf.ln(3)
    pdf.set_font("Helvetica", size=10)
    total = 0
    for _ in range(random.randint(2, 5)):
        item = fake.word().capitalize()
        price = random.randint(5000, 80000)
        total += price
        pdf.cell(120, 6, item)
        pdf.cell(0, 6, fmt_money(price, currency), ln=True)
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(120, 7, "Total a pagar:")
    pdf.cell(0, 7, fmt_money(total, currency), ln=True)


def make_transport_slip(pdf, supplier, inv_id, currency):
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, supplier, ln=True)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 6, f"Guia #{inv_id}  Fecha: {fake.date_between('-60d','today')}", ln=True)
    pdf.ln(3)
    origin = fake.city()
    dest = fake.city()
    weight = round(random.uniform(50, 5000), 1)
    freight = round(weight * random.uniform(500, 2000))
    pdf.cell(0, 6, f"Origen: {origin}", ln=True)
    pdf.cell(0, 6, f"Destino: {dest}", ln=True)
    pdf.cell(0, 6, f"Peso: {weight} kg", ln=True)
    pdf.cell(0, 6, f"Tipo de carga: {random.choice(['General','Refrigerada','Fragil'])}", ln=True)
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, f"Flete total: {fmt_money(freight, currency)}", ln=True)


def make_international(pdf, supplier, inv_id, currency):
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, supplier, ln=True)
    pdf.set_font("Helvetica", size=10)
    po = f"PO-{random.randint(10000,99999)}"
    swift = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=11))
    iban = 'GB' + ''.join(random.choices('0123456789', k=20))
    pdf.cell(0, 6, f"Invoice: {inv_id}  |  PO: {po}", ln=True)
    pdf.cell(0, 6, f"Date: {fake.date_between('-60d','today')}", ln=True)
    pdf.cell(0, 6, f"SWIFT: {swift}  |  IBAN: {iban}", ln=True)
    pdf.ln(3)
    amount = round(random.uniform(1000, 20000), 2)
    pdf.cell(0, 6, f"Services rendered: International freight & logistics", ln=True)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"Amount Due: {fmt_money(amount, currency)}", ln=True)


def make_retail_receipt(pdf, supplier, inv_id, currency):
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, supplier, align="C", ln=True)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 6, f"Recibo #{inv_id}  {fake.date_between('-60d','today')}", align="C", ln=True)
    pdf.ln(3)
    total = 0
    for _ in range(random.randint(3, 7)):
        item = fake.word().capitalize()
        qty = random.randint(1, 5)
        unit = random.randint(5000, 50000)
        sub = qty * unit
        total += sub
        pdf.cell(80, 6, item)
        pdf.cell(20, 6, f"{qty} x")
        pdf.cell(40, 6, fmt_money(unit, currency))
        pdf.cell(0, 6, fmt_money(sub, currency), ln=True)
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, f"TOTAL: {fmt_money(total, currency)}", align="C", ln=True)


def make_telco_statement(pdf, supplier, inv_id, currency):
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, supplier, ln=True)
    pdf.set_font("Helvetica", size=10)
    account = f"ACC-{random.randint(100000,999999)}"
    pdf.cell(0, 6, f"Estado de Cuenta No: {inv_id}  |  Cuenta: {account}", ln=True)
    pdf.cell(0, 6, f"Periodo: {fake.month_name()} 2025", ln=True)
    pdf.ln(3)
    items = [("Plan empresarial 100Mbps", random.randint(80000, 200000)),
             ("Lineas adicionales", random.randint(20000, 60000)),
             ("Servicio de nube", random.randint(30000, 100000))]
    for desc, price in items:
        pdf.cell(120, 6, desc)
        pdf.cell(0, 6, fmt_money(price, currency), ln=True)
    total = sum(p for _, p in items)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(120, 7, "Total a pagar:")
    pdf.cell(0, 7, fmt_money(total, currency), ln=True)


def make_handwritten_sim(pdf, supplier, inv_id, currency):
    pdf.add_page()
    pdf.set_font("Courier", "B", 13)
    pdf.cell(0, 8, supplier, ln=True)
    pdf.set_font("Courier", size=11)
    pdf.cell(0, 7, f"Factura: {inv_id}   Fecha: {fake.date_between('-60d','today')}", ln=True)
    pdf.ln(3)
    total = 0
    for _ in range(random.randint(2, 5)):
        service = fake.catch_phrase()[:35]
        price = random.randint(20000, 300000)
        total += price
        dots = '.' * (50 - len(service))
        pdf.cell(0, 7, f"{service}{dots}{fmt_money(price, currency)}", ln=True)
    pdf.ln(3)
    pdf.set_font("Courier", "B", 11)
    pdf.cell(0, 7, f"TOTAL{'.' * 45}{fmt_money(total, currency)}", ln=True)


STYLE_MAP = {
    "saas_minimalist": make_saas_minimalist,
    "latam_formal": make_latam_formal,
    "small_vendor": make_small_vendor,
    "transport_slip": make_transport_slip,
    "international": make_international,
    "retail_receipt": make_retail_receipt,
    "telco_statement": make_telco_statement,
    "handwritten_sim": make_handwritten_sim,
}


def main():
    inv_counter = 1
    for supplier, style, currency in SUPPLIERS:
        for _ in range(3):
            inv_id = f"INV-{inv_counter:04d}"
            fname = f"invoice_{inv_counter:02d}_{style}.pdf"
            fpath = f"documents/sample_invoices/{fname}"

            if inv_counter == 25:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Helvetica", size=8)
                for _ in range(200):
                    pdf.cell(0, 3, fake.sentence(), ln=True)
                pdf.output(fpath)
                manifest.append({"invoice": inv_id, "file": fname, "style": "illegible", "supplier": supplier, "currency": currency, "note": "intentionally illegible"})
                print(f"Invoice {inv_counter:02d}: {fname} [ILLEGIBLE]")
            else:
                pdf = FPDF()
                STYLE_MAP[style](pdf, supplier, inv_id, currency)
                pdf.output(fpath)
                manifest.append({"invoice": inv_id, "file": fname, "style": style, "supplier": supplier, "currency": currency})
                print(f"Invoice {inv_counter:02d}: {fname}")

            inv_counter += 1

    with open("documents/is02_invoices_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(manifest)} invoices and manifest.")


if __name__ == "__main__":
    main()
