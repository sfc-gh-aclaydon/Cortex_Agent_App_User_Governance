# Secure Multi-User Analytics with Snowflake Cortex Analyst

A proof-of-concept application that enables multiple users to query structured data using natural language through Snowflake's Cortex Analyst REST API, while ensuring each user only sees data relevant to their access permissions.

## Features

- **Natural Language Queries**: Ask questions in plain English and get SQL-powered answers
- **Row-Level Security**: Users see only data they're authorized to access based on regions
- **SQL Masking**: Security predicates are hidden from user-visible SQL queries
- **Multi-User Support**: Different users get different data views automatically
- **Snowflake Integration**: Uses Cortex Analyst REST API for query processing

## Architecture

- **Backend**: Python Flask with Snowflake integration
- **Frontend**: Simple Bootstrap-based SPA
- **Security**: Row Access Policies (RAPs) with session context injection
- **Database**: Snowflake (MAPS_SEARCH_ANALYTICS.APPLICATION schema)

## Prerequisites

- Python 3.11
- Snowflake account with Cortex Analyst enabled
- Docker (optional, for containerized deployment)

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp env.example .env

# Edit .env with your Snowflake credentials
# You need: SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_ACCOUNT, SNOWFLAKE_ROLE
# Database will be MAPS_SEARCH_ANALYTICS with APPLICATION schema
```

### 2. Database Setup

Run the SQL scripts in Snowflake to create the required schema and data:

```sql
-- See setup_database.sql for complete setup instructions
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

#### Local Development
```bash
python app.py
```

#### Docker
```bash
docker-compose up --build
```

### 5. Access the Application

Open your browser to: http://localhost:8080

## Demo Users

The application includes three demo users with different regional access:

- **alice.smith** - Access to North America & Europe
- **bob.jones** - Access to North America only  
- **carol.wong** - Access to Asia Pacific & Latin America

Password for all demo users: `password123`

## Sample Questions

Try these natural language queries:

- "What were our total sales by region last quarter?"
- "Which customers had the highest revenue this year?"
- "Show me software sales by quarter"
- "What's our top performing product category?"
- "Which sales rep had the most deals?"

## Project Structure

```
analytics_app/
├── app.py                  # Main Flask application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── models/
│   ├── user.py            # User and Region models
│   └── database.py        # Snowflake connection management
├── services/
│   ├── auth_service.py    # Authentication logic
│   ├── query_service.py   # Cortex Analyst integration
│   └── sql_masker.py      # SQL masking for security
├── templates/
│   ├── login.html         # Login page
│   └── dashboard.html     # Main dashboard
# semantic_model.yaml no longer needed - using semantic view in database
├── Dockerfile
├── docker-compose.yml
└── env.example            # Environment variables template
```

## Security Features

### Row Access Policies (RAPs)
- Automatically filter data based on user's accessible regions
- Session context injection for user identification
- Transparent to Cortex Analyst query generation

### SQL Masking
- Remove security predicates from user-visible SQL
- Preserve business logic while hiding security filters
- Fallback to generic message if masking fails

### Authentication
- Secure password hashing with bcrypt
- Session-based authentication with timeouts
- User region mapping for access control

## Development

### Adding New Users
1. Insert user record in `USERS` table with hashed password
2. Add region mappings in `USER_REGION_MAPPING` table
3. User will automatically get filtered data access

### Adding New Regions
1. Insert region in `REGIONS` table
2. Add sample data in `SALES_DATA` with the new region_id
3. Assign users to regions via `USER_REGION_MAPPING`

### Customizing the Semantic View
The semantic view is created in the database setup script. To customize:
- Edit the CREATE SEMANTIC VIEW statement in `setup_database.sql`
- Add new tables, dimensions, or metrics
- Update table descriptions and comments for better query understanding
- Re-run the semantic view creation after making changes

## Troubleshooting

### Common Issues

1. **Authentication Fails**: Check Snowflake credentials in .env file
2. **No Data Returned**: Verify user has region mappings in USER_REGION_MAPPING
3. **Cortex Analyst Errors**: Ensure semantic view was created successfully in the database
4. **Connection Issues**: Check Snowflake account identifier and network access

### Health Check

The application provides a health endpoint:
```
GET /health
```

### Logs

Application logs are available in:
- Console output (development)
- `/app/logs/` directory (Docker)

## Production Considerations

This is a proof-of-concept. For production use, consider:

- OAuth/SAML authentication integration
- Advanced audit logging and monitoring
- Connection pooling and caching
- Rate limiting and DDoS protection
- HTTPS termination and security headers
- Multi-environment deployment strategies

## License

This project is for demonstration purposes.
