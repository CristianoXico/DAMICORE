#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"

# Add all changes to git
git add .

# Commit with a descriptive message
commit_message="docs: update documentation and project structure

- Add comprehensive README in PT and EN
- Create CONTRIBUTING.md with contribution guidelines
- Update CHANGELOG.md with latest changes
- Add development dependencies and pre-commit hooks
- Improve .gitignore and .dockerignore"

git commit -m "$commit_message"

# Push to the remote repository
git push origin main

echo "✅ Changes committed and pushed successfully!"
