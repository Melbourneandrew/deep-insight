# Business Seeding API

## Overview

The business creation API has been enhanced to support seeding new businesses with initial employees and questions. When creating a business, you can optionally provide seed data, or the system will use default seed data.

## API Endpoint

**POST** `/businesses/`

## Request Schema

### Basic Business Creation (uses default seed data)

```json
{
  "name": "My Company Name"
}
```

### Business Creation with Custom Seed Data

```json
{
  "name": "My Company Name",
  "seed_data": {
    "employees": [
      {
        "email": "john.doe@company.com",
        "bio": "Senior Software Engineer with 8 years of experience"
      },
      {
        "email": "jane.smith@company.com",
        "bio": "Product Manager with expertise in user experience"
      }
    ],
    "questions": [
      {
        "content": "What motivates you most in your current role?",
        "is_follow_up": false
      },
      {
        "content": "Can you elaborate on that experience?",
        "is_follow_up": true
      }
    ]
  }
}
```

## Schema Details

### CreateBusinessRequest

- `name` (string, required): The name of the business
- `seed_data` (BusinessSeedData, optional): Initial data to seed the business with

### BusinessSeedData

- `employees` (array of EmployeeSeedData, optional): List of employees to create
- `questions` (array of QuestionSeedData, optional): List of questions to create

### EmployeeSeedData

- `email` (string, required): Employee's email address (must be unique)
- `bio` (string, optional): Employee's biography/description

### QuestionSeedData

- `content` (string, required): The question text
- `is_follow_up` (boolean, optional): Whether this is a follow-up question (defaults to false)

## Default Seed Data

If no `seed_data` is provided, the system will automatically seed the business with:

- **5 default employees** with sample bios and email addresses
- **13 default questions** including both regular and follow-up questions

The default seed data is loaded from `/backend/app/default_business_seed.json`.

## Response

The API returns the created business object with the generated UUID and name:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "My Company Name"
}
```

## Example Usage

### cURL Example

```bash
# Create business with default seed data
curl -X POST "http://localhost:8000/businesses/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Tech Startup Inc"}'

# Create business with custom seed data
curl -X POST "http://localhost:8000/businesses/" \
  -H "Content-Type: application/json" \
  -d @example_business_seed.json
```

### Python Example

```python
import requests

# Basic creation
response = requests.post(
    "http://localhost:8000/businesses/",
    json={"name": "My Company"}
)

# With custom seed data
seed_data = {
    "name": "Custom Company",
    "seed_data": {
        "employees": [
            {"email": "ceo@company.com", "bio": "Company founder"}
        ],
        "questions": [
            {"content": "What are your goals?", "is_follow_up": False}
        ]
    }
}

response = requests.post(
    "http://localhost:8000/businesses/",
    json=seed_data
)
```

### JavaScript/TypeScript Example

```javascript
// Using the updated frontend API
import { api } from "@/lib/api";

// Basic creation (uses default seed data)
const response = await api.businesses.create({
  name: "My Company",
});

// With custom seed data
const response = await api.businesses.create({
  name: "Custom Company",
  seed_data: {
    employees: [{ email: "ceo@company.com", bio: "Company founder" }],
    questions: [{ content: "What are your goals?", is_follow_up: false }],
  },
});
```

## Files

- `backend/app/default_business_seed.json` - Default seed data
- `backend/app/example_business_seed.json` - Example of custom seed data format
- `backend/app/services/schemas/schema.py` - Request/response schemas
- `backend/app/controllers/business_controller.py` - API implementation

## Error Handling

The API will return appropriate HTTP status codes:

- `201 Created` - Business successfully created
- `400 Bad Request` - Invalid request data
- `422 Unprocessable Entity` - Validation errors (e.g., invalid email format)
- `500 Internal Server Error` - Server-side errors

If the default seed file is missing or corrupted, the system will fall back to minimal default data to ensure the business is still created successfully.
