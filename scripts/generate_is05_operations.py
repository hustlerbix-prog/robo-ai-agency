import os
import csv
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('es')
random.seed(42)

DRIVERS = [
    ("Rodriguez, Carlos", 0.30),
    ("Huanca, Maria", 0.20),
    ("Quispe, Jorge", 0.20),
    ("Flores, Ana", 0.15),
    ("Mamani, Luis", 0.15),
]

ORIGINS = ["Lima", "Arequipa", "Trujillo", "Chiclayo", "Cusco"]
DESTINATIONS = ["Ica", "Piura", "Tacna", "Puno", "Huancayo", "Chimbote", "Iquitos", "Cajamarca"]
CARGO_TYPES = ["Electrodomesticos", "Alimentos", "Materiales construccion", "Ropa y textiles", "Herramientas", "Productos farmaceuticos"]


def pick_driver():
    r = random.random()
    cumul = 0
    for name, w in DRIVERS:
        cumul += w
        if r < cumul:
            return name
    return DRIVERS[-1][0]


def main():
    os.makedirs("documents", exist_ok=True)
    rows = []

    start_date = datetime(2025, 1, 6)
    trip_id = 1

    for week in range(12):
        week_start = start_date + timedelta(weeks=week)
        trips_this_week = random.randint(10, 12)

        for _ in range(trips_this_week):
            driver = pick_driver()
            origin = random.choice(ORIGINS)
            dest = random.choice(DESTINATIONS)
            cargo = random.choice(CARGO_TYPES)
            weight_kg = round(random.uniform(500, 15000), 1)
            distance_km = random.randint(150, 1800)
            trip_date = week_start + timedelta(days=random.randint(0, 4))

            status_r = random.random()
            if status_r < 0.75:
                estado = "Completado"
            elif status_r < 0.85:
                estado = "Cancelado"
            else:
                estado = "En Transito"

            if estado == "Completado":
                pagado = "No" if random.random() < 0.25 else "Si"
            else:
                pagado = "N/A"

            flete_usd = round(distance_km * 0.05 + weight_kg * 0.002, 2)

            rows.append({
                "trip_id": f"TP-{trip_id:04d}",
                "semana": f"W{week+1:02d}",
                "fecha": trip_date.strftime("%Y-%m-%d"),
                "conductor": driver,
                "origen": origin,
                "destino": dest,
                "tipo_carga": cargo,
                "peso_kg": weight_kg,
                "distancia_km": distance_km,
                "flete_usd": flete_usd,
                "estado": estado,
                "pagado": pagado,
            })
            trip_id += 1

    fieldnames = ["trip_id", "semana", "fecha", "conductor", "origen", "destino",
                  "tipo_carga", "peso_kg", "distancia_km", "flete_usd", "estado", "pagado"]

    with open("documents/is05_operations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    completed = [r for r in rows if r["estado"] == "Completado"]
    unpaid = [r for r in completed if r["pagado"] == "No"]
    print(f"Saved {len(rows)} trips to documents/is05_operations.csv")
    print(f"  Completado: {len(completed)}, Unpaid: {len(unpaid)}")


if __name__ == "__main__":
    main()
