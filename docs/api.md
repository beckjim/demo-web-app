# API Reference

REST API endpoints and usage.

## Base URL

```
http://127.0.0.1:5000
https://yourdomain.com (production)
```

## Authentication

All endpoints except `/login` and `/logout` require authentication via Microsoft 365.

## Endpoints

### Public Routes

#### GET /login
Initiates Microsoft 365 sign-in flow.

**Response:** Redirect to Microsoft login page

```bash
curl http://localhost:5000/login -L
```

#### GET /auth/redirect
Callback endpoint after Microsoft authentication.

**Query Parameters:**
- `code` - Authorization code
- `state` - CSRF protection token

**Response:** Redirect to `/`

#### GET /logout
Signs out user and clears session.

**Response:** Redirect to Microsoft logout, then to `/`

```bash
curl http://localhost:5000/logout -L
```

### Dashboard

#### GET /
List all entries and dashboard overview.

**Requires:** Authentication

**Query Parameters:** None

**Response:** HTML dashboard

```bash
curl -b cookie.txt http://localhost:5000/
```

**Content:**
- User's own entries
- Managed entries (for managers)
- Final assessments
- Quick actions (Create, Edit, Delete)

### Entry Management

#### GET /entries/new
Display new entry form.

**Requires:** Authentication
**Methods:** GET

**Response:** HTML form

```bash
curl -b cookie.txt http://localhost:5000/entries/new
```

#### POST /entries
Create a new entry.

**Requires:** Authentication
**Content-Type:** application/x-www-form-urlencoded

**Request Body:**
```
objective_rating=Achieved objective
objective_comment=Met objectives
technical_rating=Meets expectations
project_rating=Meets expectations
methodology_rating=Meets expectations
abilities_comment=Solid technical skills
efficiency_collaboration=Meets expectations
efficiency_ownership=Exceeds expectations
efficiency_resourcefulness=Meets expectations
efficiency_comment=Strong ownership
conduct_mutual_trust=Exceeds expectations
conduct_proactivity=Meets expectations
conduct_leadership=Meets expectations
conduct_comment=Trustworthy
general_comments=Overall strong
feedback_received=Yes
```

**Response:** 302 Redirect to `/` on success

```bash
curl -b cookie.txt -X POST http://localhost:5000/entries \
  -d "objective_rating=Achieved objective" \
  -d "objective_comment=Met all goals"
  # ... other fields
```

#### GET /entries/<int:entry_id>/edit
Display edit form for entry.

**Requires:** Authentication + Ownership

**Response:** HTML form

```bash
curl -b cookie.txt http://localhost:5000/entries/1/edit
```

#### POST /entries/<int:entry_id>/edit
Update existing entry.

**Requires:** Authentication + Ownership
**Content-Type:** application/x-www-form-urlencoded

**Request Body:** Same as POST /entries

**Response:** 302 Redirect to `/`

```bash
curl -b cookie.txt -X POST http://localhost:5000/entries/1/edit \
  -d "objective_comment=Updated comment"
```

#### POST /entries/<int:entry_id>/delete
Delete an entry.

**Requires:** Authentication + Ownership
**Methods:** POST

**Response:** 302 Redirect to `/`

```bash
curl -b cookie.txt -X POST http://localhost:5000/entries/1/delete
```

### Manager Functions

#### POST /entries/<int:entry_id>/finalize
Create final assessment from employee's self-assessment.

**Requires:** Authentication + Manager Role

**Response:** 302 Redirect to `/final_entries/<id>/edit`

```bash
curl -b cookie.txt -X POST http://localhost:5000/entries/1/finalize
```

#### GET /final_entries/<int:final_id>/edit
Display manager feedback form.

**Requires:** Authentication + Manager Role

**Response:** HTML form

```bash
curl -b cookie.txt http://localhost:5000/final_entries/1/edit
```

#### POST /final_entries/<int:final_id>/edit
Submit manager feedback.

**Requires:** Authentication + Manager Role

**Request Body:**
```
manager_objective_comment=Achieved all objectives
manager_abilities_comment=Strong technical skills
manager_efficiency_comment=Excellent collaborator
goals_2026=Lead project X, improve Y
manager_general_comments=Ready for advancement
```

**Response:** 302 Redirect to `/`

```bash
curl -b cookie.txt -X POST http://localhost:5000/final_entries/1/edit \
  -d "manager_objective_comment=Exceeded expectations"
```

#### POST /final_entries/<int:final_id>/delete
Delete final assessment.

**Requires:** Authentication + Manager Role

**Response:** 302 Redirect to `/`

```bash
curl -b cookie.txt -X POST http://localhost:5000/final_entries/1/delete
```

## Response Codes

| Code | Meaning            | Example                 |
| ---- | ------------------ | ----------------------- |
| 200  | OK                 | GET request successful  |
| 302  | Redirect           | Form submission success |
| 304  | Not Modified       | Cached response         |
| 400  | Bad Request        | Invalid form data       |
| 404  | Not Found          | Entry doesn't exist     |
| 405  | Method Not Allowed | Wrong HTTP method       |
| 500  | Server Error       | Application error       |

## Error Handling

### Flash Messages

Errors appear as flash messages in the UI:

```python
flash("All fields must be completed with valid options", "error")
flash("Entry created", "success")
```

### Validation Errors

Invalid data returns 302 redirect with error message:

```
POST /entries
→ Validation fails
→ Flash error message
→ 302 redirect to /
```

## Rate Limiting

Currently no rate limiting. Production deployments should implement:

- Per-user limits
- Per-IP limits
- Database operation throttling

## Pagination

Currently no pagination. Entries are returned in full list.

**Future enhancement:**
```
GET /entries?page=1&limit=10
```

## Caching

- Sessions: Server-side (Flask sessions)
- Static files: Browser cache
- Database: No explicit caching

## Security

- ✅ CSRF protection (state parameter)
- ✅ XSS prevention (Jinja2 escaping)
- ✅ SQL injection prevention (ORM)
- ✅ Access control on all routes
- ✅ Session-based authentication

## Examples

### Create Entry with curl

```bash
# Set up session cookie
curl -c cookie.txt http://localhost:5000/login

# Create entry
curl -b cookie.txt -X POST http://localhost:5000/entries \
  -d "objective_rating=Achieved objective" \
  -d "objective_comment=Met objectives" \
  # ... more fields
```

### Using Python requests

```python
import requests

session = requests.Session()
session.post("http://localhost:5000/login")

response = session.post("http://localhost:5000/entries", data={
    "objective_rating": "Achieved objective",
    "objective_comment": "Met objectives",
    # ... more fields
})

print(response.status_code)
print(response.text)
```

## Next Steps

- [Configuration](configuration.md) - API configuration
- [Deployment](deployment.md) - Deploy the API
