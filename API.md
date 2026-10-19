# API documentation

Base URL: `http://localhost:8000` (Swagger UI: `/docs`, OpenAPI JSON: `/openapi.json`).
All bodies are JSON. A ready-made Postman collection is in
[`postman/Wedding_RSVP.postman_collection.json`](postman/Wedding_RSVP.postman_collection.json).

## Endpoints

| Method | Path                    | Description                     | Success | Errors   |
|--------|-------------------------|---------------------------------|---------|----------|
| GET    | `/`                     | Health check                    | 200     | –        |
| GET    | `/registration/`        | List all registrations          | 200     | –        |
| GET    | `/registration/{id}`    | Get one registration by ID      | 200     | 404, 422 |
| POST   | `/registration/`        | Create a registration           | 201     | 422, 500 |
| PUT    | `/registration/{id}`    | Replace a registration          | 200     | 404, 422, 500 |
| DELETE | `/registration/{id}`    | Delete a registration           | 204 (no body) | 404, 422, 500 |

## Request body (POST, PUT)

| Field              | Type    | Rules                                                      |
|--------------------|---------|------------------------------------------------------------|
| `name`             | string  | required, 1–100 chars                                      |
| `surname`          | string  | required, 1–100 chars                                      |
| `attending`        | boolean | required                                                   |
| `amount_of_people` | integer | optional (default 0), 0–10; must be ≥ 1 if `attending` is true; forced to 0 if false |

```json
{ "name": "Aigerim", "surname": "Sadykova", "attending": true, "amount_of_people": 2 }
```

## Response object

```json
{
  "id": 1,
  "name": "Aigerim",
  "surname": "Sadykova",
  "attending": true,
  "amount_of_people": 2,
  "created_at": "2026-10-07T14:35:10.123456"
}
```

`GET /registration/` returns an array of these objects ordered by `id`.

## Errors

| Status | Meaning | Body |
|--------|---------|------|
| 404 | No registration with that ID | `{"detail": "Registration with id 99 not found"}` |
| 422 | Validation failed (bad body or non-integer ID) | FastAPI validation error list |
| 500 | Database error (details are logged, not returned) | `{"detail": "Database error"}` |

## Examples

```bash
curl -X POST   localhost:8000/registration/ -H "Content-Type: application/json" \
     -d '{"name":"Aigerim","surname":"Sadykova","attending":true,"amount_of_people":2}'
curl           localhost:8000/registration/
curl           localhost:8000/registration/1
curl -X PUT    localhost:8000/registration/1 -H "Content-Type: application/json" \
     -d '{"name":"Aigerim","surname":"Sadykova","attending":true,"amount_of_people":4}'
curl -X DELETE localhost:8000/registration/1
```
