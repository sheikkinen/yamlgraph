## 2026-09-28: Git Report

Perfect! Now I have a comprehensive view. Let me provide a detailed analysis:

## 📊 Git Repository Analysis: Last 3 Days Development Summary

**Repository:** YAMLGraph (a LLM graph orchestration framework)
**Analysis Period:** September 25-27, 2026
**Commits Analyzed:** 50 recent commits

---

## 🎯 **Feature-Level Summary**

### **1. Release Cycle: v0.6.1 → v0.6.2**
- **v0.6.1 Release** (Sept 27): Consolidated 14+ feature requests
- **v0.6.2 Release** (Sept 27): Focused on schema validation and error handling improvements

---

### **2. Major Feature Areas Completed**

#### **A. Schema & Constrained Decoding (FR-1123, FR-1125)**
- **FR-1123**: Reject untyped subschemas before Anthropic constrained decoding
- **FR-1125**: Refuse unconstrained/open objects on Anthropic-bound nodes
- **FR-1126**: Showcase refusal behavior in `ramp_rtm` demo with refused vs filled shape examples
- **Impact**: Prevents silent schema validation failures with LLM providers that enforce strict typing

#### **B. Error Handling & Exit Codes (FR-1083-1098, FR-1124)**
- **FR-1097/1098**: Graph run exit status reflects completion errors (exit code 3)
- **FR-1124**: LLM nodes now default to `on_error: fail` instead of `record_and_continue`
- **Impact**: Better observability and fail-fast behavior for production workflows

#### **C. CLI Variable Validation (FR-1084)**
- Graph run now refuses undeclared `--var` and `--var-file` keys
- Prevents silent configuration mismatches
- **Impact**: Stricter input validation at runtime

#### **D. Concurrency Management (FR-1085)**
- Default `max_concurrency` resolution at every managed run boundary
- Consistent concurrency handling across different execution contexts
- **Impact**: More predictable performance characteristics

#### **E. Map Node Improvements (FR-1065, FR-1073, FR-1116, FR-1120)**
- **FR-1065**: Resumable map investigation with probe patterns
- **FR-1073**: Map result contract - failures leave collect operation
- **FR-1116**: Map memo for f
