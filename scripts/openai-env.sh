#!/usr/bin/env bash

set -euo pipefail

if [[ -n "${OPENAI_API_KEY:-}" ]]; then
    return 0 2>/dev/null || exit 0
fi

token_file="${OPENAI_TOKEN_FILE:-$HOME/.config/openai/token.txt}"

if [[ -f "$token_file" ]]; then
    OPENAI_API_KEY="$(tr -d '\r\n' < "$token_file")"
    export OPENAI_API_KEY
    return 0 2>/dev/null || exit 0
fi

if [[ "${MULTIQC_REQUIRE_OPENAI_TOKEN_FILE:-0}" == "1" ]]; then
    echo "OPENAI_API_KEY is unset and token file does not exist: $token_file" >&2
    exit 1
fi
