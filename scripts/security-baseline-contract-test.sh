#!/usr/bin/env bash

set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly repository_root
workflow="$repository_root/.github/workflows/Toolkit-Security.yml"

fail() {
  printf 'security baseline contract: %s\n' "$*" >&2
  exit 1
}

assert_workflow_count() {
  local expected="$1" needle="$2" actual
  actual="$(grep -F -c -- "$needle" "$workflow" || true)"
  [ "$actual" -eq "$expected" ] ||
    fail "expected $expected workflow occurrences of $needle, found $actual"
}

# Keep both production matchers (gosec and Semgrep/OpenGrep) on the same
# rule/path/snippet identity. Line remains available only for diagnostics.
assert_workflow_count 2 '| unique_by([.rule_id, .path, .snippet])'
# The dollar signs below are literal jq variables expected in the workflow.
# shellcheck disable=SC2016
assert_workflow_count 2 '.rule_id == $finding.rule_id and'
# shellcheck disable=SC2016
assert_workflow_count 2 '.path == $finding.path and'
# shellcheck disable=SC2016
assert_workflow_count 2 '.snippet == $finding.snippet'
# shellcheck disable=SC2016
assert_workflow_count 0 '($known | index($finding))'

test_root="$(mktemp -d "${TMPDIR:-/tmp}/security-baseline-contract.XXXXXX")"
readonly test_root
cleanup() {
  rm -rf -- "$test_root"
}
trap cleanup EXIT INT TERM

baseline="$test_root/baseline.json"
sarif="$test_root/findings.sarif"
output="$test_root/output.json"

jq -n '{
  schema_version: 1,
  gosec: [{
    rule_id: "G115",
    path: "internal/example.go",
    line: 10,
    snippet: "value := uint64(size)"
  }],
  semgrep: [],
  opengrep: []
}' > "$baseline"

jq -n '{
  runs: [{
    results: [
      {
        ruleId: "G115",
        message: {text: "integer overflow conversion"},
        locations: [{physicalLocation: {
          artifactLocation: {uri: "internal/example.go"},
          region: {startLine: 42, snippet: {text: "value := uint64(size)"}}
        }}]
      },
      {
        ruleId: "G115",
        message: {text: "duplicate identity on another line"},
        locations: [{physicalLocation: {
          artifactLocation: {uri: "internal/example.go"},
          region: {startLine: 43, snippet: {text: "value := uint64(size)"}}
        }}]
      }
    ]
  }]
}' > "$sarif"

compare_sarif() {
  local report="$1"
  jq --arg tool gosec --slurpfile baseline "$baseline" '
    [
      .runs[]?.results[]?
      | {
          rule_id: (.ruleId // ""),
          path: (.locations[0].physicalLocation.artifactLocation.uri // ""),
          line: (.locations[0].physicalLocation.region.startLine // 0),
          snippet: (.locations[0].physicalLocation.region.snippet.text // "")
        }
    ]
    | sort_by(.rule_id, .path, .snippet, .line)
    | unique_by([.rule_id, .path, .snippet])
    | . as $current
    | ($baseline[0][$tool] // []) as $known
    | {
        current_count: ($current | length),
        new: [
          $current[]
          | select(
              . as $finding
              | (any($known[]?;
                  .rule_id == $finding.rule_id and
                  .path == $finding.path and
                  .snippet == $finding.snippet
                ) | not)
            )
        ]
      }
  ' "$report" > "$output"
}

compare_sarif "$sarif"
[ "$(jq -r '.current_count' "$output")" -eq 1 ] ||
  fail 'duplicate rule/path/snippet identities were not collapsed'
[ "$(jq -r '.new | length' "$output")" -eq 0 ] ||
  fail 'line-only movement did not match the reviewed baseline finding'

jq '.runs[0].results[0].locations[0].physicalLocation.region.snippet.text = "value := uint32(size)"
    | .runs[0].results = [ .runs[0].results[0] ]' "$sarif" > "$test_root/snippet-drift.sarif"
compare_sarif "$test_root/snippet-drift.sarif"
[ "$(jq -r '.new | length' "$output")" -eq 1 ] ||
  fail 'snippet changes must require renewed review'

printf 'security baseline contract passed (rule/path/snippet identity; line is diagnostic)\n'
