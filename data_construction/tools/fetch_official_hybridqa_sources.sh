#!/usr/bin/env bash
# Fetch and verify the official HybridQA question data and linked environment.
# The destination must be a machine-local directory outside the Git worktree.

set -euo pipefail

readonly script_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly project_root="$(cd -- "$script_directory/../.." && pwd -P)"
readonly HYBRIDQA_URL="https://github.com/wenhuchen/HybridQA.git"
readonly HYBRIDQA_COMMIT="db22fda8c5951438fade3c69d75b350335ba93b3"
readonly HYBRIDQA_TREE="1e1ef6a6168ef6c6cf362264d8f7b75859ce8fdf"
readonly WIKITABLES_URL="https://github.com/wenhuchen/WikiTables-WithLinks.git"
readonly WIKITABLES_COMMIT="dc066e1a6d5281511d8b73a6107d5ad2824cc2b2"
readonly WIKITABLES_TREE="b4f2d5e0eeb2d18cf95bf6e6a583bc499c53b68c"

destination=""
verify_only=false

usage() {
  printf '%s\n' \
    "Usage: $0 --dest <machine-local-cache-directory> [--verify-only]" \
    "" \
    "The command creates these children under --dest:" \
    "  HybridQA-db22fda" \
    "  WikiTables-WithLinks-dc066e1" \
    "" \
    "--verify-only performs no network access and requires both checkouts."
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

while (($#)); do
  case "$1" in
    --dest)
      (($# >= 2)) || die "--dest requires a value"
      destination="$2"
      shift 2
      ;;
    --verify-only)
      verify_only=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[[ -n "$destination" ]] || {
  usage >&2
  exit 2
}

command -v git >/dev/null || die "git is required"
command -v sha256sum >/dev/null || die "sha256sum is required"
command -v find >/dev/null || die "find is required"
command -v realpath >/dev/null || die "realpath is required"
command -v sort >/dev/null || die "sort is required"
command -v xargs >/dev/null || die "xargs is required"

destination="$(realpath -m -- "$destination")"
if [[ "$destination" == "$project_root" || "$destination" == "$project_root/"* ]]; then
  die "--dest must be outside the project worktree: $project_root"
fi
mkdir -p -- "$destination"
destination="$(cd -- "$destination" && pwd -P)"

readonly hybridqa_dir="$destination/HybridQA-db22fda"
readonly wikitables_dir="$destination/WikiTables-WithLinks-dc066e1"

prepare_checkout() {
  local label="$1"
  local url="$2"
  local commit="$3"
  local expected_tree="$4"
  local target="$5"
  local observed_remote
  local observed_head
  local observed_tree
  local checkout_was_created=false

  if [[ -e "$target" && ! -d "$target/.git" ]]; then
    die "$target exists but is not the expected Git checkout"
  fi

  if [[ ! -d "$target/.git" ]]; then
    "$verify_only" && die "$label checkout is absent in --verify-only mode: $target"
    git clone --filter=blob:none --no-checkout "$url" "$target"
    checkout_was_created=true
  fi

  observed_remote="$(git -C "$target" remote get-url origin)"
  if [[ "$observed_remote" != "$url" && "$observed_remote" != "${url%.git}" ]]; then
    die "$label origin mismatch: expected $url, observed $observed_remote"
  fi

  # A fresh --no-checkout clone reports every tracked path as deleted until its
  # first checkout.  Existing checkouts must still be clean before we mutate
  # them, but the just-created checkout is safe to populate below.
  if [[ "$checkout_was_created" == false ]] \
    && [[ -n "$(git -C "$target" status --porcelain --untracked-files=all)" ]]; then
    die "$label checkout has local changes; refusing to overwrite it: $target"
  fi

  if ! "$verify_only"; then
    git -C "$target" fetch --depth 1 origin "$commit"
  fi

  git -C "$target" cat-file -e "${commit}^{commit}" 2>/dev/null \
    || die "$label pinned commit is unavailable: $commit"

  if "$verify_only"; then
    observed_head="$(git -C "$target" rev-parse HEAD)"
    [[ "$observed_head" == "$commit" ]] \
      || die "$label HEAD is not pinned in --verify-only mode: expected $commit, observed $observed_head"
  else
    git -C "$target" checkout --detach "$commit"
  fi

  observed_head="$(git -C "$target" rev-parse HEAD)"
  [[ "$observed_head" == "$commit" ]] \
    || die "$label HEAD mismatch: expected $commit, observed $observed_head"

  observed_tree="$(git -C "$target" show -s --format=%T HEAD)"
  [[ "$observed_tree" == "$expected_tree" ]] \
    || die "$label root tree mismatch: expected $expected_tree, observed $observed_tree"
}

check_sha256() {
  local expected="$1"
  local path="$2"
  local observed

  [[ -f "$path" ]] || die "required artifact is missing: $path"
  read -r observed _ < <(sha256sum -- "$path")
  [[ "$observed" == "$expected" ]] \
    || die "SHA-256 mismatch for $path: expected $expected, observed $observed"
}

check_git_tree() {
  local repository="$1"
  local expression="$2"
  local expected="$3"
  local observed

  observed="$(git -C "$repository" rev-parse "$expression")"
  [[ "$observed" == "$expected" ]] \
    || die "Git tree mismatch for $expression: expected $expected, observed $observed"
}

canonical_content_list_sha256() {
  local repository="$1"
  local relative_directory="$2"

  (
    cd -- "$repository"
    find "$relative_directory" -maxdepth 1 -type f -name '*.json' -print0 \
      | LC_ALL=C sort -z \
      | xargs -0 sha256sum \
      | sha256sum \
      | awk '{print $1}'
  )
}

check_directory() {
  local repository="$1"
  local relative_directory="$2"
  local expected_count="$3"
  local expected_hash="$4"
  local observed_count
  local observed_hash

  [[ -d "$repository/$relative_directory" ]] \
    || die "required directory is missing: $repository/$relative_directory"
  observed_count="$(find "$repository/$relative_directory" -maxdepth 1 -type f -name '*.json' | wc -l)"
  [[ "$observed_count" -eq "$expected_count" ]] \
    || die "file-count mismatch for $relative_directory: expected $expected_count, observed $observed_count"
  observed_hash="$(canonical_content_list_sha256 "$repository" "$relative_directory")"
  [[ "$observed_hash" == "$expected_hash" ]] \
    || die "content-list hash mismatch for $relative_directory: expected $expected_hash, observed $observed_hash"
}

prepare_checkout \
  "HybridQA" "$HYBRIDQA_URL" "$HYBRIDQA_COMMIT" "$HYBRIDQA_TREE" "$hybridqa_dir"
prepare_checkout \
  "WikiTables-WithLinks" "$WIKITABLES_URL" "$WIKITABLES_COMMIT" "$WIKITABLES_TREE" "$wikitables_dir"

check_git_tree "$hybridqa_dir" \
  "$HYBRIDQA_COMMIT:released_data" "e3746c1ae9de9b8ecc85f8a6326faa1edf58a90f"
check_sha256 "b33aa73638959a2383e1e1638fd6abe87818b7379c7a42eac1621475d2d959e2" \
  "$hybridqa_dir/released_data/train.json"
check_sha256 "424272b233735a70ed8ef5af4a615373d114f472168c686c4370d54c92d58ac1" \
  "$hybridqa_dir/released_data/dev.json"
check_sha256 "41845fec9cba21979e663a96626c2880adbf2d26b5667ea7d0bf61fab0cdc356" \
  "$hybridqa_dir/released_data/test.json"
check_sha256 "5008fc2e4b8859f729201fe4a45800dba95686ab5cde5a9f1a66b5794e27fd5b" \
  "$hybridqa_dir/released_data/train.traced.json"
check_sha256 "2fe4ca01e23d4e589ee6a79f46d7eeeddefd1d33a581c7ceb8955902da3f19c1" \
  "$hybridqa_dir/released_data/dev.traced.json"
check_sha256 "617cd141a09550e85a0634b68b2e16727a87f9a6005002d31f40d839dfa389ed" \
  "$hybridqa_dir/released_data/dev_reference.json"

check_git_tree "$wikitables_dir" \
  "$WIKITABLES_COMMIT:tables_tok" "772e97624b08e0bd5534b8991a8c2dd8fb6b153f"
check_git_tree "$wikitables_dir" \
  "$WIKITABLES_COMMIT:request_tok" "f1c1a1dab31b2341f338a6a7bf626b5b8c569f20"
check_sha256 "3320a9457ae6ebcdb80ee8b47a7fb20cd657dece67f6dad60ebf189ee90763d8" \
  "$wikitables_dir/orig_id_to_uid.json"
check_directory "$wikitables_dir" "tables_tok" 15316 \
  "3969fcf6c0192d6085ad999e3abd41f0039a73c878ffd30d7cd8b7786ea62c92"
check_directory "$wikitables_dir" "request_tok" 15316 \
  "bc289b9aa6d397369b44cbf9b54250539a5a0cf01287f94c9a5572e79e8cd916"

printf 'Verified official HybridQA source at commit %s\n' "$HYBRIDQA_COMMIT"
printf 'Verified official linked environment at commit %s\n' "$WIKITABLES_COMMIT"
printf 'Machine-local source root: %s\n' "$destination"
