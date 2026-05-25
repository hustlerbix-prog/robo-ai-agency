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
echo "=== IS-01: Generating emails ==="
python scripts/generate_is01_emails.py

echo ""
echo "=== IS-02: Generating invoices ==="
python scripts/generate_is02_invoices.py

echo ""
echo "=== IS-03: Generating clinic procedures manual ==="
python scripts/generate_is03_procedures.py

echo ""
echo "=== IS-04: Generating legal intakes ==="
python scripts/generate_is04_intakes.py

echo ""
echo "=== IS-05: Generating operations CSV ==="
python scripts/generate_is05_operations.py

echo ""
echo "=== All demo data generated! ==="
echo "Run 'python scripts/check_data_quality.py' to validate."
