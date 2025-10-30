# Contributing to SyroApp

Thank you for your interest in contributing to SyroApp! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites
- Python 3.9+
- pip or conda
- Redis (for Celery tasks)
- Spotify Developer Account

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/SyroApp.git
cd SyroApp
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your Spotify credentials and settings
```

5. **Setup database**
```bash
python manage.py migrate
python manage.py createsuperuser
```

6. **Start Redis** (in another terminal)
```bash
redis-server
```

7. **Start the development server**
```bash
python manage.py runserver
```

Visit http://localhost:8000 in your browser.

## Development Workflow

### Before Making Changes
1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Make sure tests pass: `python manage.py test`
3. Ensure no uncommitted changes to sensitive files

### Code Style Guidelines

#### Python
- Follow PEP 8 style guide
- Use meaningful variable and function names
- Keep functions focused and under 50 lines when possible
- Add docstrings to all functions and classes

#### JavaScript
- Use camelCase for variables and functions
- Always use const/let (never var)
- Comment complex logic
- Escape HTML strings to prevent XSS

#### Django
- Use Django ORM instead of raw SQL when possible
- Implement proper error handling in views
- Use generic views and ViewSets where appropriate
- Keep business logic in services, not views

### Commit Messages

Follow conventional commit format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, perf, test, chore

Examples:
```
feat(search): add playlist search to player page

fix(player): correct album art display on mobile

docs(readme): update installation instructions

refactor(views): split views into logical modules
```

### Testing

```bash
# Run all tests
python manage.py test

# Run specific test module
python manage.py test SyroMusic.tests

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## Security Guidelines

### Never Commit
- `.env` files with credentials
- API keys or secrets
- Database dumps with user data
- Private keys or certificates

### Always
- Validate and sanitize user input
- Escape HTML output to prevent XSS
- Use Django's CSRF protection
- Validate file uploads
- Use HTTPS in production
- Never log sensitive information

## Code Review Process

1. Push your branch to the repository
2. Create a Pull Request with clear description
3. Include before/after screenshots for UI changes
4. Link any related issues
5. Ensure CI/CD pipeline passes
6. Request review from maintainers
7. Address feedback and request re-review

## Reporting Issues

### Bug Reports
Include:
- Clear description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Screenshots if applicable
- Browser/device information

### Feature Requests
Include:
- Clear description of desired functionality
- Why this feature would be useful
- Possible implementation approach
- Any relevant mockups or examples

## Performance Considerations

When contributing, be mindful of:
- Database query efficiency (avoid N+1 queries)
- Frontend bundle size
- Image optimization
- Caching strategies
- API rate limits

## Documentation

- Update README.md for user-facing changes
- Update CHANGELOG.md in the Unreleased section
- Add docstrings to all new functions
- Comment complex algorithms
- Document configuration options

## Questions?

- Check existing documentation in README.md and this file
- Review past issues for similar questions
- Create a new discussion for general questions

## Code of Conduct

- Be respectful and inclusive
- Welcome diverse perspectives
- Focus on constructive feedback
- Help others learn and grow

Thank you for contributing!
