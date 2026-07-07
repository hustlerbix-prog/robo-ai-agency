import os
import json
import csv

PASS = "PASS"
FAIL = "FAIL"
results = []


def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, label, detail))
    print(f"[{status}] {label}" + (f" — {detail}" if detail else ""))


def main():
    # is01_emails.json
    try:
        with open("documents/is01_emails.json") as f:
            emails = json.load(f)
        count = len(emails)
        has_urgent = any(e["category"] == "maintenance_urgent" for e in emails)
        check("IS-01 emails count >= 25", count >= 25, f"{count} emails found")
        check("IS-01 has maintenance_urgent", has_urgent)
    except Exception as e:
        check("IS-01 emails.json readable", False, str(e))

    # sample_invoices PDFs
    try:
        pdfs = [f for f in os.listdir("documents/sample_invoices") if f.endswith(".pdf")]
        check("IS-02 invoice PDFs >= 20", len(pdfs) >= 20, f"{len(pdfs)} PDFs found")
    except Exception as e:
        check("IS-02 invoice PDFs", False, str(e))

    # procedimientos PDF
    try:
        size = os.path.getsize("documents/procedimientos_clinica_santa_elena.pdf")
        check("IS-03 procedures PDF > 20KB", size > 20480, f"{size} bytes")
    except Exception as e:
        check("IS-03 procedures PDF", False, str(e))

    # is04_intakes.json
    try:
        with open("documents/is04_intakes.json") as f:
            intakes = json.load(f)
        check("IS-04 intakes count >= 20", len(intakes) >= 20, f"{len(intakes)} intakes found")
        required = {"nombre", "email", "telefono", "tipo_asunto", "descripcion", "urgencia"}
        complete = all(
            required <= set(i) and all(str(i[k]).strip() for k in required)
            for i in intakes
        )
        check("IS-04 intakes fields complete", complete)
    except Exception as e:
        check("IS-04 intakes.json readable", False, str(e))

    # is05_operations.csv unpaid completed trips
    try:
        with open("documents/is05_operations.csv") as f:
            rows = list(csv.DictReader(f))
        unpaid = [r for r in rows if r["estado"] == "Completado" and r["pagado"] == "No"]
        check("IS-05 unpaid completed >= 5", len(unpaid) >= 5, f"{len(unpaid)} unpaid completed trips")
    except Exception as e:
        check("IS-05 operations.csv", False, str(e))

    # lora training data (optional)
    if os.path.exists("lora/train.jsonl"):
        try:
            with open("lora/train.jsonl") as f:
                train = [json.loads(l) for l in f if l.strip()]
            from collections import Counter
            counts = Counter(ex["output"] for ex in train)
            min_count = min(counts.values()) if counts else 0
            check("AO-01 training >= 10 per code", min_count >= 10, f"min per code: {min_count}")
            balanced = max(counts.values()) / min_count < 3 if min_count > 0 else False
            check("AO-01 training balanced (max/min < 3)", balanced, f"max={max(counts.values())}, min={min_count}")
        except Exception as e:
            check("AO-01 lora/train.jsonl", False, str(e))
    else:
        print("[SKIP] AO-01 lora/train.jsonl not found (run separately)")

    passes = sum(1 for s, _, _ in results if s == PASS)
    fails = sum(1 for s, _, _ in results if s == FAIL)
    print(f"\nSummary: {passes} PASS, {fails} FAIL")


if __name__ == "__main__":
    main()
