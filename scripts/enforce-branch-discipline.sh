#!/usr/bin/env bash
set -u

usage() {
  cat <<'USAGE'
Usage: scripts/enforce-branch-discipline.sh [--branch <name>] [--allow-primary] [--require-upstream]

Refuses implementation work on main/master unless --allow-primary is explicit.
USAGE
}

BRANCH=""
ALLOW_PRIMARY=0
REQUIRE_UPSTREAM=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --branch)
      shift
      if [ "$#" -eq 0 ]; then
        echo "missing value for --branch" >&2
        exit 2
      fi
      BRANCH="$1"
      ;;
    --allow-primary)
      ALLOW_PRIMARY=1
      ;;
    --require-upstream)
      REQUIRE_UPSTREAM=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [ -z "$BRANCH" ]; then
  BRANCH="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
fi

if [ -z "$BRANCH" ]; then
  echo "branch discipline failed: detached HEAD or no git branch detected" >&2
  exit 2
fi

case "$BRANCH" in
  main|master)
    if [ "$ALLOW_PRIMARY" -ne 1 ]; then
      echo "branch discipline failed: '$BRANCH' is integration-only; create a feature branch before implementation work" >&2
      exit 2
    fi
    ;;
esac

if [ "$REQUIRE_UPSTREAM" -eq 1 ]; then
  if ! git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
    echo "branch discipline failed: '$BRANCH' has no upstream; push with 'git push -u origin $BRANCH' before handoff" >&2
    exit 2
  fi
fi

echo "branch discipline ok: $BRANCH"
