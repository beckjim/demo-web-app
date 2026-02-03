# Data Model

Deep dive into the Employee Dialogue data model and database schema.

## Overview

Employee Dialogue uses SQLite with SQLAlchemy ORM for data persistence. The model supports two main entities:

1. **Entry** - Employee self-assessments
2. **FinalEntry** - Manager-created final performance reviews

## Entry Model

Self-assessment entries created by employees.

### Fields

#### Identity & Ownership
```python
id: Integer (Primary Key)
name: String(120)          # Employee name from Azure AD
email: String(120)         # Employee email
manager_name: String(120)  # Manager name from Graph API (nullable)
created_at: DateTime       # ISO 8601 UTC timestamp
updated_at: DateTime       # ISO 8601 UTC timestamp
```

#### Objective Assessment
```python
objective_rating: String(60)      # One of OBJECTIVE_CHOICES
objective_comment: Text           # Required, freeform text
```

Valid `objective_rating` values:
- "Exceeded objective"
- "Achieved objective"
- "Under-achieved objective"
- "Objective is obsolete or was changed"

#### Ability Assessment
```python
technical_rating: String(40)      # One of ABILITY_CHOICES
project_rating: String(40)        # One of ABILITY_CHOICES
methodology_rating: String(40)    # One of ABILITY_CHOICES
abilities_comment: Text           # Context for ratings
```

Valid rating values:
- "Exceeds expectations"
- "Meets expectations"
- "Mostly in line"
- "Below expectations"
- "N/A"

#### Efficiency Assessment
```python
efficiency_collaboration: String(40)         # Rating
efficiency_ownership: String(40)             # Rating
efficiency_resourcefulness: String(40)       # Rating
efficiency_comment: Text                     # Freeform feedback
```

#### Conduct Assessment
```python
conduct_mutual_trust: String(40)             # Rating
conduct_proactivity: String(40)              # Rating
conduct_leadership: String(40)               # Rating
conduct_comment: Text                        # Freeform feedback
```

#### General Information
```python
general_comments: Text             # Additional comments
feedback_received: String(10)      # "Yes" or "No"
```

### Constraints

```sql
-- All String and Text fields are NOT NULL with defaults
-- Defaults to empty string ('') for optional comments
-- PK (id) auto-increments
-- created_at and updated_at are auto-managed
```

## FinalEntry Model

Manager-created final assessment based on an Entry.

### Key Differences from Entry

1. **Linked to Entry**
   ```python
   source_entry_id: Integer (Foreign Key)  # References Entry.id
   ```

2. **Manager Fields**
   ```python
   manager_objective_comment: Text        # Manager feedback
   manager_abilities_comment: Text        # Manager feedback
   manager_efficiency_comment: Text       # Manager feedback
   manager_general_comments: Text         # Manager feedback
   goals_2026: Text                      # Goals for next period
   ```

3. **Read-Only Entry Fields**
   - All Entry fields are duplicated in FinalEntry
   - They're copied when FinalEntry is created
   - Updating Entry doesn't affect FinalEntry
   - Ensures assessment history immutability

### Field Structure

```python
# Identity
id, source_entry_id, name, email, manager_name

# Employee's self-assessment (copied from Entry)
objective_rating, objective_comment
technical_rating, project_rating, methodology_rating, abilities_comment
efficiency_collaboration, efficiency_ownership, efficiency_resourcefulness, efficiency_comment
conduct_mutual_trust, conduct_proactivity, conduct_leadership, conduct_comment
general_comments, feedback_received

# Manager's additions
manager_objective_comment
manager_abilities_comment
manager_efficiency_comment
goals_2026
manager_general_comments

# Timestamps
created_at, updated_at
```

## Relationships

### One-to-Many: Entry → FinalEntry

```
Entry (source_entry_id)
  ↓ (0 or 1)
FinalEntry
```

**Rules:**
- One Entry can have at most one FinalEntry
- FinalEntry requires a source_entry_id
- Deleting Entry should cascade to FinalEntry

**Implementation:**
```python
# In Entry route handlers
final_entry = FinalEntry.query.filter_by(source_entry_id=entry.id).first()
if final_entry:
    # Cannot edit Entry if FinalEntry exists
    return "Cannot edit: final assessment exists"
```

## Data Validation

### Server-Side Validation

```python
def _validate_choice(value: str, choices: list[str]) -> bool:
    return value in choices
```

Applied to:
- objective_rating
- technical_rating, project_rating, methodology_rating
- efficiency_collaboration, efficiency_ownership, efficiency_resourcefulness
- conduct_mutual_trust, conduct_proactivity, conduct_leadership

### Required Fields

**On Entry Creation:**
```python
Base: name, email
Objective: objective_rating, objective_comment (both required)
Abilities: technical_rating, project_rating, methodology_rating, abilities_comment
Efficiency: collaboration, ownership, resourcefulness, comment
Conduct: trust, proactivity, leadership, comment
General: general_comments, feedback_received
```

**On FinalEntry Creation:**
```python
Manager: objective_comment, abilities_comment, efficiency_comment, goals_2026, general_comments
```

### Access Control

```python
def _can_access_entry(entry: Entry, session_user: dict) -> bool:
    # Only entry owner can access (edit/delete)
    return entry.name.lower() == session_user['name'].lower()

def _can_manage_entry(entry: Entry, session_user: dict) -> bool:
    # Only manager can create/edit final assessment
    return entry.manager_name.lower() == session_user['name'].lower()
```

## Schema Initialization

### Migration Strategy

The application uses inline migrations via SQLAlchemy ALTER TABLE:

```python
with app.app_context():
    database.create_all()  # Create missing tables
    
    # Add missing columns
    cursor.execute(
        "ALTER TABLE entry ADD COLUMN new_field TEXT NOT NULL DEFAULT ''"
    )
```

Benefits:
- ✅ No separate migration files
- ✅ Works with SQLite
- ✅ Backward compatible
- ✅ Lightweight

## Timestamps

### Time Management

```python
def _utc_now():
    return datetime.now(timezone.utc)

# In models
created_at = database.Column(database.DateTime, default=_utc_now)
updated_at = database.Column(database.DateTime, default=_utc_now, onupdate=_utc_now)
```

**Guarantees:**
- ✅ All timestamps in UTC
- ✅ Timezone-aware
- ✅ Sortable chronologically
- ✅ ISO 8601 compliant

## Example Data

### Sample Entry

```python
entry = Entry(
    name="Jane Doe",
    email="jane.doe@company.com",
    manager_name="John Smith",
    objective_rating="Achieved objective",
    objective_comment="Successfully delivered Q4 project on time and within budget",
    technical_rating="Exceeds expectations",
    project_rating="Meets expectations",
    methodology_rating="Meets expectations",
    abilities_comment="Strong technical skills, could improve project planning",
    efficiency_collaboration="Meets expectations",
    efficiency_ownership="Exceeds expectations",
    efficiency_resourcefulness="Meets expectations",
    efficiency_comment="Collaborative team member with strong ownership mindset",
    conduct_mutual_trust="Exceeds expectations",
    conduct_proactivity="Meets expectations",
    conduct_leadership="Meets expectations",
    conduct_comment="Trustworthy and reliable team member",
    general_comments="Overall strong performer, ready for increased responsibilities",
    feedback_received="Yes"
)
```

## Query Examples

### Get employee's entry
```python
entry = Entry.query.filter(
    func.lower(Entry.name) == user_name.lower()
).first()
```

### Get manager's pending entries
```python
entries = Entry.query.filter(
    Entry.manager_name == user_name,
    ~Entry.id.in_(
        database.session.query(FinalEntry.source_entry_id)
    )
).all()
```

### Get final assessment for entry
```python
final = FinalEntry.query.filter_by(
    source_entry_id=entry.id
).first()
```

## Next Steps

- [Database Queries](../development/testing.md) - Testing the data model
- [API Reference](../api.md) - REST endpoint documentation
- [Architecture](structure.md) - Overall system design
