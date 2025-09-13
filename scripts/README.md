# Scripts

This directory contains utility scripts for maintaining the Build Your Own X repository.

## Available Scripts

### health-check.sh
Validates the repository structure and provides statistics about the tutorial collection.

**Usage:**
```bash
./scripts/health-check.sh
```

**What it checks:**
- ✅ Required documentation files
- ✅ GitHub template files  
- ✅ README.md structure
- ✅ Learning path presence
- 📊 Tutorial statistics by category

## Running Scripts

All scripts are designed to be run from the repository root directory:

```bash
cd /path/to/build-your-own-x
./scripts/health-check.sh
```

## Contributing Scripts

When adding new scripts:
1. Make them executable: `chmod +x scripts/your-script.sh`
2. Add documentation to this README
3. Follow the existing script structure and output format
4. Test thoroughly before committing

## Future Scripts

Potential scripts to add:
- **link-validator.sh** - Comprehensive link checking
- **tutorial-analyzer.sh** - Deep analysis of tutorial categories and gaps
- **stats-generator.sh** - Generate detailed statistics for repository health
- **category-organizer.sh** - Help organize and categorize new submissions