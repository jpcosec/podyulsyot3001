#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

usage() {
  cat <<'EOF'
Usage:
  scripts/run_prep_match_langsmith.sh --job-id <job_id> --source-url <url> --profile-evidence <path> [options]

Required:
  --job-id <job_id>

Required for non-resume runs:
  --source-url <url>
  --profile-evidence <path>

Options:
  --source <source>            Default: tu_berlin
  --run-id <run_id>            Default: run-cli
  --checkpoint-db <path>       Optional sqlite checkpoint path
  --resume                     Resume checkpointed run
  -h, --help                   Show this help

Environment:
  LANGSMITH_API_KEY            Required
  LANGSMITH_PROJECT            Optional (defaulted to phd-20 if unset)
  LANGSMITH_ENDPOINT           Optional

Example:
  LANGSMITH_API_KEY=<key> scripts/run_prep_match_langsmith.sh \
    --source tu_berlin \
    --job-id 201399 \
    --source-url "https://example.org/job" \
    --profile-evidence data/reference_data/profile/evidence.json
EOF
}

SOURCE="tu_berlin"
JOB_ID=""
RUN_ID="run-cli"
SOURCE_URL=""
PROFILE_EVIDENCE=""
CHECKPOINT_DB=""
RESUME=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      SOURCE="$2"
      shift 2
      ;;
    --job-id)
      JOB_ID="$2"
      shift 2
      ;;
    --run-id)
      RUN_ID="$2"
      shift 2
      ;;
    --source-url)
      SOURCE_URL="$2"
      shift 2
      ;;
    --profile-evidence)
      PROFILE_EVIDENCE="$2"
      shift 2
      ;;
    --checkpoint-db)
      CHECKPOINT_DB="$2"
      shift 2
      ;;
    --resume)
      RESUME=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$JOB_ID" ]]; then
  echo "--job-id is required" >&2
  usage
  exit 1
fi

if [[ -z "${LANGSMITH_API_KEY:-}" ]]; then
  echo "LANGSMITH_API_KEY is required" >&2
  exit 1
fi

export LANGSMITH_PROJECT="${LANGSMITH_PROJECT:-phd-20}"

CMD=(
  python -m src.cli.run_prep_match
  --source "$SOURCE"
  --job-id "$JOB_ID"
  --run-id "$RUN_ID"
  --langsmith-verifiable
)

if [[ -n "$CHECKPOINT_DB" ]]; then
  CMD+=(--checkpoint-db "$CHECKPOINT_DB")
fi

if [[ "$RESUME" -eq 1 ]]; then
  CMD+=(--resume)
else
  if [[ -z "$SOURCE_URL" || -z "$PROFILE_EVIDENCE" ]]; then
    echo "--source-url and --profile-evidence are required unless --resume is set" >&2
    usage
    exit 1
  fi
  CMD+=(--source-url "$SOURCE_URL" --profile-evidence "$PROFILE_EVIDENCE")
fi

cd "$REPO_ROOT"
"${CMD[@]}"
