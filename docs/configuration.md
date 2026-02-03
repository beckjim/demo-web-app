# Configuration

Configure Employee Dialogue for your environment.

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Flask configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Microsoft Entra (Azure AD)
AZURE_AD_CLIENT_SECRET=your_client_secret

# Database (optional)
DATABASE_URL=sqlite:///app.db
```

## Required Configuration

### SECRET_KEY

Used for Flask session encryption and CSRF protection.

**Development:**
```env
SECRET_KEY=dev-secret-key-unsafe-only-for-development
```

**Production:**
```bash
# Generate a secure key
python -c "import secrets; print(secrets.token_hex(32))"
```

Then set it in `.env`:
```env
SECRET_KEY=generated_value_from_above
```

### AZURE_AD_CLIENT_SECRET

The client secret from your Azure AD application registration.

1. Go to [Azure Portal](https://portal.azure.com)
2. Select **App registrations**
3. Choose your registered application
4. Navigate to **Certificates & secrets**
5. Copy the **client secret value**
6. Add to `.env`:
```env
AZURE_AD_CLIENT_SECRET=your_copied_secret
```

!!! warning
    Never commit secrets to version control. Use `.env` and add it to `.gitignore`.

## Optional Configuration

### Database Configuration

By default, SQLite database is stored at `app.db` in the project root.

To use a different location:
```env
DATABASE_URL=sqlite:///path/to/your/app.db
```

### Flask Debug Mode

```env
FLASK_ENV=development    # Enable debug mode
FLASK_ENV=production     # Disable debug mode
```

### Logging

The application uses Python's built-in logging. For production deployments, configure log levels:

```python
# In src/employee_dialogue/__init__.py
import logging
app.logger.setLevel(logging.INFO)
```

## Azure AD Configuration

### App Registration Settings

Required settings in Azure Portal:

| Setting             | Value                                 |
| ------------------- | ------------------------------------- |
| Redirect URI        | `http://127.0.0.1:5000/auth/redirect` |
| Token Configuration | Add groups claim                      |
| API Permissions     | `User.Read`, `Directory.Read.All`     |
| Admin Consent       | Required                              |

### API Permissions

1. Go to **App registrations** → Your app
2. Select **API permissions**
3. Add **Microsoft Graph** permissions:
   - `User.Read` (Delegated)
   - `Directory.Read.All` (Application)

4. Request **Admin consent**

## Deployment Configuration

### Environment-Specific Settings

**Staging:**
```env
FLASK_ENV=staging
SECRET_KEY=staging-secret-key
DEBUG=False
```

**Production:**
```env
FLASK_ENV=production
SECRET_KEY=very-long-cryptographically-secure-key
DEBUG=False
DATABASE_URL=postgresql://user:pass@db-host/dbname
```

### Docker Configuration

Use environment variables when running Docker:

```bash
docker run -e FLASK_ENV=production \
           -e SECRET_KEY=your-key \
           -e AZURE_AD_CLIENT_SECRET=your-secret \
           employee-dialogue
```

Or in `docker-compose.yml`:

```yaml
services:
  web:
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - AZURE_AD_CLIENT_SECRET=${AZURE_AD_CLIENT_SECRET}
```

## Verifying Configuration

Check that configuration is loaded correctly:

```bash
uv run python -c "from employee_dialogue import app; print(app.config)"
```

## Troubleshooting

### Configuration not loading

1. Verify `.env` file exists in project root
2. Check file permissions (should be readable)
3. Restart Flask application after changing `.env`

### Manager field not prefilling

- Ensure `Directory.Read.All` permission is granted
- Request **admin consent** in Azure Portal
- Check server logs: `app.logger.warning()`

### CSRF token errors

- Ensure `SECRET_KEY` is set
- Clear browser cookies
- Verify session configuration

## Next Steps

- [Getting Started](getting-started.md) - Run the application
- [Azure AD Setup](architecture/authentication.md) - Detailed auth configuration
- [Deployment](deployment.md) - Deploy to production
