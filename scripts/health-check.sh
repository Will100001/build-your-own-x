#!/bin/bash

# Repository Health Check Script
# This script validates the repository structure and content

echo "🔍 Build Your Own X - Repository Health Check"
echo "============================================="

# Check required files
echo
echo "📋 Checking required files..."
required_files=(
    "README.md"
    "CONTRIBUTING.md" 
    "CODE_OF_CONDUCT.md"
    "SETUP.md"
    "LICENSE"
    "SECURITY.md"
    ".github/PULL_REQUEST_TEMPLATE.md"
    ".github/ISSUE_TEMPLATE/tutorial-submission.yml"
    ".github/ISSUE_TEMPLATE/broken-link.yml"
    ".github/ISSUE_TEMPLATE/feature-request.yml"
    ".github/ISSUE_TEMPLATE/question.yml"
    ".github/workflows/link-validation.yml"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ $file exists"
    else
        echo "❌ $file is missing"
        all_files_exist=false
    fi
done

if $all_files_exist; then
    echo "✅ All required files are present!"
else
    echo "❌ Some required files are missing"
fi

# Count tutorials by category
echo
echo "📊 Tutorial statistics:"
total_tutorials=$(grep -c '\*\*.*\*\*: _.*_' README.md)
echo "Total tutorials: $total_tutorials"

echo
echo "📈 Top categories by tutorial count:"
grep "^#### Build your own" README.md | sed 's/.*`\(.*\)`/\1/' | while read category; do
    count=$(awk "/#### Build your own \`$category\`/,/^#### / { if (/\*\*.*\*\*: _.*_/) count++ } END { print count+0 }" README.md)
    echo "  $category: $count tutorials"
done | sort -k2 -nr | head -10

# Check README structure
echo
echo "🏗️ Validating README.md structure..."

structure_valid=true

# Check for required sections
if ! grep -q "## 🚀 Quick Start" README.md; then
    echo "❌ Missing 'Quick Start' section in README.md"
    structure_valid=false
fi

if ! grep -q "## 📑 Categories" README.md; then
    echo "❌ Missing 'Categories' section in README.md"  
    structure_valid=false
fi

if ! grep -q "## Tutorials" README.md; then
    echo "❌ Missing 'Tutorials' section in README.md"
    structure_valid=false
fi

if ! grep -q "## 🤝 Contribute" README.md; then
    echo "❌ Missing 'Contribute' section in README.md"
    structure_valid=false
fi

if $structure_valid; then
    echo "✅ README.md structure is valid!"
else
    echo "❌ README.md structure has issues"
fi

# Check for learning paths
echo
echo "🎯 Checking learning paths..."
if grep -q "### 🌱.*Beginner Path" README.md; then
    echo "✅ Beginner learning path found"
else
    echo "❌ Beginner learning path missing"
fi

if grep -q "### 🚀.*Intermediate Path" README.md; then
    echo "✅ Intermediate learning path found"
else
    echo "❌ Intermediate learning path missing"
fi

if grep -q "### 🧠.*Advanced Path" README.md; then
    echo "✅ Advanced learning path found"
else
    echo "❌ Advanced learning path missing"
fi

echo
echo "🎉 Repository health check complete!"

# Summary
echo
echo "📋 Summary:"
echo "- Documentation files: $(ls *.md | wc -l)"
echo "- GitHub templates: $(find .github -name "*.yml" -o -name "*.md" | wc -l)"
echo "- Total tutorials: $total_tutorials"
echo "- Categories: $(grep -c "^#### Build your own" README.md)"

echo
echo "✨ The Build Your Own X repository is enhanced and ready!"