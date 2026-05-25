import os
import json
import random
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

COST_CODES = [
    ("MFG-MAT", "Manufacturing Materials — raw materials, components, and manufacturing supplies"),
    ("MFG-EQP", "Manufacturing Equipment — machinery, tools, and production equipment"),
    ("MFG-MNT", "Manufacturing Maintenance — repairs and maintenance of production assets"),
    ("LOG-FRT", "Logistics Freight — shipping, transportation, and freight costs"),
    ("LOG-PKG", "Logistics Packaging — packaging materials and labeling"),
    ("ADM-OFF", "Administrative Office — office supplies and general admin expenses"),
    ("ADM-SVC", "Administrative Services — professional services, consulting, subscriptions"),
    ("ADM-TRV", "Administrative Travel — travel, accommodation, and per diem"),
    ("IT-HRD", "IT Hardware — computers, servers, and physical IT equipment"),
    ("IT-SFT", "IT Software — software licenses, SaaS subscriptions, and digital tools"),
]


def generate_batch(code, description, batch_num):
    prompt = f"""Generate 10 unique expense line item descriptions that should be classified as cost code {code}: {description}.

Batch {batch_num} — make these different from typical examples.

Return ONLY a JSON array of 10 objects with this exact format:
[
  {{"instruction": "Classify the following expense into the correct cost code.", "input": "expense description here", "output": "{code}"}},
  ...
]

Make descriptions realistic, varied (mix of vendors, amounts mentioned in text, partial info), and sometimes ambiguous but clearly fitting {code}."""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    text = msg.content[0].text.strip()
    start = text.find("[")
    end = text.rfind("]") + 1
    return json.loads(text[start:end])


def main():
    os.makedirs("lora", exist_ok=True)
    all_examples = []

    for code, description in COST_CODES:
        print(f"Generating examples for {code}...")
        for batch in range(1, 3):
            examples = generate_batch(code, description, batch)
            all_examples.extend(examples)
            print(f"  Batch {batch}: {len(examples)} examples")

    random.shuffle(all_examples)

    split = int(len(all_examples) * 0.8)
    train = all_examples[:split]
    test = all_examples[split:]

    with open("lora/train.jsonl", "w") as f:
        for ex in train:
            f.write(json.dumps(ex) + "\n")

    with open("lora/test.jsonl", "w") as f:
        for ex in test:
            f.write(json.dumps(ex) + "\n")

    with open("lora/full_dataset.json", "w") as f:
        json.dump(all_examples, f, indent=2)

    print(f"\nTotal: {len(all_examples)} | Train: {len(train)} | Test: {len(test)}")
    print("Saved: lora/train.jsonl, lora/test.jsonl, lora/full_dataset.json")


if __name__ == "__main__":
    main()
