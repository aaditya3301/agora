# Contributing to Agora Supply Chain Simulator

Thank you for your interest in contributing to Agora! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/agora-supply-chain-simulator.git
   cd agora-supply-chain-simulator
   ```
3. **Set up the development environment**:
   ```bash
   pip install -r requirements.txt
   ```

## 🛠️ Development Workflow

### Creating a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:
- `feature/new-agent-type` - for new features
- `fix/inventory-bug` - for bug fixes
- `docs/api-documentation` - for documentation updates
- `refactor/message-bus` - for code refactoring

### Making Changes

1. **Follow the existing code structure**:
   - Agents go in `agents/` directory
   - Data models in `models/` directory
   - Simulation logic in `simulation/` directory
   - Web interface in `web/` directory

2. **Write tests** for your changes:
   - Unit tests for individual components
   - Integration tests for multi-component features
   - Follow existing test patterns

3. **Update documentation** as needed:
   - Update README.md for user-facing changes
   - Update docstrings for code changes
   - Update design documents in `.kiro/specs/` if needed

### Code Style Guidelines

- **Python**: Follow PEP 8 style guidelines
- **JavaScript**: Use consistent indentation and naming
- **Comments**: Write clear, concise comments explaining complex logic
- **Docstrings**: Use descriptive docstrings for all classes and methods

### Testing Your Changes

```bash
# Run all tests
python -m pytest

# Run specific test files
python -m pytest tests/agents/test_store_agent.py

# Test the web interface
python web/app.py
# Then visit http://localhost:5000
```

## 📝 Commit Guidelines

### Commit Message Format

```
type(scope): brief description

Longer description if needed

- List any breaking changes
- Reference issues: Fixes #123
```

### Commit Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
git commit -m "feat(agents): add new supplier agent type"
git commit -m "fix(warehouse): resolve inventory tracking bug"
git commit -m "docs(readme): update installation instructions"
```

## 🔍 Pull Request Process

1. **Ensure your code passes all tests**
2. **Update documentation** for any user-facing changes
3. **Create a pull request** with:
   - Clear title describing the change
   - Detailed description of what was changed and why
   - Screenshots for UI changes
   - Reference to any related issues

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots for UI changes

## Related Issues
Fixes #123
```

## 🐛 Reporting Issues

### Bug Reports

Include:
- **Clear description** of the bug
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Environment details** (Python version, OS, etc.)
- **Error messages** or logs if available

### Feature Requests

Include:
- **Clear description** of the proposed feature
- **Use case** explaining why it's needed
- **Possible implementation** ideas (optional)

## 🏗️ Architecture Guidelines

### Adding New Agent Types

1. **Inherit from BaseAgent** in `agents/base_agent.py`
2. **Implement required methods**:
   - `step()`: Execute one simulation step
   - `handle_message()`: Process incoming messages
3. **Define message types** the agent sends/receives
4. **Add to agent integration** in `simulation/agent_integration.py`
5. **Update web interface** for visualization

### Extending the Message System

1. **Add new message types** to `models/message.py`
2. **Update relevant agents** to handle new messages
3. **Test message routing** through the message bus
4. **Document message protocols** in design docs

### Web Interface Changes

1. **Update HTML templates** in `web/templates/`
2. **Add CSS styles** in `web/static/css/`
3. **Update JavaScript** in `web/static/js/`
4. **Test WebSocket communication** with backend

## 📚 Resources

- **Design Documents**: `.kiro/specs/` directory
- **API Documentation**: Inline docstrings and comments
- **Test Examples**: `tests/` directory
- **Web Interface**: `web/` directory

## 🤝 Community Guidelines

- **Be respectful** and inclusive
- **Help others** learn and contribute
- **Ask questions** if you're unsure about anything
- **Share knowledge** and best practices
- **Give constructive feedback** on pull requests

## 📞 Getting Help

- **Open an issue** for questions or problems
- **Check existing issues** before creating new ones
- **Review the documentation** in `.kiro/specs/`
- **Look at existing code** for examples and patterns

Thank you for contributing to Agora Supply Chain Simulator! 🎉