---
name: chunked-write-protocol
description: Mandatory file operation pattern for Hermes. Split large writes across multiple tool calls to avoid server timeout (350 line hard limit per operation). Applies to all new-file creation and existing-file edits.
---

# Skill: Chunked Write Protocol

**MANDATORY CONSTRAINT for all file operations in Hermes.**

Splitting large file writes into chunks prevents server timeout failures. This is not optional—it is a hard operational requirement.

## Core Rule

**MAXIMUM 350 LINES per single write/edit operation. NO EXCEPTIONS.**

Violations cause complete operation failure due to 2-3 minute server timeout. Chunked writes are faster and 100% reliable.

## When to Apply

### 1. New Files (>300 lines total)

**Pattern**:
1. Write initial chunk (250-300 lines) via `write_file()`
2. Append remaining content in 250-300 line chunks via subsequent `write_file()` or `patch()`
3. Repeat until complete

**Example: 600-line file**
```
Operation 1: write_file() → lines 1-300
Operation 2: write_file() → lines 301-600
```

### 2. Editing Existing Files

**Pattern**:
- Use surgical edits (patch/targeted changes) — change ONLY what's needed
- Never rewrite entire files to change 5 lines
- Split large refactors into multiple small, focused edits

**Example: Refactoring class (wrong vs right)**

❌ WRONG:
```python
# Rewrite entire 400-line file to change 2 methods
write_file("src/models/user.py", full_rewritten_content)  # TIMEOUT
```

✅ RIGHT:
```python
# Edit each method separately
patch("src/models/user.py", old_method_a, new_method_a)
patch("src/models/user.py", old_method_b, new_method_b)
```

### 3. Large Code Generation (Multi-section files)

**Pattern**:
1. Generate imports section (50-100 lines) → write
2. Generate type definitions (100-150 lines) → write
3. Generate functions (200-250 lines) → write
4. Combine results incrementally

**Example: Backend API file (1200 lines)**

Section 1: Imports + Type definitions (150 lines) → `write_file()`
Section 2: Route handlers (300 lines) → `write_file()`
Section 3: Controllers (300 lines) → `write_file()`
Section 4: Middleware + Utilities (300 lines) → `write_file()`
Section 5: Tests (150 lines) → `write_file()`

## Pre-Flight Checklist

Before any write operation:

```
[ ] Count lines in content to write
[ ] Is it > 350 lines?
    ☐ YES → Plan chunking strategy + split content
    ☐ NO → Proceed with single write_file() or patch()
[ ] For existing-file edits: Is this a surgical change?
    ☐ YES → Use patch() with exact old/new strings
    ☐ NO → Consider splitting into multiple patch() calls
[ ] Execute operations in sequence
[ ] Verify output (git diff, file inspection)
```

## Rationale

### Why This Matters

- **Server timeout**: 2-3 minute limit on all tool operations
- **Large writes fail completely**: No partial success, no retry hook, timeout = failure
- **Chunked writes are faster**: Multiple small operations run in parallel stages faster than one blocked large operation
- **Reliability**: 100% success rate vs. unpredictable failures

### Performance Impact

```
Single 500-line write:
  → Upload (30s) + Timeout (120s) = FAIL

5 × 100-line writes:
  → Upload (6s each) + Process (2s each) = 40s total = SUCCESS
```

## Practical Examples

### Example 1: New Vue 3 Component (250 lines)

✅ Single write is safe:
```javascript
write_file("resources/js/components/Card.vue", content)  # OK
```

### Example 2: New Vue 3 Page (500 lines)

❌ Too large for single write:
```javascript
# FAIL (timeout)
write_file("resources/js/pages/Dashboard.vue", full_content)
```

✅ Split into chunks:
```javascript
# OK (two operations)
write_file("resources/js/pages/Dashboard.vue", first_300_lines)
write_file("resources/js/pages/Dashboard.vue", remaining_200_lines)  # append mode
```

### Example 3: Refactor Laravel Model (150 → 180 lines)

✅ Surgical patch is safe:
```python
patch("app/Models/User.php", 
  old_method_code, 
  new_method_code)  # OK
```

### Example 4: Add Multiple Methods to Class (existing 300 lines)

❌ Rewriting entire file:
```python
# FAIL (timeout)
patch("app/Models/User.php", 
  entire_old_class_code, 
  entire_new_class_code)
```

✅ Add methods one-by-one via patch:
```python
patch("app/Models/User.php", 
  "    }\n}", 
  """    }
    
    public function newMethod1() { ... }
}\n""")

patch("app/Models/User.php",
  "    }\n}",
  """    }
  
    public function newMethod2() { ... }
}\n""")
```

## Verification

After chunked writes, always verify:

```bash
# Verify file was created correctly
ls -la <file_path>
wc -l <file_path>

# Verify content integrity
git diff <file_path>  # Check for double-inserts, missing sections

# Verify syntax if applicable
python -m py_compile <file_path>  # Python
node -c <file_path>               # JavaScript
php -l <file_path>                # PHP
```

## Anti-Patterns (Things That Will Fail)

| Pattern | Status | Why |
|---------|--------|-----|
| Single 500-line write | ❌ FAIL | Timeout |
| Rewrite entire 400-line file to fix 1 line | ❌ FAIL | Timeout + unnecessary |
| Patch that includes entire method + context | ⚠️ RISKY | May timeout if >350 lines |
| Multiple `write_file()` calls on same file sequentially | ✅ OK | Each call is independent |

## Tooling Rules

### write_file()
- Max 350 lines per call
- Overwrites entire file (destructive)
- Use for new files only
- For appending: read existing, append, write back (fits in 350 lines)

### patch()
- Surgical edits only
- old_string must be unique in file
- Total size must fit in 350 lines (usually does for edits)
- Preferred for existing files

### execute_code()
- Can call write_file() internally
- Respects chunking limits
- Good for programmatic multi-file generation

## Integration with CI/CD

After all writes complete, verify:
```bash
git status        # Show all changes
git diff          # Show diffs
npm run build     # or: php artisan serve, pytest, etc.
```

If build fails → root cause might be:
- Incomplete chunked write (missing section)
- Syntax error in generated code
- File encoding issue

---

## Summary

**Follow this rule on every file operation:**

```
IF line_count(content) > 350:
    SPLIT into chunks of 250-300 lines
    EXECUTE sequentially or in parallel stages
ELSE:
    PROCEED with single write_file() or patch()
ALWAYS:
    VERIFY with git diff and syntax checks
```

This is not a suggestion—it is a hard constraint encoded in server timeouts.
