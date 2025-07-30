# Contributing to CEAF Farmácia

## Development Workflow

### Branches
- **`main`**: Production-ready code
- **`development`**: Development branch for new features

### Getting Started

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd farmacia
   ./scripts/setup.sh
   ```

2. **Create feature branch**:
   ```bash
   git checkout development
   git checkout -b feature/your-feature-name
   ```

3. **Make changes and test**:
   ```bash
   # Make your changes
   source venv/bin/activate
   ./run.py  # Test the application
   ```

4. **Commit changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Merge back**:
   ```bash
   git checkout development
   git merge feature/your-feature-name
   ```

### Commit Message Format

Use conventional commits format:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

### Code Style

- Use Black for Python formatting: `black src/`
- Use flake8 for linting: `flake8 src/`
- Follow PEP 8 guidelines
- Add docstrings to functions and classes

### Testing

Before committing:
1. Test the web application: `./run.py`
2. Test the scraper: `./scripts/scrape_data.py --cache`
3. Run any existing tests: `pytest` (when available)

### Key Files

- `src/app.py` - Main Flask application
- `src/scraper.py` - Web scraping functionality
- `src/llm_processor.py` - AI processing
- `templates/` - HTML templates
- `static/` - CSS, JS, and assets
- `CLAUDE.md` - Claude Code instructions

### Adding New Medical Terms

To add new popular terms or misspellings:

1. Edit `src/app.py` in the `fallback_smart_search()` function
2. Add to the `medical_terms` dictionary
3. Test with the new terms
4. Update examples in templates if needed

### Database Changes

Currently uses file-based data storage in `data/` directory.
If adding database support:
1. Update requirements.txt
2. Add database configuration to .env.example
3. Create migration scripts
4. Update CLAUDE.md instructions

## Issues and Support

When reporting issues:
1. Include Python version
2. Include error logs from `logs/farmacia.log`
3. Describe steps to reproduce
4. Include search terms that don't work

## License

This project is for educational and public service purposes.