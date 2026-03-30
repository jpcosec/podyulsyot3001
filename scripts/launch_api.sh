#!/bin/bash
# scripts/launch_api.sh - Smart API launcher

set -e

python3 -m src.cli.main api start
