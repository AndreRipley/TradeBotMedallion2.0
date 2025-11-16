# 🔒 Security Guide

## ⚠️ CRITICAL: API Keys Were Exposed

**Your API keys were accidentally committed to the public repository.** 

### Immediate Actions Required:

1. **ROTATE YOUR API KEYS IMMEDIATELY** ⚠️
   - Go to https://alpaca.markets/ → Dashboard → API Keys
   - **Delete the old keys** and generate new ones
   - The exposed keys are compromised and should never be used again

2. **Update your local `.env` file**
   - After generating new keys, update your local `.env` file
   - Never commit `.env` to git (it's in `.gitignore`)

3. **Remove keys from git history** (Recommended)
   - The keys are still visible in git history
   - Use one of these methods:
   
   **Option A: Using git filter-repo (recommended)**
   ```bash
   pip install git-filter-repo
   git filter-repo --path env_template.txt --invert-paths
   git push origin --force --all
   ```
   
   **Option B: Contact GitHub Support**
   - GitHub can help remove sensitive data from repository history
   - Go to: https://support.github.com/contact

### What Was Fixed:

✅ Removed real API keys from `env_template.txt`  
✅ Replaced with placeholder values  
✅ Added security warnings  
✅ `.env` file is properly gitignored  

### Prevention Checklist:

- ✅ Never commit `.env` file (it's in `.gitignore`)
- ✅ Only use placeholder values in template files
- ✅ Use environment variables for sensitive data
- ✅ Rotate keys immediately if exposed
- ✅ Use GitHub Secrets for CI/CD workflows

### Current Security Status:

| File | Status | Notes |
|------|--------|-------|
| `.env` | ✅ Safe | Gitignored, never committed |
| `env_template.txt` | ✅ Fixed | Now contains placeholders only |
| Git History | ⚠️ Contains old keys | Should be cleaned (see above) |

### Best Practices Going Forward:

1. **Always use placeholders in template files:**
   ```
   ALPACA_API_KEY=your_api_key_here
   ```

2. **Never commit real credentials:**
   - Use `.env` files (gitignored)
   - Use environment variables
   - Use secret management services

3. **If you accidentally commit secrets:**
   - Rotate keys immediately
   - Remove from git history
   - Consider using tools like `git-secrets` or `truffleHog`

4. **For production deployments:**
   - Use cloud secret managers (AWS Secrets Manager, Azure Key Vault, etc.)
   - Use CI/CD secrets (GitHub Secrets, GitLab CI/CD variables)
   - Never hardcode credentials

