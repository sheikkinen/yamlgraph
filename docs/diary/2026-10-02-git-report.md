## 2026-10-02: Git Report

Based on the analysis of the last 50 commits, here's a comprehensive feature-level summary of the development in the last 3 days:

## 📊 **Development Summary - Last 3 Days**

### **Release Activity**
- **v0.6.1 and v0.6.2** released with multiple stability improvements
- Active changelog management with unreleased features being prepared

---

### **🎯 Major Feature Areas**

#### **1. Schema & Validation Enhancements**
- **FR-1123**: Untyped subschema gate for constrained decoding - prevents invalid schema structures before reaching LLM providers
- **FR-1125**: Refuse unconstrained objects on Anthropic-bound nodes - improved safety for structured output with Anthropic
- **FR-1127**: Nested fields grammar - enhanced inline schema form support
- **FR-1140**: Bare-list structured output planning - documenting judgment for list handling

#### **2. Error Handling & Robustness**
- **FR-1124**: LLM nodes now default to `on_error: fail` - safer default behavior
- **FR-1097/FR-1098**: Graph run exit codes properly reflect completion errors (exit code 3)
- **FR-1121**: Daily digest ranker survives constrained decoding and fails loudly
- **FR-1128**: Spike probe inline LLM exemption naming

#### **3. Map/Subgraph Operations**
- **FR-1122**: Daily digest map contract migration - improved map result handling
- **FR-1129**: Planned Operations section replaces Effort - better operation tracking
- **FR-939**: Typed on_overflow policy with fail-by-default
- **FR-1073**: Map result contract - failures leave collect phase

#### **4. Infrastructure & CLI**
- **FR-1084**: Graph run rejects undeclared `--var`/`--var-file` keys - prevents silent failures
- **FR-1085**: Resolved max_concurrency at every managed run boundary - consistent concurrency handling
- **FR-1104**: CI dedup - retire core-test, Python 3.14 ceiling leg

#### **5. Linting & Validation**
- **FR-1119**: Linter knows map-owned state fields - improved semantic validation
- **FR-1086**: Lint compile check - graph validation
