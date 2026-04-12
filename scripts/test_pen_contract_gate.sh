#!/usr/bin/env bash
set -euo pipefail

pytest -q tests/pen_hair_v1/test_pen_hair_v1.py tests/pen_hair_v1/test_contract_freeze.py
