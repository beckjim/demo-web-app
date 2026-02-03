# Getting Started

Get up and running with Employee Dialogue in minutes.

## Prerequisites

- **Python 3.9+**
- **pip** or **uv** package manager
- **Git** (optional, for cloning)
- **Microsoft 365 Account** (for authentication testing)

## Installation

### 1. Clone or Download the Repository

```bash
git clone https://github.com/beckjim/employee-dialogue.git
cd employee-dialogue
```

### 2. Set Up Python Environment

#### Using uv (Recommended)

```bash
pip install uv
uv venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # macOS/Linux
uv sync
```

#### Using pip and venv

```bash
python -m venv .venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
AZURE_AD_CLIENT_SECRET=your_client_secret_from_azure
```

!!! note
    For development, you can use a simple string for `SECRET_KEY`. In production, use a cryptographically secure value.

### 4. Set Up Azure AD Application

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **App registrations**
3. Click **New registration**
4. Configure:
   - **Name**: Employee Dialogue
   - **Supported account types**: Accounts in this organizational directory only
   - **Redirect URI**: `http://localhost:5000/auth/redirect`
5. Create a **Client Secret** and copy its value to `.env`

### 5. Run the Application

```bash
uv run flask --app employee_dialogue run --debug
```

The application will start at `http://127.0.0.1:5000`

## First Steps

1. Open your browser to `http://127.0.0.1:5000`
2. Click **Sign in with Microsoft**
3. Authenticate with your Microsoft 365 account
4. You'll be redirected to the dashboard

## Troubleshooting

### "AZURE_AD_CLIENT_SECRET not set"
- Ensure your `.env` file exists and contains `AZURE_AD_CLIENT_SECRET`
- Restart the Flask application after updating `.env`

### "State mismatch" during login
- This usually means session persistence issues
- Clear browser cookies and try again
- Ensure `SECRET_KEY` is set in `.env`

### Manager not prefilled
- The app requires `Directory.Read.All` permission in Azure AD
- Request admin consent in Azure Portal
- Network timeout might occur; check logs for Graph API errors

## Next Steps

- [Configuration Guide](configuration.md) - Advanced setup options
- [Usage Guide](usage/creating-entries.md) - Learn how to use the app
- [Architecture](architecture/structure.md) - Understand the codebase
