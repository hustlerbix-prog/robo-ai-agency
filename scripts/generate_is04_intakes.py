import os
import json
import random
import anthropic
from faker import Faker

fake = Faker('es_CO')
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

DISTRIBUTION = [
    ("Civil", 6),
    ("Laboral", 5),
    ("Penal", 4),
    ("Comercial", 3),
    ("Otro", 2),
]

URGENCY_WEIGHTS = [
    ("urgente", 0.20),
    ("esta_semana", 0.50),
    ("sin_prisa", 0.30),
]


def pick_urgency():
    r = random.random()
    cumul = 0
    for label, w in URGENCY_WEIGHTS:
        cumul += w
        if r < cumul:
            return label
    return "sin_prisa"


def generate_description(tipo, name):
    prompt = f"""Eres un ciudadano colombiano llamado {name} que necesita asesoria legal.
Escribe una descripcion breve (3-5 oraciones) de un caso de tipo '{tipo}' para una firma de abogados.
Usa lenguaje coloquial, menciona fechas y montos especificos. Maximo 120 palabras."""
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text.strip()


def main():
    os.makedirs("documents", exist_ok=True)
    intakes = []

    for tipo, count in DISTRIBUTION:
        for _ in range(count):
            name = fake.name()
            email = fake.email()
            phone = fake.phone_number()
            urgencia = pick_urgency()
            descripcion = generate_description(tipo, name)

            intakes.append({
                "nombre": name,
                "email": email,
                "telefono": phone,
                "tipo_asunto": tipo,
                "descripcion": descripcion,
                "urgencia": urgencia,
            })
            print(f"Generated [{tipo}] intake for {name} ({urgencia})")

    with open("documents/is04_intakes.json", "w", encoding="utf-8") as f:
        json.dump(intakes, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(intakes)} intakes to documents/is04_intakes.json")


if __name__ == "__main__":
    main()
