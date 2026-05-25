import os
import anthropic
from fpdf import FPDF

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SECTIONS = [
    ("Admision de Pacientes", "Procedimiento completo de admision de pacientes incluyendo registro, verificacion de seguro medico, asignacion de cama y documentacion inicial."),
    ("Administracion de Medicamentos", "Protocolo de administracion segura de medicamentos: verificacion de dosis, registro en historia clinica, manejo de reacciones adversas."),
    ("Reporte de Incidentes", "Procedimiento para reportar incidentes clinicos: clasificacion de severidad, cadena de notificacion, documentacion y seguimiento."),
    ("Proteccion de Datos del Paciente", "Politicas de confidencialidad y proteccion de datos segun normativa colombiana, acceso a historias clinicas y manejo de informacion sensible."),
    ("Cancelacion de Citas", "Proceso de cancelacion y reprogramacion de citas medicas: plazos, notificaciones, lista de espera y registro."),
    ("Limpieza y Esterilizacion", "Protocolos de higiene hospitalaria: frecuencia de limpieza por area, productos autorizados, esterilizacion de equipos e instrumental."),
    ("Mantenimiento de Equipos", "Programa de mantenimiento preventivo y correctivo de equipos medicos: cronograma, responsables, registros y proveedores autorizados."),
    ("Facturacion y Cobros", "Procedimiento de facturacion a pacientes particulares y EPS: codigos CUPS, tarifas SOAT, conciliacion con aseguradoras."),
    ("Confidencialidad del Personal", "Obligaciones de confidencialidad del personal medico y administrativo, acuerdos de no divulgacion y consecuencias de incumplimiento."),
    ("Apertura y Cierre de Turno", "Procedimientos de apertura y cierre de turno: entrega de pacientes, verificacion de inventario de medicamentos, registro de novedades."),
]


def generate_section(title, description):
    prompt = f"""Eres el jefe de calidad de la Clinica Santa Elena en Bogota, Colombia.
Redacta la seccion '{title}' del manual de procedimientos internos.
Contexto: {description}

El texto debe:
- Estar en espanol formal colombiano
- Tener minimo 400 palabras
- Incluir pasos numerados concretos
- Mencionar cargos especificos (Jefe de Enfermeria, Director Medico, etc.)
- Incluir formularios o codigos internos ficticios (ej: FO-ADM-001)
- Sonar completamente real y profesional
- NO incluir el titulo de la seccion al inicio del texto

Genera SOLO el contenido de la seccion, sin introduccion ni conclusion generica."""

    msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text.strip()


class ClinicaPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(0, 70, 127)
        self.cell(0, 8, "CLINICA SANTA ELENA - MANUAL DE PROCEDIMIENTOS INTERNOS", align="C", ln=True)
        self.set_text_color(0, 0, 0)
        self.set_draw_color(0, 70, 127)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Pagina {self.page_no()} | Documento Confidencial", align="C")


def main():
    os.makedirs("documents", exist_ok=True)

    pdf = ClinicaPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title page
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(0, 70, 127)
    pdf.cell(0, 15, "CLINICA SANTA ELENA", align="C", ln=True)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Manual de Procedimientos Internos", align="C", ln=True)
    pdf.set_font("Helvetica", size=12)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, "Version 3.2 - Enero 2025", align="C", ln=True)
    pdf.cell(0, 10, "Bogota D.C., Colombia", align="C", ln=True)
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 8, "Documento de uso interno y confidencial", align="C", ln=True)
    pdf.cell(0, 8, "Prohibida su reproduccion sin autorizacion de la Gerencia General", align="C", ln=True)

    all_text = "CLINICA SANTA ELENA\nManual de Procedimientos Internos\nVersion 3.2 - Enero 2025\n\n"

    for i, (title, description) in enumerate(SECTIONS, 1):
        print(f"Generating section {i}/10: {title}...")
        content = generate_section(title, description)

        pdf.add_page()
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_fill_color(230, 240, 250)
        pdf.cell(0, 10, f"Seccion {i}: {title}", ln=True, fill=True)
        pdf.ln(4)
        pdf.set_font("Helvetica", size=11)

        for line in content.split("\n"):
            safe = line.encode("latin-1", errors="replace").decode("latin-1")
            if safe.strip():
                pdf.multi_cell(0, 6, safe, wrapmode="CHAR")

        all_text += f"\n\n=== SECCION {i}: {title.upper()} ===\n\n{content}"
        print(f"  Done ({len(content)} chars)")

    pdf.output("documents/procedimientos_clinica_santa_elena.pdf")
    with open("documents/procedimientos_clinica_santa_elena.txt", "w", encoding="utf-8") as f:
        f.write(all_text)

    print("\nSaved:")
    print("  documents/procedimientos_clinica_santa_elena.pdf")
    print("  documents/procedimientos_clinica_santa_elena.txt")


if __name__ == "__main__":
    main()
