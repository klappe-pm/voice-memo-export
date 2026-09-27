#!/usr/bin/env bash
# Compatibility wrapper that keeps the established import path while centralizing
# shared behavior in lib/guard-utils.sh.

set -u

_LOG_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=guard-utils.sh
source "$_LOG_LIB_DIR/guard-utils.sh"

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  level="${1:-info}"
  shift || true
  case "$level" in
    info) log_info "$*" ;;
    warn) log_warn "$*" ;;
    error) log_error "$*" ;;
    debug) log_debug "$*" ;;
    *) log_info "$level $*" ;;
  esac
fi
