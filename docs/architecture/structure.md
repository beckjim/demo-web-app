# Project Structure

Understanding the Employee Dialogue codebase organization.

## Directory Layout

```
employee-dialogue/
├── src/
│   └── employee_dialogue/
│       ├── __init__.py              # Flask app and routes
│       ├── templates/
│       │   ├── base.html            # Base template
│       │   ├── index.html           # Dashboard
│       │   ├── create.html          # Create entry form
│       │   ├── edit.html            # Edit entry form
│       │   └── final_edit.html      # Manager final assessment form
│       └── static/                  # CSS, JavaScript, assets
├── tests/
│   ├── __init__.py
│   └── test_app.py                  # Unit tests
├── docs/                            # Documentation (mkdocs)
│   ├── index.md
│   ├── installation.md
│   └── ... (more doc files)
├── pyproject.toml                   # Project configuration
├── mkdocs.yml                       # Documentation configuration
├── Dockerfile                       # Docker image definition
├── compose.yml                      # Docker Compose setup
├── README.md                        # Project overview
└── TESTING.md                       # Testing guide
```

## Core Application (`src/employee_dialogue/__init__.py`)

### Architecture Layers

```
User Browser
    ↓
Flask Routes (@app.route)
    ↓
Route Handlers (create_entry, edit_entry, etc.)
    ↓
Validation Functions (_validate_choice, _can_access_entry)
    ↓
SQLAlchemy Models (Entry, FinalEntry)
    ↓
SQLite Database (app.db)
```

### Module Organization

| Module         | Responsibility                          |
| -------------- | --------------------------------------- |
| **Models**     | `Entry`, `FinalEntry` - Database schema |
| **Routes**     | `/`, `/entries`, `/login`, etc.         |
| **Validators** | `_validate_choice`, `_can_access_entry` |
| **Auth**       | `login_required`, MSAL integration      |
| **Templates**  | HTML rendering for forms and views      |

## Database Schema

### Entry Table
Self-assessment entries created by employees

| Column             | Type              | Purpose                                   |
| ------------------ | ----------------- | ----------------------------------------- |
| id                 | Integer (PK)      | Unique identifier                         |
| name               | String            | Employee name (from Azure AD)             |
| email              | String            | Employee email                            |
| manager_name       | String            | Manager assigned from Graph API           |
| objective_rating   | String            | One of OBJECTIVE_CHOICES                  |
| objective_comment  | Text              | Employee's objective feedback             |
| technical_rating   | String            | One of ABILITY_CHOICES                    |
| project_rating     | String            | One of ABILITY_CHOICES                    |
| methodology_rating | String            | One of ABILITY_CHOICES                    |
| abilities_comment  | Text              | Context for ability ratings               |
| efficiency_*       | String (3 fields) | Collaboration, ownership, resourcefulness |
| efficiency_comment | Text              | Feedback on efficiency                    |
| conduct_*          | String (3 fields) | Trust, proactivity, leadership            |
| conduct_comment    | Text              | Feedback on conduct                       |
| general_comments   | Text              | Additional comments                       |
| feedback_received  | String            | Yes/No value                              |
| created_at         | DateTime          | When created                              |
| updated_at         | DateTime          | When last updated                         |

### FinalEntry Table
Manager-created final assessments

| Column             | Type            | Purpose                                            |
| ------------------ | --------------- | -------------------------------------------------- |
| id                 | Integer (PK)    | Unique identifier                                  |
| source_entry_id    | Integer (FK)    | Links to original Entry                            |
| name               | String          | Employee name                                      |
| email              | String          | Employee email                                     |
| manager_name       | String          | Manager conducting review                          |
| *manager_*_comment | Text (5 fields) | Manager feedback sections                          |
| goals_2026         | Text            | Goals for next period                              |
| ...                | ...             | (includes all Entry fields as read-only reference) |

## Static Assets Structure

```
static/
├── css/
│   └── style.css          # Base styles
├── js/
│   └── form-validation.js # Client-side validation
└── images/
    └── logo.png           # Application logo
```

## Templates Structure

### Template Inheritance

```
base.html (layout, navigation)
  ├── index.html (dashboard)
  ├── create.html (new entry form)
  ├── edit.html (edit entry form)
  └── final_edit.html (manager feedback form)
```

### Key Template Features

- **Form validation** - Client and server-side
- **Error messages** - Flash messages for feedback
- **Responsive design** - Mobile-friendly layout
- **Accessibility** - ARIA labels, semantic HTML

## Configuration Files

### pyproject.toml
- Project metadata (name, version, author)
- Dependencies (Flask, SQLAlchemy, etc.)
- Build system configuration (hatchling)
- Tool configurations (ruff, pytest, etc.)

### mkdocs.yml
- Documentation site configuration
- Navigation structure
- Theme and plugins
- Extensions for markdown

### Docker Files
- **Dockerfile** - Image definition with Python runtime
- **compose.yml** - Multi-container orchestration

## Key Constants

```python
# Azure AD Configuration
CLIENT_ID = "64326e78-7c64-4dd1-98d4-6bcfd6936c29"
TENANT_ID = "b3cd43f7-99bd-4233-8384-6f3a21adeced"
SCOPES = ["User.Read", "Directory.Read.All"]

# Validation Choices
OBJECTIVE_CHOICES = [
    "Exceeded objective",
    "Achieved objective",
    "Under-achieved objective",
    "Objective is obsolete or was changed",
]

ABILITY_CHOICES = [
    "Exceeds expectations",
    "Meets expectations",
    "Mostly in line",
    "Below expectations",
    "N/A",
]
```

## Import Organization

```python
# External imports
import os, uuid
from datetime import datetime, timezone
from functools import wraps

# Third-party imports
import msal, requests
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

# Local imports (none - single module)
```

## Next Steps

- [Data Model](data-model.md) - Detailed database schema
- [Authentication](authentication.md) - Auth flow and security
- [Development](../development/contributing.md) - Contributing guide
