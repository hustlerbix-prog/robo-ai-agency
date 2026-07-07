#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Loading environment variables ==="
set -a
source "$LAB_DIR/.env"
set +a

echo "=== Activating virtual environment ==="
source ~/demo-env/bin/activate

cd "$LAB_DIR"

echo ""
echo "=== IS-05: Generating freight operations CSV (Faker, fast) ==="
python scripts/generate_is05_operations.py

echo ""
echo "=== IS-02: Generating invoices (fpdf2, fast) ==="
python scripts/generate_is02_invoices.py

echo ""
echo "=== IS-01: Generating property-management emails (Claude Haiku) ==="
python scripts/generate_is01_emails.py

echo ""
echo "=== IS-04: Generating legal intakes (Claude Haiku) ==="
python scripts/generate_is04_intakes.py

echo ""
echo "=== IS-03: Generating clinic procedures manual (Claude Opus, resumable) ==="
python scripts/generate_is03_chunked.py

echo ""
echo "=== All demo data generated! ==="
echo "Run 'python scripts/check_data_quality.py' to validate."
