# 📝 CHANGELOG

## v1.1 Security Hardened (2025-05-08)

### 🔐 Security Fixes (12 Total)

#### Critical
- **Fixed**: NameError in TaskMonitor - undefined `username` variable
- **Fixed**: Unsafe `os.system()` calls - now using `subprocess.run()` with list-based args

#### High Priority
- **Fixed**: Race condition in multi-threaded file access
- **Fixed**: Path traversal vulnerability in paste operations
- **Added**: Path normalization to prevent escaping restricted directories

#### Medium Priority
- **Fixed**: ReDoS vulnerability in regex search
- **Fixed**: Font size validation (8-16pt range)
- **Fixed**: Color format validation (hex color check)
- **Fixed**: Filename validation to prevent dangerous characters
- **Added**: Search result limiting (1000 max display)

#### Low Priority
- **Improved**: Exception handling specificity
- **Fixed**: Resource cleanup on application exit
- **Added**: LRU cache minimum size enforcement

###  User Experience Enhancements
- Better error messages with specific feedback
- Confirmation dialogs for dangerous operations
- Visual indicators for safety classification (🟢🟡🔴)
- Improved status messages with emoji indicators
- Thread-safe clipboard operations
---

**Version History**:
- v1.0: Initial release with security hardening
- v1.1 Security Hardened: All 12 vulnerabilities fixed

---