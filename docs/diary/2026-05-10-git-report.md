## 2026-05-10: Git Report

Perfect! Now I have enough information to provide a comprehensive analysis. Let me create a feature-level summary:

## 📊 Git Repository Analysis: Last 3 Days (May 7-9, 2026)

Based on the commit history and file changes, here's a feature-level summary of recent development:

### **🎯 Major Features Completed**

#### 1. **FR-360: Voice-Driven GitHub Issue Intake** (May 9)
   - **Status**: ✅ Merged & Documented
   - **Scope**: Implemented a voice-driven interface for creating GitHub issues via the `incaller` project
   - **Key Components**:
     - New `create_issue.py` tool node for programmatic issue creation
     - Voice readback prompts (`speak_issue_url.yaml`, `speak_issue_error.yaml`)
     - Graph routing guards and state management
     - 233 lines of test coverage (REQ-YG-333..339)
   - **Artifacts**: Capability CAP-144, updated README, architecture docs

#### 2. **FR-358: Watcher2 Primary PR Title Selection** (May 8-9)
   - **Status**: ✅ Completed with sanity-check validation
   - **Purpose**: Deterministic primary PR title selection in watcher2 pipeline
   - **Documentation**: Diary reflections and validation logs

#### 3. **FR-355: MCP Startup Schema Validation Gate** (May 8)
   - **Status**: ✅ Completed
   - **Details**: 
     - Fixed MCP dict state field normalization to use `object+additionalProperties`
     - Added schema validation during discovery phase
     - Prevents runtime schema mismatches

---

### **🔧 Bug Fixes & Technical Improvements**

| Fix | Impact |
|-----|--------|
| **Bash Context Placeholder Regex** | Eliminated false positives from shell syntax `{ cmd; }` and JSON literals |
| **FSM Socket Path & Port Conflicts** | Fixed shared bridge module networking issues |
| **Judge Model Update** | Upgraded to Claude Sonnet 4.6 for better performance |
| **Context Planner Provider** | Fixed module map injection and graceful assembler behavior |
| **MCP Dict Schema Normalization** | Corrected discovery schema for state field handling |
| **Capture
