#!/usr/bin/env bash

# WezTerm project initializer: auto-activate this repo's conda environment.
if [[ "${CONDA_DEFAULT_ENV:-}" == "phd-cv" ]]; then
  return 0 2>/dev/null || exit 0
fi

if ! command -v conda >/dev/null 2>&1; then
  return 0 2>/dev/null || exit 0
fi

if ! declare -F conda >/dev/null 2>&1; then
  __conda_hook="$(conda shell.bash hook 2>/dev/null)" || true
  if [[ -n "${__conda_hook}" ]]; then
    eval "${__conda_hook}"
  fi
  unset __conda_hook
fi

if declare -F conda >/dev/null 2>&1; then
  conda activate phd-cv >/dev/null 2>&1 || \
    echo "[wezterm-init] Failed to activate conda env 'phd-cv'" >&2
fi
