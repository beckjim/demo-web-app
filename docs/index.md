# Employee Dialogue

Performance review self-assessments and manager evaluations with Microsoft 365 authentication.

## Overview

Employee Dialogue is a Flask web application that facilitates performance review processes by allowing:

- **Employees** to complete self-assessments with structured evaluations
- **Managers** to review and provide feedback on employee assessments
- **Seamless integration** with Microsoft 365 authentication
- **Automatic manager prefilling** via Microsoft Graph API

## Key Features

✨ **Self-Assessment Form**
- Objective achievement ratings
- Technical, project, and methodology ratings
- Efficiency and conduct evaluations
- General comments and feedback tracking

🔐 **Microsoft 365 Authentication**
- Secure login via Microsoft Entra (Azure AD)
- Automatic manager assignment via Graph API
- Session-based access control

📊 **Manager Dashboard**
- Review employee assessments
- Provide managerial feedback
- Create final performance evaluations
- Track assessment history

## Quick Start

```bash
# Install dependencies
pip install uv
uv venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
uv sync

# Run the application
uv run flask --app employee_dialogue run --debug
```

Visit [Getting Started](getting-started.md) for detailed setup instructions.

## Project Status

- **Version**: 0.1.0
- **Python**: 3.14
- **License**: MIT
- **Status**: Active Development

## Next Steps

- 📖 [Getting Started Guide](getting-started.md)
- ⚙️ [Configuration](configuration.md)
- 🏗️ [Architecture Overview](architecture/structure.md)
- 🤝 [Contributing](development/contributing.md)
