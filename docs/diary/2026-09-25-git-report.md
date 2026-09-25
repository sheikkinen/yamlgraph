## 2026-09-25: Git Report

Perfect! Now I have enough information to provide a comprehensive analysis. Let me organize this by feature level.

## Git Repository Analysis: Last 3 Days (Sept 22-24, 2026)

### **Overview**
The repository shows **active development with two major release cycles** (v0.5.26 and v0.6.0) completed within the 3-day window, plus ongoing architectural improvements and issue resolution.

---

### **Feature-Level Summary**

#### **1. Release Management & Versioning** 
- **v0.6.0 released** (Sept 23) - Major version bump
- **v0.5.26 released** (Sept 23) - Patch release  
- **v0.5.25 changelog** frozen with extensive feature set
- Multiple changelog entries organized by feature request (FR) numbers

#### **2. Core Fixes & Improvements**

| Feature | Description | Status |
|---------|-------------|--------|
| **FR-1060: Subgraph Mode Validation** | Schema boundary validation for subgraph mode | ✅ Fixed |
| **FR-1058: RunnableConfig Propagation** | Direct subgraph registration with config propagation | ✅ Fixed |
| **FR-1057: Prompt Template Dialect** | Single template dialect decision per message | ✅ Fixed |
| **FR-1056: DeepSeek Thinking Budget** | Disable thinking when budget=0 | ✅ Fixed |
| **FR-1055: Anthropic System Segments** | System prompt cache blocks now reach API | ✅ Fixed |
| **FR-1054: Nested Object Schemas** | Nested objects now reach provider layer | ✅ Fixed |

#### **3. New Features Implemented**

| Feature | Description | Status |
|---------|-------------|--------|
| **FR-1049: OpenCode Judge Variant** | Third backend in sole-route judge adapter | ✅ Complete |
| **FR-1048: OpenCode CLI Backend** | CLI backend for copilot node with session tracking | ✅ Complete |
| **FR-1050: Loop Limits Binding** | Loop limits must bind or fail compilation | ✅ Fixed |
| **FR-1051: Artifact Hash Defaults** | Honour defaults.prompts_relative in artifact_hash | ✅ Fixed |

#### **4. Documentation & Architecture Work**

| Area | Activity |
|------|----------|
| **Issue Planning**
