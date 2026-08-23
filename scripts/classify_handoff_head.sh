#!/bin/sh

# Classify the relationship between a recorded handoff baseline and a Git HEAD.
# Exit 0: exact or linear descendant; exit 2: unavailable/diverged; exit 1: check failure.

set -u

if [ "$#" -ne 3 ]; then
    printf '%s\n' 'error:usage'
    exit 1
fi

repository=$1
expected_head=$2
current_head=$3

if ! printf '%s\n' "$expected_head" | grep -Eq '^[0-9a-f]{40}$'; then
    printf '%s\n' 'invalid-baseline'
    exit 2
fi

if ! git -C "$repository" cat-file -e "$expected_head^{commit}" 2>/dev/null; then
    printf '%s\n' 'missing-baseline'
    exit 2
fi

if ! git -C "$repository" cat-file -e "$current_head^{commit}" 2>/dev/null; then
    printf '%s\n' 'error:current-head-unavailable'
    exit 1
fi

if [ "$current_head" = "$expected_head" ]; then
    printf '%s\n' 'exact'
    exit 0
fi

git -C "$repository" merge-base --is-ancestor "$expected_head" "$current_head" 2>/dev/null
relation_rc=$?
case "$relation_rc" in
    0)
        distance=$(git -C "$repository" rev-list --count "$expected_head..$current_head" 2>/dev/null) || {
            printf '%s\n' 'error:distance-unavailable'
            exit 1
        }
        printf 'descendant:%s\n' "$distance"
        exit 0
        ;;
    1)
        printf '%s\n' 'diverged'
        exit 2
        ;;
    *)
        printf '%s\n' 'error:merge-base-failed'
        exit 1
        ;;
esac
