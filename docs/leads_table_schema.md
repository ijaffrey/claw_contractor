# Leads Table Schema Documentation

## Table: nyc_dob_leads

### Purpose
Stores NYC DOB contractor lead data with qualification scoring and contact tracking.
Based on NYC DOB API response structure analysis and existing SQLite database patterns.

### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, INDEX | Unique identifier |
| job_number | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | NYC DOB job number |
| job_type | VARCHAR(100) | | Type of construction job |
| job_description | TEXT | | Detailed job description |
| owner_name | VARCHAR(200) | INDEX | Property owner name |
| owner_phone | VARCHAR(20) | | Contact phone number |
| owner_business_name | VARCHAR(200) | | Owner's business name |
| owner_house_number | VARCHAR(20) | | Owner address house number |
| owner_house_street | VARCHAR(200) | | Owner address street |
| owner_city | VARCHAR(100) | | Owner address city |
| owner_state | VARCHAR(10) | | Owner address state |
| owner_zip | VARCHAR(10) | INDEX | Owner address ZIP code |
| site_house_number | VARCHAR(20) | | Job site house number |
| site_house_street | VARCHAR(200) | | Job site street |
| site_city | VARCHAR(100) | | Job site city |
| site_state | VARCHAR(10) | | Job site state |
| site_zip | VARCHAR(10) | INDEX | Job site ZIP code |
| work_type | VARCHAR(100) | INDEX | Type of work being performed |
| permit_sequence | INTEGER | | Permit sequence number |
| permit_subtype | VARCHAR(100) | | Permit subtype |
| filing_status | VARCHAR(50) | | Current filing status |
| status_date | DATE | INDEX | Date of status change |
| job_start_date | DATE | | Scheduled job start date |
| permittee_license_number | VARCHAR(50) | | Contractor license number |
| permittee_license_type | VARCHAR(50) | | Type of contractor license |
| work_on_floor | VARCHAR(20) | | Floor where work is performed |
| estimated_job_costs | DECIMAL(12,2) | | Estimated project cost |
| qualification_score | INTEGER | DEFAULT 0, INDEX | Lead qualification score (0-100) |
| is_qualified | BOOLEAN | DEFAULT FALSE, INDEX | Whether lead meets qualification criteria |
| contact_attempted | BOOLEAN | DEFAULT FALSE | Whether contact has been attempted |
| created_at | DATETIME | DEFAULT utcnow(), NOT NULL, INDEX | Record creation timestamp |
| updated_at | DATETIME | DEFAULT utcnow(), onupdate=utcnow() | Last update timestamp |

### Indexes

- `id`: Primary key lookup
- `job_number`: Unique job number lookup (UNIQUE)
- `owner_name`: Owner name search
- `owner_zip`: Geographic filtering by owner location
- `site_zip`: Geographic filtering by job site
- `work_type`: Work type filtering
- `qualification_score`: Qualification score ordering
- `is_qualified`: Qualified leads filtering
- `status_date`: Recent activity filtering
- `created_at`: Chronological ordering

### Data Validation Rules

1. **job_number**: Must be unique across all records
2. **Phone numbers**: Should follow standard US format validation
3. **ZIP codes**: Should be 5 or 9 digit US ZIP codes
4. **qualification_score**: Range 0-100
5. **Dates**: status_date and job_start_date should not be in distant past
6. **estimated_job_costs**: Should be positive values
7. **Boolean fields**: is_qualified and contact_attempted default to False

### NYC DOB API Response Structure Analysis

Based on analysis of NYC DOB API endpoint:
`https://data.cityofnewyork.us/api/views/ipu4-2q9a/rows.json`

The API provides construction permit and inspection data with fields including:
- Job identification numbers
- Property owner information
- Job site addresses
- Work type classifications
- Permit status and dates
- Estimated costs
- Contractor license information

### Usage Patterns

- **Lead Import**: Bulk insert from NYC DOB API responses
- **Qualification**: Update qualification_score and is_qualified fields
- **Contact Tracking**: Update contact_attempted flag
- **Geographic Queries**: Filter by owner_zip or site_zip
- **Scoring Queries**: Order by qualification_score DESC
- **Status Filtering**: Filter by is_qualified for qualified leads
- **Temporal Queries**: Filter by status_date or created_at for recent activity

### Integration Points

- **lead_adapter.py**: Normalizes NYC DOB API data to this schema
- **database_manager.py**: Handles CRUD operations for lead records
- **qualified_lead_detector.py**: Updates qualification_score and is_qualified
- **conversation_manager.py**: Links to conversation tracking for contact management
- **contractor_notifier.py**: Queries qualified leads for notification

### Performance Considerations

- Multiple indexes support common query patterns
- qualification_score index enables efficient scoring queries
- Geographic indexes (owner_zip, site_zip) support location-based filtering
- Temporal indexes (status_date, created_at) support time-based queries
- Unique constraint on job_number prevents duplicate lead entries

### Database Technology

Currently using SQLite with SQLAlchemy ORM, following existing patterns in:
- `database.py`: Database session management
- `test_database.py`: Connection testing patterns
- `infrastructure/`: Migration script location
