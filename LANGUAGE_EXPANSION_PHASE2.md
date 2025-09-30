# CodeConcat Language Expansion - Phase 2
## Additional 15 Strategic Languages (v0.10.0)

**Status**: Planned for Post-v0.9.0
**Target Release**: v0.10.0-v0.10.2
**Builds On**: Phase 1 (14 languages in v0.9.0)

---

## Executive Summary

Following the successful implementation of 14 new languages in v0.9.0, Phase 2 targets 15 additional strategic languages focused on maximum practical value for codeconcat users. These languages cover mobile development, infrastructure-as-code, database analysis, emerging ecosystems, systems programming, and WebAssembly.

### New Languages by Strategic Priority

```
HIGH PRIORITY (7)            MEDIUM PRIORITY (6)         LOW PRIORITY (2)
├─ Kotlin (Android/JVM)      ├─ Zig (Emerging Systems)   ├─ Nim (Niche)
├─ Dart (Flutter)            ├─ V (Simple & Fast)        └─ Embedded C
├─ SQL (DB Analysis)         ├─ Crystal (Ruby-Like)
├─ Terraform (IaC)           ├─ Elixir (Real-time)
├─ WebAssembly (WASM/WAT)    ├─ Scala (Big Data)
├─ GraphQL (API)             └─ Nix (DevOps)
└─ (Community Vote)
```

---

## High Priority Languages (Target: v0.10.0)

### 1. Kotlin - Android & Server-Side Development

**Strategic Value**: CRITICAL
- 60%+ of new Android projects use Kotlin
- Growing server-side adoption (Ktor, Spring Boot)
- JetBrains backing ensures long-term support
- Replaces Java in many enterprise contexts

**Tree-sitter Grammar**:
- Repository: tree-sitter-grammars/tree-sitter-kotlin
- Status: Official tree-sitter-grammars organization
- Version: Latest (January 2025 update)
- Quality: HIGH - actively maintained, comprehensive coverage
- PyPI Package: tree-sitter-kotlin (available)

**Implementation Complexity**: LOW
- Similar to Java/Swift parsing patterns
- Strong type system with inference
- Extension functions and coroutines need attention

**Use Cases**:
- Android app codebases
- Kotlin Multiplatform projects
- Server-side microservices
- Gradle build scripts (.kts files)

**File Extensions**: .kt, .kts

---

### 2. Dart - Flutter Cross-Platform Development

**Strategic Value**: HIGH
- Flutter dominance in cross-platform mobile
- Single codebase for iOS/Android/Web/Desktop
- Used by: Google Pay, BMW, Alibaba, eBay
- Growing rapidly in startup ecosystem

**Tree-sitter Grammar**:
- Repository: yanok/tree-sitter-dart
- Status: Community-maintained, derived from official Dart spec
- Quality: HIGH - generated from specification
- Alternative: UserNobody14/tree-sitter-dart

**Implementation Complexity**: LOW-MEDIUM
- C-like syntax with modern features
- Async/await patterns
- Widget tree analysis important for Flutter

**Use Cases**:
- Flutter mobile app analysis
- Dart backend services (shelf, dart_frog)
- Cross-platform codebases
- Widget composition understanding

**File Extensions**: .dart

---

### 3. SQL - Database Schema & Query Analysis

**Strategic Value**: CRITICAL
- Universal in enterprise development
- Every codebase interacts with databases
- Migration analysis crucial for large projects
- Query optimization insights

**Tree-sitter Grammar**:
- Repository: DerekStride/tree-sitter-sql
- Dialects: PostgreSQL, MySQL, SQLite, MSSQL
- Status: Community-maintained, comprehensive
- Alternative: m-novikov/tree-sitter-sql (PostgreSQL-focused)

**Implementation Complexity**: MEDIUM
- Multiple dialect variations
- DDL vs DML extraction
- Complex query structure parsing
- Stored procedure support

**Use Cases**:
- Database migration analysis
- Schema documentation generation
- Query performance review
- ORM integration understanding

**File Extensions**: .sql, .ddl, .dml

---

### 4. Terraform (HCL) - Infrastructure as Code

**Strategic Value**: HIGH
- Standard for cloud infrastructure management
- AWS, Azure, GCP deployment analysis
- Critical for DevOps workflows
- Growing multi-cloud adoption

**Tree-sitter Grammar**:
- Repository: rmagatti/tree-sitter-terraform (HCL2)
- Alternative: MichaHoffmann/tree-sitter-hcl
- Status: Community-maintained, high quality
- Version: Supports HCL2 syntax

**Implementation Complexity**: LOW
- Clear block structure
- Resource/module declarations
- Variable and output extraction
- Provider configuration parsing

**Use Cases**:
- Infrastructure audit and analysis
- Module dependency mapping
- Resource inventory generation
- Multi-environment configuration review

**File Extensions**: .tf, .tfvars, .hcl

---

### 5. WebAssembly (WASM & WAT) - Universal Binary Format

**Strategic Value**: HIGH
- Universal compilation target (Rust, C++, Go, AssemblyScript)
- Browser and server-side execution
- Performance-critical web applications
- Emerging as language-agnostic runtime

**Tree-sitter Grammar**:
- WASM (Binary): wasm-lsp/tree-sitter-wasm
- WAT (Text): wasm-lsp/tree-sitter-wat
- Status: Community-maintained, WebAssembly-focused
- Quality: HIGH - spec-compliant

**Implementation Complexity**: MEDIUM
- Binary format (WASM) vs text format (WAT)
- Module structure extraction
- Import/export analysis
- Function signatures and types

**Use Cases**:
- Browser-based application analysis
- WASM module inspection
- Cross-language compilation verification
- Performance optimization review

**File Extensions**: .wasm, .wat

---

### 6. GraphQL - API Schema & Query Language

**Strategic Value**: HIGH
- Standard for modern API design
- Used by GitHub, Shopify, Facebook, Netflix
- Schema-first development
- Strong typing for API contracts

**Tree-sitter Grammar**:
- Repository: bkegley/tree-sitter-graphql
- Status: Community-maintained
- Quality: HIGH - spec-compliant
- Coverage: Schema, queries, mutations, subscriptions

**Implementation Complexity**: LOW
- Simple schema definition language
- Type system extraction
- Query/mutation/subscription patterns
- Directive handling

**Use Cases**:
- API schema documentation
- GraphQL federation analysis
- Client query validation
- Schema evolution tracking

**File Extensions**: .graphql, .gql

---

### 7. (Reserved for Community Vote)

**Options Under Consideration**:
- **Lua** (Game dev, Neovim plugins, embedded scripting)
- **Erlang** (Telecom, WhatsApp, RabbitMQ infrastructure)
- **Perl** (Legacy systems, bioinformatics, sysadmin)

---

## Medium Priority Languages (Target: v0.10.1+)

### 6. Zig - Emerging Systems Language

**Strategic Value**: MEDIUM-HIGH
- Potential C replacement with modern safety
- Bun runtime built with Zig
- Growing in performance-critical tooling
- Clean interop with C/C++

**Tree-sitter Grammar**:
- Repository: maxxnino/tree-sitter-zig
- Alternative: GrayJack/tree-sitter-zig
- Status: Community-maintained, active development
- Quality: GOOD - covers Zig 0.11+

**Implementation Complexity**: LOW-MEDIUM
- Clear syntax, no hidden control flow
- Comptime expressions need handling
- Error unions and optionals

**Use Cases**:
- Low-level systems programming
- Performance-critical tools
- C/C++ replacement projects
- WebAssembly compilation targets

**File Extensions**: .zig

---

### 7. Elixir - Concurrent & Real-Time Systems

**Strategic Value**: MEDIUM
- Powers Discord, WhatsApp infrastructure
- Excellent for real-time, distributed systems
- Phoenix framework popularity
- Erlang VM reliability

**Tree-sitter Grammar**:
- Repository: elixir-lang/tree-sitter-elixir
- Status: OFFICIAL - maintained by Elixir core team
- Quality: EXCELLENT - comprehensive coverage
- Active updates with language releases

**Implementation Complexity**: MEDIUM
- Macro system complexity
- Pipeline operator patterns
- Module attribute extraction
- Protocol implementations

**Use Cases**:
- Real-time web applications
- Chat/messaging systems
- IoT device orchestration
- Distributed systems analysis

**File Extensions**: .ex, .exs

---

### 8. Scala - Big Data & Enterprise

**Strategic Value**: MEDIUM
- Apache Spark, Kafka ecosystems
- Financial services infrastructure
- LinkedIn, Twitter backends
- Mature enterprise presence

**Tree-sitter Grammar**:
- Repository: tree-sitter/tree-sitter-scala
- Status: Official tree-sitter organization
- Quality: GOOD - covers Scala 2.x and 3.x
- Challenges: Complex type system

**Implementation Complexity**: HIGH
- Multiple paradigms (OOP + FP)
- Advanced type system
- Implicit resolution
- Macro system

**Use Cases**:
- Big data pipeline analysis
- Spark job codebases
- Financial trading systems
- Akka actor systems

**File Extensions**: .scala, .sc

---

### 9. GraphQL - API Schema & Query Language

**Strategic Value**: MEDIUM
- Standard for modern API design
- Used by GitHub, Shopify, Facebook
- Schema documentation critical
- Client-server contract analysis

**Tree-sitter Grammar**:
- Repository: bkegley/tree-sitter-graphql
- Status: Community-maintained
- Quality: HIGH - spec-compliant

**Implementation Complexity**: LOW
- Simple schema definition language
- Type system extraction
- Query/mutation/subscription patterns
- Directive handling

**Use Cases**:
- API schema documentation
- GraphQL federation analysis
- Client query validation
- Schema evolution tracking

**File Extensions**: .graphql, .gql

---

### 10. Nix - Reproducible Build System

**Strategic Value**: MEDIUM
- Reproducible package management
- NixOS ecosystem growth
- DevOps adoption increasing
- Deterministic builds appeal

**Tree-sitter Grammar**:
- Repository: cstrahan/tree-sitter-nix
- Status: Community-maintained
- Quality: GOOD - covers Nix language

**Implementation Complexity**: MEDIUM
- Unique functional syntax
- Lazy evaluation semantics
- Derivation extraction
- Overlay system

**Use Cases**:
- NixOS configuration analysis
- Package derivation review
- Flake structure understanding
- Reproducible build audit

**File Extensions**: .nix

---

## Low Priority Languages

### 11. Nim - Python-Like Performance

**Strategic Value**: LOW
- Technical merits but limited adoption
- Small but passionate community
- Python-like with C performance
- Game development niche

**Tree-sitter Grammar**:
- Repository: alaviss/tree-sitter-nim
- Status: Community-maintained
- Quality: DECENT - basic coverage

**Implementation Complexity**: LOW
- Python-like syntax
- Macro system
- Template metaprogramming

**File Extensions**: .nim, .nims

---

## Implementation Priority Tiers

### Tier 1 - Essential (Immediate Implementation)
```
Priority 1: Kotlin    - Mobile ecosystem critical
Priority 2: Dart      - Cross-platform dominance
Priority 3: SQL       - Universal database need
Priority 4: Terraform - Cloud infrastructure standard
```

### Tier 2 - Strategic Value (Next Wave)
```
Priority 5: Zig       - Emerging ecosystem
Priority 6: Elixir    - Real-time systems
Priority 7: GraphQL   - API standard
```

### Tier 3 - Specialized (Community Demand)
```
Priority 8: Scala     - Big data ecosystem
Priority 9: Nix       - DevOps niche
Priority 10: Nim      - Performance enthusiasts
```

---

## Grammar Verification Matrix

| Language | Repository | Status | Quality | Complexity |
|----------|-----------|--------|---------|------------|
| Kotlin | tree-sitter-grammars/tree-sitter-kotlin | Official | HIGH | LOW |
| Dart | yanok/tree-sitter-dart | Community | HIGH | LOW-MED |
| SQL | DerekStride/tree-sitter-sql | Community | GOOD | MEDIUM |
| Terraform | rmagatti/tree-sitter-terraform | Community | HIGH | LOW |
| Zig | maxxnino/tree-sitter-zig | Community | GOOD | LOW-MED |
| Elixir | elixir-lang/tree-sitter-elixir | Official | EXCELLENT | MEDIUM |
| Scala | tree-sitter/tree-sitter-scala | Official | GOOD | HIGH |
| GraphQL | bkegley/tree-sitter-graphql | Community | HIGH | LOW |
| Nix | cstrahan/tree-sitter-nix | Community | GOOD | MEDIUM |
| Nim | alaviss/tree-sitter-nim | Community | DECENT | LOW |

---

## Phase 2 Implementation Timeline

### v0.10.0 - Tier 1 Languages (6-8 weeks post v0.9.0)

**Week 1-2: Kotlin**
- Enhanced parser with Android-specific patterns
- Extension function extraction
- Coroutine flow analysis
- Gradle Kotlin DSL support

**Week 3-4: Dart**
- Flutter widget tree parsing
- Async/await pattern extraction
- State management patterns
- Null-safety analysis

**Week 5-6: SQL**
- Multi-dialect support (PostgreSQL, MySQL, SQLite)
- DDL schema extraction
- DML query patterns
- Stored procedure parsing

**Week 7-8: Terraform**
- Resource block extraction
- Module dependency mapping
- Variable and output analysis
- Provider configuration parsing

### v0.10.1 - Tier 2 Languages (4-6 weeks post v0.10.0)

**Week 1-2: Zig, Elixir**
- Zig systems programming patterns
- Elixir macro system handling
- Protocol/behaviour extraction

**Week 3-4: GraphQL**
- Schema type extraction
- Query/mutation patterns
- Directive handling

### v0.10.2 - Tier 3 Languages (As demanded)

**Community-driven implementation**
- Scala (if big data users request)
- Nix (if DevOps users request)
- Nim (if performance community requests)

---

## Enhanced Parser Patterns

### Mobile Development Pattern (Kotlin, Dart)
```python
def _init_mobile_queries(self):
    # UI component declarations
    self.component_query = """
    (class_declaration
        (modifiers) @modifiers
        name: (identifier) @name
        (#match? @name "Widget|Activity|Fragment|Composable")
    ) @component
    """

    # Async patterns
    self.async_query = """
    (function_declaration
        (modifiers) @modifiers
        (#match? @modifiers "async|suspend")
    ) @async_function
    """
```

### Infrastructure Pattern (Terraform, Nix)
```python
def _init_infrastructure_queries(self):
    # Resource declarations
    self.resource_query = """
    (block
        (identifier) @block_type
        (#eq? @block_type "resource")
        (string_lit) @resource_type
        (string_lit) @resource_name
    ) @resource
    """

    # Module references
    self.module_query = """
    (block
        (identifier) @block_type
        (#eq? @block_type "module")
    ) @module
    """
```

### Database Pattern (SQL)
```python
def _init_database_queries(self):
    # Table definitions
    self.table_query = """
    (create_table_statement
        name: (identifier) @table_name
    ) @table
    """

    # Query patterns
    self.select_query = """
    (select_statement) @select
    """
```

---

## Success Metrics (Phase 2)

### Technical
- [ ] All Tier 1 languages (4) in v0.10.0
- [ ] >95% test coverage per parser
- [ ] <5% additional overhead (cumulative <15% from v0.8.5)
- [ ] SQL multi-dialect support validated

### User-Facing
- [ ] Mobile development workflow coverage (Kotlin + Dart)
- [ ] Infrastructure analysis capability (Terraform + SQL)
- [ ] Complete documentation per language
- [ ] Example projects for each tier

---

## Community Feedback Integration

### Open Questions for Community
1. **5th High-Priority Language**: Lua, Erlang, or Perl?
2. **SQL Dialect Priority**: PostgreSQL, MySQL, SQLite order?
3. **Kotlin Build System**: Full Gradle DSL support needed?
4. **Flutter Specifics**: Widget inspection depth?

### Voting Mechanism
- GitHub Discussion: "Phase 2 Language Priorities"
- Poll closes 4 weeks after v0.9.0 release
- Top-voted language becomes 5th Tier 1 addition

---

## Appendix: Alternative Grammars

### Backup Grammar Sources

**Kotlin**:
- Primary: tree-sitter-grammars/tree-sitter-kotlin
- Backup: fwcd/tree-sitter-kotlin
- Backup: tormodatt/tree-sitter-kotlin

**Dart**:
- Primary: yanok/tree-sitter-dart
- Backup: UserNobody14/tree-sitter-dart

**SQL**:
- Primary: DerekStride/tree-sitter-sql (multi-dialect)
- Backup: m-novikov/tree-sitter-sql (PostgreSQL)
- Backup: dhcmrlchtdj/tree-sitter-sqlite

**Zig**:
- Primary: maxxnino/tree-sitter-zig
- Backup: GrayJack/tree-sitter-zig

---

**Plan Status**: ✅ READY FOR COMMUNITY REVIEW
**Last Updated**: 2025-09-29
**Version**: 1.0

---

## Medium Priority Languages (Continued)

### 6. V - Simple, Fast Compiled Language

**Strategic Value**: MEDIUM
- Simple syntax like Go, performance like C
- Fast compilation times
- Growing in systems programming
- Memory-safe by default

**Tree-sitter Grammar**:
- Repository: v-analyzer/v-analyzer (includes tree-sitter)
- Alternative: kkiyama117/tree-sitter-v
- Status: Community-maintained
- Quality: GOOD - covers V 0.4+

**Implementation Complexity**: LOW
- Go-like syntax simplicity
- No hidden control flow
- Clear function/struct extraction
- Module system straightforward

**Use Cases**:
- Systems programming projects
- Performance-critical tools
- C replacement codebases
- Game development

**File Extensions**: .v, .vsh

**Note**: V is positioned as "simple, fast, safe, compiled" - appeals to developers wanting C performance without C complexity.

---

### 7. Crystal - Ruby-Like Performance Language

**Strategic Value**: MEDIUM
- Ruby syntax with C performance
- Static typing with inference
- Growing web framework ecosystem (Lucky, Amber)
- Compile-time optimization

**Tree-sitter Grammar**:
- Repository: keidax/tree-sitter-crystal
- Status: Community-maintained
- Quality: GOOD - covers Crystal 1.x

**Implementation Complexity**: MEDIUM
- Ruby-like syntax familiarity
- Macro system complexity
- Type inference handling
- Shard (package) system

**Use Cases**:
- High-performance web services
- Ruby migration projects
- CLI tool development
- Microservices with Ruby ergonomics

**File Extensions**: .cr

**Strategic Note**: Crystal fills the "Ruby syntax + C performance" niche. Growing but still smaller ecosystem than established languages.

---

## Low Priority Languages (Continued)

### 2. Embedded C - Microcontroller & IoT Development

**Strategic Value**: LOW-MEDIUM
- Subset of C for embedded systems
- Arduino, ESP32, STM32 development
- IoT device firmware
- Resource-constrained environments

**Tree-sitter Grammar**:
- Uses standard tree-sitter-c with embedded extensions
- Specialized patterns for hardware registers
- Status: Use existing C parser with enhancements
- Quality: Depends on base C parser

**Implementation Complexity**: LOW
- Extends existing C/C++ parser
- Hardware register patterns
- Interrupt handler detection
- Memory-mapped I/O

**Use Cases**:
- IoT firmware codebases
- Embedded systems projects
- Arduino library analysis
- Microcontroller development

**File Extensions**: .c, .h (same as C, context-dependent)

**Implementation Note**: Rather than separate parser, enhance existing TreeSitterCppParser with embedded-specific patterns.

---

## Special Consideration: SAS (Not Recommended)

### SAS - Statistical Analysis System

**Strategic Value**: LOW
- Legacy statistical software
- Declining usage (replaced by Python/R)
- Proprietary license restrictions
- Poor open-source tool support

**Tree-sitter Grammar**:
- Status: NO OFFICIAL GRAMMAR AVAILABLE
- Community attempts: Limited and incomplete
- Quality: POOR - proprietary syntax challenges
- Maintenance: Minimal to none

**Implementation Complexity**: VERY HIGH
- Proprietary syntax quirks
- Multiple procedure languages
- Macro language complexity
- Limited grammar resources

**Recommendation**: **DO NOT IMPLEMENT**
- Poor grammar availability
- Declining market share
- Python/R cover same use cases
- Limited codeconcat user demand

**Alternative**: Focus on Python (already supported) and R (already supported) for statistical analysis workflows.

---

## Updated Grammar Verification Matrix

| Language | Repository | Status | Quality | Complexity | Priority |
|----------|-----------|--------|---------|------------|----------|
| Kotlin | tree-sitter-grammars/tree-sitter-kotlin | Official | HIGH | LOW | HIGH |
| Dart | yanok/tree-sitter-dart | Community | HIGH | LOW-MED | HIGH |
| SQL | DerekStride/tree-sitter-sql | Community | GOOD | MEDIUM | HIGH |
| Terraform | rmagatti/tree-sitter-terraform | Community | HIGH | LOW | HIGH |
| WASM | wasm-lsp/tree-sitter-wasm | Community | HIGH | MEDIUM | HIGH |
| WAT | wasm-lsp/tree-sitter-wat | Community | HIGH | MEDIUM | HIGH |
| GraphQL | bkegley/tree-sitter-graphql | Community | HIGH | LOW | HIGH |
| Zig | maxxnino/tree-sitter-zig | Community | GOOD | LOW-MED | MEDIUM |
| V | v-analyzer/v-analyzer | Community | GOOD | LOW | MEDIUM |
| Crystal | keidax/tree-sitter-crystal | Community | GOOD | MEDIUM | MEDIUM |
| Elixir | elixir-lang/tree-sitter-elixir | Official | EXCELLENT | MEDIUM | MEDIUM |
| Scala | tree-sitter/tree-sitter-scala | Official | GOOD | HIGH | MEDIUM |
| Nix | cstrahan/tree-sitter-nix | Community | GOOD | MEDIUM | MEDIUM |
| Nim | alaviss/tree-sitter-nim | Community | DECENT | LOW | LOW |
| Embedded C | Use tree-sitter-c + extensions | Official | GOOD | LOW | LOW |
| SAS | N/A - No quality grammar | None | POOR | VERY HIGH | SKIP |

---

## Revised Implementation Timeline

### v0.10.0 - Tier 1 (High Priority: 6 languages)

**Weeks 1-2: Mobile Ecosystem**
- Kotlin (Android/JVM)
- Dart (Flutter)

**Weeks 3-4: Infrastructure & Data**
- SQL (Multi-dialect)
- Terraform (HCL)

**Weeks 5-6: Modern Web Standards**
- WebAssembly (WASM + WAT)
- GraphQL

**Deliverable**: 6 high-priority parsers with comprehensive mobile, infrastructure, and web coverage

---

### v0.10.1 - Tier 2 (Medium Priority: 6 languages)

**Weeks 1-2: Emerging Systems Languages**
- Zig
- V
- Crystal

**Weeks 3-4: Enterprise & Real-Time**
- Elixir
- Scala

**Weeks 5-6: DevOps Niche**
- Nix

**Deliverable**: 6 medium-priority parsers covering emerging and specialized ecosystems

---

### v0.10.2 - Tier 3 (Low Priority: 2 languages + Community Choice)

**Weeks 1-2: Performance Niche**
- Nim
- Embedded C (C parser enhancement)

**Weeks 3-4: Community Vote Winner**
- Lua, Erlang, or Perl (based on demand)

**Deliverable**: Final 3 parsers completing Phase 2

**Note**: SAS is explicitly excluded due to poor grammar availability and declining usage.

---

## Total Language Coverage Projection

```
Current (v0.8.5):   11 languages
Phase 1 (v0.9.0):  +14 languages = 25 total
Phase 2 (v0.10.x): +15 languages = 40 total
```

**40 Languages** = Comprehensive coverage of:
- Systems programming (C, C++, Rust, Zig, V, Crystal, Nim)
- Mobile development (Swift, Kotlin, Dart)
- Web development (JavaScript/TS, PHP, Ruby, Elixir)
- Functional programming (OCaml, ReScript, ReasonML, Elixir, Scala)
- Shaders (GLSL, HLSL, Metal)
- Data & DB (R, Julia, SQL, MATLAB alternatives)
- Infrastructure (Bash, Terraform, Nix)
- Blockchain (Solidity)
- Formal verification (Lean, Coq)
- WebAssembly & APIs (WASM/WAT, GraphQL)
- Domain-specific (Astro, Haxe, Vala)

---

## Enhanced Parser Patterns (New)

### WebAssembly Pattern (WASM/WAT)
```python
def _init_wasm_queries(self):
    # Module structure
    self.module_query = """
    (module) @module
    """

    # Function exports
    self.export_query = """
    (export
        name: (string) @name
    ) @export
    """

    # Function imports
    self.import_query = """
    (import
        module: (string) @module
        name: (string) @name
    ) @import
    """

    # Function signatures
    self.func_query = """
    (func
        (identifier)? @name
        (param)* @params
        (result)? @result
    ) @function
    """
```

### V Language Pattern
```python
def _init_v_queries(self):
    # Function definitions (V-specific)
    self.function_query = """
    (function_declaration
        receiver: (parameter_list)? @receiver
        name: (identifier) @name
        parameters: (parameter_list) @params
    ) @function
    """

    # Struct definitions
    self.struct_query = """
    (struct_declaration
        name: (identifier) @name
    ) @struct
    """

    # Module imports
    self.import_query = """
    (import_declaration
        path: (import_path) @path
    ) @import
    """
```

### Crystal Pattern (Ruby-like)
```python
def _init_crystal_queries(self):
    # Class definitions
    self.class_query = """
    (class
        name: (constant) @name
        superclass: (constant)? @superclass
    ) @class
    """

    # Method definitions
    self.method_query = """
    (method
        name: (identifier) @name
        parameters: (method_parameters)? @params
    ) @method
    """

    # Macro definitions (Crystal-specific)
    self.macro_query = """
    (macro
        name: (identifier) @name
    ) @macro
    """
```

---

## Appendix: Grammar Repository Links

### High Priority
- **Kotlin**: https://github.com/tree-sitter-grammars/tree-sitter-kotlin
- **Dart**: https://github.com/yanok/tree-sitter-dart
- **SQL**: https://github.com/DerekStride/tree-sitter-sql
- **Terraform**: https://github.com/rmagatti/tree-sitter-terraform
- **WASM**: https://github.com/wasm-lsp/tree-sitter-wasm
- **WAT**: https://github.com/wasm-lsp/tree-sitter-wat
- **GraphQL**: https://github.com/bkegley/tree-sitter-graphql

### Medium Priority
- **Zig**: https://github.com/maxxnino/tree-sitter-zig
- **V**: https://github.com/v-analyzer/v-analyzer
- **Crystal**: https://github.com/keidax/tree-sitter-crystal
- **Elixir**: https://github.com/elixir-lang/tree-sitter-elixir
- **Scala**: https://github.com/tree-sitter/tree-sitter-scala
- **Nix**: https://github.com/cstrahan/tree-sitter-nix

### Low Priority
- **Nim**: https://github.com/alaviss/tree-sitter-nim
- **Embedded C**: Use tree-sitter-c with enhancements

---

**Plan Status**: ✅ COMPLETE - Ready for Community Review
**Last Updated**: 2025-09-29
**Version**: 2.0
**Total New Languages**: 15 (SAS excluded)
