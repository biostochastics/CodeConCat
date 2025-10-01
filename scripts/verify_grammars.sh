#!/bin/bash
# scripts/verify_grammars.sh
# Grammar verification script for codeconcat language expansion
# Verifies that all required tree-sitter grammars are available

set -e  # Exit on error

echo "Verifying tree-sitter grammar availability..."
echo "=============================================="

# Current supported languages (v0.8.5)
CURRENT_LANGUAGES=(
  python c cpp csharp java javascript typescript go rust php swift julia bash r
)

# Tier 1: Critical Languages (v0.9.0 target)
TIER1_LANGUAGES=(
  kotlin dart sql hcl graphql ruby solidity
)

# Tier 2: High-Value Languages (v0.10.0 target)
TIER2_LANGUAGES=(
  glsl hlsl metal wasm zig elixir crystal
)

# Tier 3: Specialized Languages (v0.11.0 target)
TIER3_LANGUAGES=(
  ocaml rescript reason lean coq haxe v scala
)

# Tier 4: Niche Languages (v0.12.0 target)
TIER4_LANGUAGES=(
  nim nix vala astro
)

# Combine all languages based on tier flag
ALL_LANGUAGES=("${CURRENT_LANGUAGES[@]}")

# Parse command line arguments
TIER="current"
VERBOSE=false
EXIT_ON_ERROR=true

while [[ $# -gt 0 ]]; do
  case $1 in
    --tier)
      TIER="$2"
      shift 2
      ;;
    --all)
      TIER="all"
      shift
      ;;
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --no-exit)
      EXIT_ON_ERROR=false
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --tier TIER      Verify specific tier: current, tier1, tier2, tier3, tier4, all"
      echo "  --all            Verify all languages across all tiers"
      echo "  --verbose, -v    Show detailed output"
      echo "  --no-exit        Don't exit on first error (report all missing grammars)"
      echo "  --help, -h       Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0                    # Verify current languages only"
      echo "  $0 --tier tier1       # Verify Tier 1 languages"
      echo "  $0 --all              # Verify all languages"
      echo "  $0 --all --no-exit    # Report all missing grammars"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Select languages based on tier
case $TIER in
  current)
    LANGUAGES_TO_CHECK=("${CURRENT_LANGUAGES[@]}")
    echo "Checking current languages (v0.8.5)..."
    ;;
  tier1)
    LANGUAGES_TO_CHECK=("${CURRENT_LANGUAGES[@]}" "${TIER1_LANGUAGES[@]}")
    echo "Checking current + Tier 1 languages (v0.9.0 target)..."
    ;;
  tier2)
    LANGUAGES_TO_CHECK=("${CURRENT_LANGUAGES[@]}" "${TIER1_LANGUAGES[@]}" "${TIER2_LANGUAGES[@]}")
    echo "Checking current + Tier 1 + Tier 2 languages (v0.10.0 target)..."
    ;;
  tier3)
    LANGUAGES_TO_CHECK=("${CURRENT_LANGUAGES[@]}" "${TIER1_LANGUAGES[@]}" "${TIER2_LANGUAGES[@]}" "${TIER3_LANGUAGES[@]}")
    echo "Checking current + Tier 1-3 languages (v0.11.0 target)..."
    ;;
  tier4|all)
    LANGUAGES_TO_CHECK=("${CURRENT_LANGUAGES[@]}" "${TIER1_LANGUAGES[@]}" "${TIER2_LANGUAGES[@]}" "${TIER3_LANGUAGES[@]}" "${TIER4_LANGUAGES[@]}")
    echo "Checking all languages (v0.12.0 target)..."
    ;;
  *)
    echo "Error: Unknown tier '$TIER'"
    echo "Valid tiers: current, tier1, tier2, tier3, tier4, all"
    exit 1
    ;;
esac

echo ""

# Track failures
FAILED_LANGUAGES=()
TOTAL_CHECKED=0
SUCCESSFUL=0

# Test each language
for lang in "${LANGUAGES_TO_CHECK[@]}"; do
  TOTAL_CHECKED=$((TOTAL_CHECKED + 1))

  if [ "$VERBOSE" = true ]; then
    echo -n "Testing $lang... "
  else
    echo -n "."
  fi

  # Try to load the grammar using tree-sitter-language-pack
  # Use python from activated environment (works in both local and CI)
  if command -v python &> /dev/null; then
    PYTHON_CMD="python"
  else
    PYTHON_CMD="python3"
  fi

  if $PYTHON_CMD -c "
from tree_sitter_language_pack import get_language
try:
    lang = get_language('$lang')
    exit(0)
except Exception:
    exit(1)
" 2>/dev/null; then
    SUCCESSFUL=$((SUCCESSFUL + 1))
    if [ "$VERBOSE" = true ]; then
      echo "✓ OK"
    fi
  else
    FAILED_LANGUAGES+=("$lang")
    if [ "$VERBOSE" = true ]; then
      echo "✗ FAILED"
    fi
    if [ "$EXIT_ON_ERROR" = true ]; then
      echo ""
      echo ""
      echo "❌ Grammar verification failed!"
      echo "Language '$lang' grammar not found or failed to load."
      echo ""
      echo "This may indicate:"
      echo "  1. The grammar is not available in tree-sitter-language-pack"
      echo "  2. The language name is incorrect"
      echo "  3. tree-sitter-language-pack needs to be updated"
      echo ""
      echo "Please check:"
      echo "  - tree-sitter-language-pack is installed: pip install tree-sitter-language-pack"
      echo "  - Version is >= 0.7.2"
      echo "  - Language name matches tree-sitter-language-pack conventions"
      exit 1
    fi
  fi
done

echo ""
echo ""
echo "=============================================="
echo "Grammar Verification Complete"
echo "=============================================="
echo "Total checked: $TOTAL_CHECKED"
echo "Successful: $SUCCESSFUL"
echo "Failed: ${#FAILED_LANGUAGES[@]}"
echo ""

if [ ${#FAILED_LANGUAGES[@]} -gt 0 ]; then
  echo "⚠️  Failed languages:"
  for lang in "${FAILED_LANGUAGES[@]}"; do
    echo "  - $lang"
  done
  echo ""
  echo "❌ Grammar verification completed with errors"
  exit 1
else
  echo "✅ All grammars verified successfully!"
  exit 0
fi
