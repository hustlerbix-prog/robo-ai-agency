import os
import json
import random
import anthropic
from faker import Faker

fake = Faker('es_CO')
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

CATEGORIES = [
    ("rental_enquiry", 8),
    ("viewing_request", 6),
    ("maintenance_urgent", 4),
    ("maintenance_routine", 7),
    ("general", 5),
]

PROPERTY_REFS = [f"APT-{random.randint(1000,9999)}" for _ in range(10)] + \
               [f"LOC-{random.randint(1000,9999)}" for _ in range(5)]

SUBJECT_TEMPLATES = {
    "rental_enquiry": ["Consulta sobre arriendo de apartamento", "Información sobre disponibilidad", "Solicitud de información de arriendo"],
    "viewing_request": ["Solicitud de visita a inmueble", "¿Podemos agendar una visita?", "Interesado en ver el inmueble"],
    "maintenance_urgent": ["URGENTE: Falla en instalación eléctrica", "URGENTE: Problema de plomería", "Emergencia de mantenimiento"],
    "maintenance_routine": ["Solicitud de mantenimiento rutinario", "Revisión programada necesaria", "Mantenimiento de aires acondicionados"],
    "general": ["Consulta general", "Información adicional requerida", "Pregunta sobre contrato"],
}


def generate_body(category, name, property_ref):
    prompt_map = {
        "rental_enquiry": f"Escribe un email en español de {name} preguntando sobre disponibilidad y precio del inmueble {property_ref}. Máximo 120 palabras.",
        "viewing_request": f"Escribe un email en español de {name} solicitando una visita al inmueble {property_ref} esta semana. Máximo 100 palabras.",
        "maintenance_urgent": f"Escribe un email urgente en español de {name} reportando un problema grave de mantenimiento en {property_ref} que necesita atención inmediata. Máximo 120 palabras.",
        "maintenance_routine": f"Escribe un email en español de {name} solicitando mantenimiento rutinario en {property_ref}. Máximo 100 palabras.",
        "general": f"Escribe un email en español de {name} con una pregunta general sobre el inmueble {property_ref}. Máximo 100 palabras.",
    }
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt_map[category]}]
    )
    return msg.content[0].text.strip()


def main():
    os.makedirs("documents", exist_ok=True)
    emails = []

    for category, count in CATEGORIES:
        for _ in range(count):
            name = fake.name()
            email_addr = fake.email()
            phone = fake.phone_number()
            prop_ref = random.choice(PROPERTY_REFS)
            subject = random.choice(SUBJECT_TEMPLATES[category])
            body = generate_body(category, name, prop_ref)

            emails.append({
                "category": category,
                "sender_name": name,
                "sender_email": email_addr,
                "phone": phone,
                "property_ref": prop_ref,
                "subject": subject,
                "body": body,
            })
            print(f"Generated [{category}] email from {name}")

    with open("documents/is01_emails.json", "w", encoding="utf-8") as f:
        json.dump(emails, f, ensure_ascii=False, indent=2)

    with open("documents/is01_emails.txt", "w", encoding="utf-8") as f:
        for i, e in enumerate(emails, 1):
            f.write(f"=== Email {i} ===\n")
            f.write(f"Category: {e['category']}\n")
            f.write(f"From: {e['sender_name']} <{e['sender_email']}>\n")
            f.write(f"Phone: {e['phone']}\n")
            f.write(f"Property: {e['property_ref']}\n")
            f.write(f"Subject: {e['subject']}\n\n")
            f.write(e['body'] + "\n\n")

    print(f"\nSaved {len(emails)} emails to documents/is01_emails.json and is01_emails.txt")


if __name__ == "__main__":
    main()
