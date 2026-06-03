# Publish This Folder to GitHub

This folder is already a local Git repository and has one committed snapshot:

```powershell
git log --oneline -1
```

To publish it to your GitHub profile as `Extracted-Files`, first authenticate GitHub CLI:

```powershell
gh auth login
```

Recommended answers:

- GitHub.com
- HTTPS
- Authenticate with browser

Then run this command from this folder:

```powershell
gh repo create Extracted-Files --public --source . --remote origin --push --description "Curated HDL, PDF, and diagram-rich outputs extracted from OpenCores and FreeCores repositories"
```

GitHub repository names cannot reliably use spaces in command-line workflows, so `Extracted-Files` is the practical GitHub-safe version of "Extracted Files".

