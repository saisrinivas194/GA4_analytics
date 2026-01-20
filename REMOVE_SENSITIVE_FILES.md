# Remove Sensitive Files from Git

**IMPORTANT:** If you accidentally committed `service-account-key.json` to Git, you need to remove it immediately!

## Steps to Remove Sensitive Files:

### 1. Remove from Git (but keep local file):
```bash
cd "/Users/saisrinivaspedhapolla/Documents/GA4 API"
git rm --cached service-account-key.json
```

### 2. Verify it's in .gitignore:
The `.gitignore` file should already have:
```
service-account-key.json
*.json
```

### 3. Commit the removal:
```bash
git add .gitignore
git commit -m "Remove sensitive service account key from repository"
git push origin main
```

### 4. If already pushed to GitHub:
**URGENT:** If the file was already pushed:
1. Go to GitHub and delete the file through the web interface
2. Consider rotating/regenerating your service account key (it may be compromised)
3. Update your Streamlit secrets with the new key

### 5. Verify it's removed:
```bash
git ls-files | grep service-account-key.json
```
(Should return nothing)

## For Streamlit Cloud:
- **DO NOT** put the JSON file in your repository
- **USE** Streamlit secrets instead (Settings → Secrets)
- The secrets are encrypted and secure

