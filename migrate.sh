#!/usr/bin/env bash
set -euo pipefail

exec alembic upgrade head
