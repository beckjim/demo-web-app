# Authentication

Understanding Microsoft 365 authentication in Employee Dialogue.

## Overview

Employee Dialogue uses **OpenID Connect** and **OAuth 2.0** for authentication via Microsoft Entra (Azure AD).

## Authentication Flow

```
1. User clicks "Sign in with Microsoft"
   ↓
2. Redirected to Microsoft login page
   ↓
3. User authenticates with their account
   ↓
4. Microsoft redirects back with authorization code
   ↓
5. Backend exchanges code for tokens
   ↓
6. Backend fetches user info from Microsoft Graph
   ↓
7. Session created and user redirected to dashboard
```

## Technical Implementation

### Libraries

- **msal** - Microsoft Authentication Library for Python
- **requests** - HTTP client for Graph API calls

### Configuration

```python
CLIENT_ID = "64326e78-7c64-4dd1-98d4-6bcfd6936c29"
TENANT_ID = "b3cd43f7-99bd-4233-8384-6f3a21adeced"
CLIENT_SECRET = os.environ.get("AZURE_AD_CLIENT_SECRET")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["User.Read", "Directory.Read.All"]
```

## Routes

### `/login`
Initiates authentication flow

**Action:**
1. Generate random `state` for CSRF protection
2. Build authorization URL
3. Redirect to Microsoft login

```python
@app.route("/login")
def login():
    session["state"] = str(uuid.uuid4())
    auth_url = _build_msal_app().get_authorization_request_url(
        scopes=SCOPES,
        state=session["state"],
        redirect_uri=_redirect_uri(),
    )
    return redirect(auth_url)
```

### `/auth/redirect`
Callback from Microsoft after user authenticates

**Actions:**
1. Validate state parameter (CSRF check)
2. Exchange authorization code for tokens
3. Extract user information from ID token
4. Fetch manager name from Microsoft Graph
5. Create session
6. Redirect to dashboard

```python
@app.route("/auth/redirect")
def authorized():
    state = request.args.get("state")
    if state != session.get("state"):
        flash("State mismatch. Please try signing in again.", "error")
        return redirect(url_for("index"))
    
    code = request.args.get("code")
    result = _build_msal_app().acquire_token_by_authorization_code(
        code=code,
        scopes=SCOPES,
        redirect_uri=_redirect_uri(),
    )
    
    # Extract claims and create session
    claims = result.get("id_token_claims", {})
    session["user"] = {
        "name": claims.get("name"),
        "email": claims.get("preferred_username"),
        "oid": claims.get("oid"),
        "manager_name": _fetch_manager_name(access_token),
    }
    
    return redirect(url_for("index"))
```

### `/logout`
Signs user out

**Actions:**
1. Clear local session
2. Redirect to Microsoft logout endpoint
3. Redirect back to home page

```python
@app.route("/logout")
def logout():
    session.clear()
    post_logout = url_for("index", _external=True)
    return redirect(
        f"{AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri={post_logout}"
    )
```

## Session Management

### Session Data Structure

```python
session["user"] = {
    "name": "Jane Doe",                    # Display name
    "email": "jane.doe@company.com",      # Email address
    "oid": "12345-67890-...",             # Azure AD Object ID
    "manager_name": "John Smith",         # Manager name from Graph
}
```

### Session Security

- ✅ Flask session encryption (SECRET_KEY)
- ✅ CSRF protection (state parameter)
- ✅ HTTPS recommended in production
- ✅ Secure cookie flags enforced

## Microsoft Graph Integration

### Manager Lookup

The application fetches the manager name via Microsoft Graph API.

```python
def _fetch_manager_name(access_token: str) -> str:
    response = requests.get(
        "https://graph.microsoft.com/v1.0/me/manager",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=5,
    )
    
    if response.status_code == 200:
        data = response.json()
        return data.get("displayName") or data.get("mail") or ""
    return ""
```

**Endpoint:** `GET /me/manager`

**Requires:** `Directory.Read.All` permission

**Error Handling:**
- 404 (No manager) → Return empty string
- Timeout → Log warning, continue
- Other errors → Log exception, return empty string

## Azure AD Configuration

### App Registration

**Required Settings in Azure Portal:**

| Setting       | Value                                 |
| ------------- | ------------------------------------- |
| Name          | Employee Dialogue                     |
| Redirect URI  | `http://127.0.0.1:5000/auth/redirect` |
| Token Config  | Add groups claim                      |
| Client Secret | (Generate and store securely)         |

### API Permissions

**Required Permissions:**

1. **Microsoft Graph**
   - `User.Read` (Delegated)
   - `Directory.Read.All` (Delegated)

2. **Grant Admin Consent**
   - Navigate to API permissions
   - Click "Grant admin consent for [Organization]"
   - Required for Directory.Read.All

### Redirect URI

Must exactly match:
- Development: `http://127.0.0.1:5000/auth/redirect`
- Staging: `https://staging.yourdomain.com/auth/redirect`
- Production: `https://yourdomain.com/auth/redirect`

## Security Considerations

### Best Practices

✅ **Do:**
- Store `CLIENT_SECRET` in environment variables
- Use HTTPS in production
- Validate state parameter (prevents CSRF)
- Use HTTPOnly cookies for session
- Keep MSAL and requests libraries updated

❌ **Don't:**
- Hardcode secrets in code
- Use HTTP in production
- Skip state validation
- Log tokens or sensitive data
- Use old/deprecated MSAL versions

### Token Management

- **ID Token** - Contains user claims (name, email, oid)
- **Access Token** - Used for Graph API calls
- **Refresh Token** - Obtained but not used (session-based)

Tokens are:
- Validated server-side
- Never sent to client
- Expired after session timeout

## Troubleshooting

### "State mismatch"

**Causes:**
- Session not persisted between requests
- Different hosts/ports
- Cookies disabled

**Solutions:**
1. Check SECRET_KEY is set in .env
2. Verify redirect URI matches exactly
3. Clear browser cookies
4. Check Flask session middleware

### "Manager not prefilled"

**Causes:**
- Missing Directory.Read.All permission
- No admin consent granted
- User has no manager assigned
- Network timeout

**Solutions:**
1. Request admin consent in Azure Portal
2. Check API permissions
3. Verify user has manager in Azure AD
4. Check server logs for Graph errors

### "Login fails with error"

**Check:**
- CLIENT_ID matches Azure AD registration
- CLIENT_SECRET is correct and not expired
- Redirect URI exactly matches Azure AD
- AZURE_AD_CLIENT_SECRET env variable set
- Network connectivity to Microsoft services

## Next Steps

- [Configuration](../configuration.md) - Azure AD setup
- [Security Best Practices](../development/contributing.md) - Secure coding
