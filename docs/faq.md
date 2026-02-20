# FAQ

Frequently asked questions about Employee Dialogue.

## General Questions

### What is Employee Dialogue?

Employee Dialogue is a web-based performance management application that enables:
- Employees to complete self-assessments
- Managers to provide feedback
- Organizations to track performance systematically

### Who can use it?

Anyone with a Microsoft 365 account in your organization. Authentication is automatic via Microsoft Entra (Azure AD).

### Is it free?

Employee Dialogue is open-source and free to use. You only pay for:
- Hosting infrastructure
- Microsoft 365 licenses (usually already owned)

### What data does it store?

- Employee self-assessments
- Manager feedback
- User authentication info (from Azure AD)
- Manager information (from Microsoft Graph)

It does NOT store:
- Passwords (handled by Microsoft)
- Credit card information
- Personal data beyond what you enter

## Installation & Setup

### Do I need to install anything?

Yes:
- Python 3.9+
- Dependencies (automatically installed)
- Optional: Docker for containerized deployment

### How do I set it up?

1. Follow [Installation Guide](installation.md)
2. Create .env file with secrets
3. Register app in Azure AD
4. Run `uv run flask --app employee_dialogue run --debug`

See [Getting Started](getting-started.md) for detailed steps.

### Can I use it without Microsoft 365?

Currently no - authentication requires Microsoft Entra. Alternative auth methods could be implemented via pull requests.

### How do I get the Azure AD secrets?

See [Configuration - Azure AD Configuration](configuration.md#azure-ad-configuration)

## Usage

### Can employees edit their assessment after submitting?

Yes, until the manager creates a final assessment. Once a final assessment exists, the self-assessment becomes read-only.

### Can I delete an entry?

Yes, employees can delete their own entries. Managers can delete final assessments. Deleted data cannot be recovered.

### What if I made a mistake?

Before final assessment:
- Click Edit
- Update information
- Save changes

After final assessment:
- Contact system administrator
- Provide reason for change
- Request entry restoration

### How do managers see employee assessments?

Managers see:
- A list of their employees' self-assessments
- Status of each (pending, completed, etc.)
- Link to review and create final assessment

### Can employees see their manager's feedback immediately?

Yes - as soon as the manager submits the final assessment, the employee receives a notification and can view the feedback.

## Technical Questions

### What database does it use?

SQLite by default (suitable for up to 50-100 concurrent users). PostgreSQL recommended for larger deployments.

### Can I use it with a different database?

Yes - modify DATABASE_URL in .env to point to PostgreSQL, MySQL, etc.

### Is the data encrypted?

- At rest: No (depends on OS-level encryption)
- In transit: Yes (HTTPS recommended in production)
- Sessions: Yes (Flask session encryption)

Sensitive data is not encrypted at rest by default. Add encryption if required by your security policies.

### How many users can it support?

- **SQLite**: 50-100 concurrent users
- **PostgreSQL**: 1000+ concurrent users
- **Scaling**: Run multiple instances behind load balancer

### What are the system requirements?

**Minimum:**
- 1 GB RAM
- 100 MB disk space
- Python 3.9

**Recommended (production):**
- 4 GB RAM
- 10 GB disk space
- Python 3.11+
- Dedicated server or cloud instance

### Can I run it on a Raspberry Pi?

Technically yes, but not recommended. It will be slow for multiple concurrent users.

## Customization

### Can I change the colors/branding?

Yes - edit `src/employee_dialogue/templates/base.html` and `src/employee_dialogue/static/css/style.css`

### Can I add more assessment fields?

Yes - requires:
1. Add column to Entry/FinalEntry model
2. Update database (ALTER TABLE)
3. Update form templates
4. Add validation if needed
5. Update tests

### Can I customize the evaluation criteria?

Yes - modify `OBJECTIVE_CHOICES` and `ABILITY_CHOICES` in `src/employee_dialogue/__init__.py`

### Can I integrate with other HR systems?

Not built-in, but possible via:
- REST API (planned enhancement)
- Database queries
- Custom export scripts
- Webhooks (future feature)

## Performance & Reliability

### Is it fast?

Yes - response times are typically <200ms for regular operations. Graph API calls for manager lookup can take 1-2 seconds.

### What if the server goes down?

All submitted assessments are saved. No data is lost. When server comes back up, everything is accessible.

### How often do I need to back up data?

- **Development**: Not necessary
- **Staging**: Weekly
- **Production**: Daily

Use the backup procedures in [Deployment Guide](deployment.md)

### Does it have automatic backups?

No - you must set up backups yourself (cron job, cloud storage, etc.)

## Security & Privacy

### Is it secure?

It includes:
- ✅ CSRF protection
- ✅ XSS prevention
- ✅ SQL injection prevention
- ✅ Session-based authentication
- ✅ Access control

Recommendations:
- Use HTTPS in production
- Keep dependencies updated
- Regular security audits
- Strong SECRET_KEY

### Can I export data?

Currently data is stored in database. Future versions may include:
- PDF export
- CSV export
- JSON export

### How long is data retained?

By default, forever. Implement data retention policies if needed:
- Archive old entries
- Delete entries after N years
- GDPR compliance procedures

### How is access controlled?

- Employees can only access/edit their own entries
- Managers can only see their direct reports
- Admins can access everything
- All actions are logged (implemented in monitoring)

## Troubleshooting

### I'm getting "State mismatch" error

This is a CSRF protection mechanism. It means:
- Session didn't persist between requests
- SECRET_KEY is not set or wrong
- Different host/port than registered in Azure AD

**Solutions:**
1. Check .env has SECRET_KEY set
2. Clear browser cookies
3. Verify redirect URI matches exactly

See [Authentication Troubleshooting](architecture/authentication.md#troubleshooting)

### Manager field is empty

The app couldn't fetch manager from Microsoft Graph. Reasons:
- User has no manager assigned in Azure AD
- Directory.Read.All permission not granted
- Network timeout

The app works fine without manager info - it's optional.

### My entry disappeared

Possible causes:
- Browser cache issue (try hard refresh Ctrl+Shift+R)
- You deleted it
- Database corrupted (restore from backup)

**Check:**
1. Reload page
2. Check browser history
3. Check database backups

### Form won't submit

Possible causes:
- Missing required fields
- Invalid ratings selected
- Session expired (try logging in again)
- JavaScript disabled (enable it)

Check browser console for errors (F12 → Console tab)

## Contributing & Development

### I found a bug!

Please report it:
1. Go to [GitHub Issues](https://github.com/beckjim/employee-dialogue/issues)
2. Click "New Issue"
3. Describe the bug with steps to reproduce
4. Include error message and logs

### Can I contribute code?

Yes! See [Contributing Guide](development/contributing.md)

### How do I run tests?

```bash
uv run pytest tests/ -v
```

See [Testing Guide](development/testing.md)

### How do I build the documentation?

```bash
pip install mkdocs mkdocs-material
mkdocs serve
```

## Contact & Support

### Where can I get help?

1. Check this FAQ
2. Read [Documentation](index.md)
3. Search [GitHub Issues](https://github.com/beckjim/employee-dialogue/issues)
4. Create new issue or discussion

### How do I report security issues?

Please email: security@example.com (do not create public issue)

Include:
- Description of vulnerability
- Steps to reproduce
- Impact assessment
- Suggested fix (if any)

### Is there commercial support?

Currently no. Community support available via GitHub.

## License & Legal

### What license is it under?

MIT License - free to use, modify, and distribute. See LICENSE file.

### Do I need to acknowledge the project?

No, but it's appreciated! Attribution is not required.

### Can I use it commercially?

Yes - the MIT license allows commercial use.

### What about GDPR compliance?

Employee Dialogue stores personal data. You must:
- Have legal basis for processing
- Provide data access/export to users
- Implement data retention policies
- Encrypt data in transit and at rest
- Conduct privacy impact assessment

See your organization's legal/compliance team.

## More Questions?

Can't find the answer? 

1. Check other documentation pages
2. Search GitHub issues
3. Create a new issue
4. Ask in discussions

---

**Last updated:** February 2026
**Documentation version:** 0.1.0
