# Template Config

`MAILGATEWAY_PREDEFINED_TEMPLATES` should point to a JSON file with this shape:

```json
{
  "templates": {
    "ops-alert": {
      "subject": "Alert: {title}",
      "text_body": "Severity: {severity}\n\n{summary}",
      "html_body": "<p><strong>Severity:</strong> {severity}</p><p>{summary}</p>",
      "to": ["ops@example.com"],
      "cc": [],
      "bcc": [],
      "allowed_params": ["severity", "summary", "title"]
    }
  }
}
```

Rules:

- `subject` is required
- at least one of `text_body` or `html_body` is required
- `to` is required and must be a non-empty array
- `allowed_params` is optional; if omitted, all placeholders used by the template are allowed
- account selection comes from the deployment-owned `MAILGATEWAY_ACCOUNT` environment variable rather than the template file
