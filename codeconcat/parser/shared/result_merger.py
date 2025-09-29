"""Intelligent result merger for combining outputs from multiple parsers.

This module solves the critical issue where the unified pipeline picks a single
winner (line 537 break) instead of merging results, potentially losing declarations
that only one parser can find.

Provides multiple merge strategies:
- CONFIDENCE_WEIGHTED: Weight by parser confidence scores
- FEATURE_UNION: Union all detected features
- MAJORITY_VOTE: Consensus on conflicts (future)
- FAST_FAIL: First high-confidence wins
"""

import logging
from dataclasses import replace
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from codeconcat.base_types import Declaration, ParseResult

logger = logging.getLogger(__name__)


class MergeStrategy(Enum):
    """Strategies for merging parse results from multiple parsers."""

    CONFIDENCE_WEIGHTED = "confidence"  # Weight by parser confidence
    FEATURE_UNION = "union"  # Union all detected features
    FAST_FAIL = "fast_fail"  # First high-confidence wins (legacy behavior)
    BEST_OF_BREED = "best_of_breed"  # Pick best parser per feature type


class ResultMerger:
    """Merge results from multiple parsers intelligently.

    Eliminates the limitation where unified_pipeline.py:537 breaks after
    first successful parse, losing potential declarations from other parsers.
    """

    # Confidence thresholds for different merge strategies
    HIGH_CONFIDENCE_THRESHOLD = 0.8
    MEDIUM_CONFIDENCE_THRESHOLD = 0.5

    @staticmethod
    def merge_parse_results(
        results: List[ParseResult],
        strategy: MergeStrategy = MergeStrategy.CONFIDENCE_WEIGHTED,
        language: Optional[str] = None,
    ) -> ParseResult:
        """Merge multiple parse results using the specified strategy.

        Args:
            results: List of ParseResult objects to merge
            strategy: Merge strategy to use
            language: Programming language (for language-specific optimizations)

        Returns:
            Merged ParseResult combining best aspects of all inputs

        Complexity: O(n*m) where n is number of results, m is avg declarations per result
        """
        if not results:
            return ParseResult(declarations=[], imports=[])

        if len(results) == 1:
            return results[0]

        # Filter out results with errors unless all have errors
        valid_results = [r for r in results if not r.error]
        if not valid_results:
            # All have errors, return the one with most declarations
            return max(results, key=lambda r: len(r.declarations))

        # Apply merge strategy
        if strategy == MergeStrategy.CONFIDENCE_WEIGHTED:
            return ResultMerger._merge_confidence_weighted(valid_results, language)
        elif strategy == MergeStrategy.FEATURE_UNION:
            return ResultMerger._merge_feature_union(valid_results)
        elif strategy == MergeStrategy.FAST_FAIL:
            return ResultMerger._merge_fast_fail(valid_results)
        elif strategy == MergeStrategy.BEST_OF_BREED:
            return ResultMerger._merge_best_of_breed(valid_results)
        else:
            logger.warning(f"Unknown merge strategy: {strategy}, using CONFIDENCE_WEIGHTED")
            return ResultMerger._merge_confidence_weighted(valid_results, language)

    @staticmethod
    def _merge_confidence_weighted(
        results: List[ParseResult],
        language: Optional[str] = None,  # noqa: ARG004
    ) -> ParseResult:
        """Merge results weighted by confidence scores.

        High-confidence results contribute more to the merged output.
        Declarations from all parsers are included, with priority given to
        higher-confidence parsers in case of conflicts.

        Args:
            results: List of valid ParseResult objects
            language: Programming language

        Returns:
            Merged ParseResult
        """
        # Calculate or assign confidence scores
        scored_results = []
        for result in results:
            confidence = result.confidence_score or ResultMerger._calculate_confidence(result)
            scored_results.append((confidence, result))

        # Sort by confidence (highest first)
        scored_results.sort(key=lambda x: x[0], reverse=True)

        # Start with highest confidence result as base
        best_confidence, base_result = scored_results[0]
        logger.debug(
            f"Merging {len(results)} results, base confidence: {best_confidence:.2f}, "
            f"base parser: {base_result.parser_type or base_result.engine_used}"
        )

        # Create mutable copies of lists
        merged_declarations = list(base_result.declarations)
        merged_imports = list(base_result.imports)
        merged_missed_features = list(base_result.missed_features)
        merged_security_issues = list(base_result.security_issues)

        # Track declaration signatures to avoid duplicates
        seen_signatures = {ResultMerger._get_declaration_signature(d) for d in merged_declarations}

        # Merge in declarations from other parsers
        for confidence, result in scored_results[1:]:
            for decl in result.declarations:
                sig = ResultMerger._get_declaration_signature(decl)
                if sig not in seen_signatures:
                    merged_declarations.append(decl)
                    seen_signatures.add(sig)
                    logger.debug(
                        f"Added declaration '{decl.name}' from "
                        f"{result.parser_type or result.engine_used} (confidence: {confidence:.2f})"
                    )

            # Merge imports (union)
            for imp in result.imports:
                if imp not in merged_imports:
                    merged_imports.append(imp)

            # Update missed features (intersection - only keep if all parsers missed it)
            merged_missed_features = [
                f for f in merged_missed_features if f in result.missed_features
            ]

            # Merge security issues
            for issue in result.security_issues:
                if issue not in merged_security_issues:
                    merged_security_issues.append(issue)

        # Create merged result
        merged = replace(
            base_result,
            declarations=merged_declarations,
            imports=sorted(set(merged_imports)),
            missed_features=merged_missed_features,
            security_issues=merged_security_issues,
            confidence_score=best_confidence,
            parser_quality="merged",
            engine_used="merged:"
            + "+".join(r.parser_type or r.engine_used for _, r in scored_results),
        )

        logger.info(
            f"Merged {len(results)} results: {len(merged_declarations)} total declarations, "
            f"{len(merged_imports)} imports"
        )

        return merged

    @staticmethod
    def _merge_feature_union(results: List[ParseResult]) -> ParseResult:
        """Merge results by taking union of all features.

        This strategy maximizes coverage by including declarations from
        all parsers, regardless of confidence. Good for TypeScript where
        enhanced parsers might catch features tree-sitter misses.

        Args:
            results: List of valid ParseResult objects

        Returns:
            Merged ParseResult with union of all features
        """
        # Start with the result that has most declarations
        base_result = max(results, key=lambda r: len(r.declarations))

        all_declarations = []
        all_imports = []
        all_security_issues = []
        seen_signatures: Set[str] = set()

        # Collect all unique declarations
        for result in results:
            for decl in result.declarations:
                sig = ResultMerger._get_declaration_signature(decl)
                if sig not in seen_signatures:
                    all_declarations.append(decl)
                    seen_signatures.add(sig)

            # Union imports
            for imp in result.imports:
                if imp not in all_imports:
                    all_imports.append(imp)

            # Union security issues
            for issue in result.security_issues:
                if issue not in all_security_issues:
                    all_security_issues.append(issue)

        # Missed features: intersection (only if all parsers missed it)
        missed_features = set(results[0].missed_features)
        for result in results[1:]:
            missed_features &= set(result.missed_features)

        # Create merged result
        merged = replace(
            base_result,
            declarations=all_declarations,
            imports=sorted(set(all_imports)),
            missed_features=list(missed_features),
            security_issues=all_security_issues,
            parser_quality="union",
            engine_used="union:" + "+".join(r.parser_type or r.engine_used for r in results),
        )

        logger.info(
            f"Union merge: {len(all_declarations)} declarations from {len(results)} parsers"
        )

        return merged

    @staticmethod
    def _merge_fast_fail(results: List[ParseResult]) -> ParseResult:
        """Legacy fast-fail strategy: first high-confidence result wins.

        This replicates the old pipeline behavior but with confidence awareness.

        Args:
            results: List of valid ParseResult objects

        Returns:
            First high-confidence result or best available
        """
        for result in results:
            confidence = result.confidence_score or ResultMerger._calculate_confidence(result)
            if confidence >= ResultMerger.HIGH_CONFIDENCE_THRESHOLD:
                logger.debug(
                    f"Fast-fail: using {result.parser_type or result.engine_used} "
                    f"(confidence: {confidence:.2f})"
                )
                return result

        # No high-confidence result, return best available
        best = max(results, key=lambda r: ResultMerger._calculate_confidence(r))
        logger.debug("Fast-fail: no high-confidence result, using best available")
        return best

    @staticmethod
    def _merge_best_of_breed(results: List[ParseResult]) -> ParseResult:
        """Pick best parser for each feature type.

        Example: tree-sitter for functions, enhanced for complex class hierarchies

        Args:
            results: List of valid ParseResult objects

        Returns:
            Merged result combining best features from each parser
        """
        # Group declarations by kind
        decls_by_kind: Dict[str, List[Tuple[Declaration, str]]] = {}

        for result in results:
            parser_id = result.parser_type or result.engine_used
            for decl in result.declarations:
                kind = decl.kind
                if kind not in decls_by_kind:
                    decls_by_kind[kind] = []
                decls_by_kind[kind].append((decl, parser_id))

        # For each kind, pick the most complete declarations
        best_declarations = []
        seen_signatures: Set[str] = set()

        for _kind, decl_list in decls_by_kind.items():
            # Sort by completeness (has docstring, signature, modifiers, etc.)
            decl_list.sort(
                key=lambda x: (
                    bool(x[0].docstring),
                    bool(x[0].signature),
                    len(x[0].modifiers),
                    len(x[0].children),
                ),
                reverse=True,
            )

            # Take unique declarations (by signature)
            for decl, _parser_id in decl_list:
                sig = ResultMerger._get_declaration_signature(decl)
                if sig not in seen_signatures:
                    best_declarations.append(decl)
                    seen_signatures.add(sig)

        # Use first result as base, replace declarations
        base_result = results[0]

        # Merge imports from all
        all_imports = []
        for result in results:
            all_imports.extend(result.imports)

        merged = replace(
            base_result,
            declarations=best_declarations,
            imports=sorted(set(all_imports)),
            parser_quality="best_of_breed",
            engine_used="best_of_breed:"
            + "+".join(r.parser_type or r.engine_used for r in results),
        )

        logger.info(f"Best-of-breed merge: {len(best_declarations)} declarations selected")

        return merged

    @staticmethod
    def _get_declaration_signature(decl: Declaration) -> str:
        """Generate unique signature for a declaration to detect duplicates.

        Args:
            decl: Declaration object

        Returns:
            Unique signature string

        Complexity: O(1)
        """
        # Combine kind, name, and location for uniqueness
        return f"{decl.kind}:{decl.name}:{decl.start_line}-{decl.end_line}"

    @staticmethod
    def _calculate_confidence(result: ParseResult) -> float:
        """Calculate confidence score for a parse result.

        Factors:
        - Parser quality (full > partial > basic)
        - Number of declarations found
        - Presence of errors
        - Completeness of declarations (docstrings, signatures)

        Args:
            result: ParseResult to score

        Returns:
            Confidence score between 0.0 and 1.0

        Complexity: O(n) where n is number of declarations
        """
        if result.error:
            return 0.3  # Low confidence if errors present

        score = 0.0

        # Base score from parser quality
        quality_scores = {
            "full": 0.4,
            "partial": 0.25,
            "basic": 0.15,
            "unknown": 0.1,
        }
        score += quality_scores.get(result.parser_quality, 0.1)

        # Score from number of declarations (diminishing returns)
        decl_count = len(result.declarations)
        if decl_count > 0:
            # Log scale: sqrt to prevent over-weighting large files
            import math

            score += min(0.3, 0.05 * math.sqrt(decl_count))

        # Bonus for complete declarations
        if result.declarations:
            complete_count = sum(
                1 for d in result.declarations if d.docstring or d.signature or d.modifiers
            )
            completeness_ratio = complete_count / len(result.declarations)
            score += 0.2 * completeness_ratio

        # Bonus for imports found
        if result.imports:
            score += min(0.1, 0.01 * len(result.imports))

        # Penalty for missed features
        if result.missed_features:
            score -= min(0.15, 0.03 * len(result.missed_features))

        # Ensure score is in valid range
        return max(0.0, min(1.0, score))
