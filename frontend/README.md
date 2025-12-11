# Frontend Templates

HTML templates for the web interface.

## Templates

### `index.html`
Landing page with API documentation and getting started guide.

**Features:**
- Project overview
- Quick start guide
- API endpoint listing
- Example requests with curl
- Interactive features demo

**Route:** `GET /`

---

### `dashboard.html`
Real-time security metrics and analytics dashboard.

**Features:**
- Total requests counter
- Block rate metrics
- Threat type breakdown (pie charts)
- Time-series trends (line charts)
- Recent logs table
- Export to CSV/JSON

**Visualizations:**
- PII detection count
- Toxicity blocks
- Injection attempts
- Pass/Block/Flag ratios

**Route:** `GET /dashboard` (Auth required)

**Technologies:**
- Chart.js for visualizations
- DataTables for log tables
- Tailwind CSS for styling
- Alpine.js for interactivity

---

### `auth.html`
User login page.

**Features:**
- Username/password form
- JWT token storage
- Remember me option
- Password visibility toggle
- Error message display

**Route:** `GET /login`

**Form Action:** `POST /api/auth/login`

---

## Static Assets

Static files are served from `frontend/static/`:

```
static/
├── css/
│   └── style.css          # Custom styles
├── js/
│   ├── dashboard.js       # Dashboard logic
│   └── auth.js           # Authentication logic
└── images/
    └── logo.png          # Logo and icons
```

---

## Usage

Templates use Jinja2 template engine with FastAPI's `templates` support:

```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="frontend/templates")

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "LLM Security Middleware"}
    )
```

---

## Development

To modify templates:

1. Edit HTML files in `frontend/templates/`
2. Refresh browser (hot reload enabled in dev mode)
3. Check browser console for errors
4. Use browser DevTools to debug styles

**Tailwind CSS:**
```bash
# Watch for changes and rebuild CSS
npx tailwindcss -i ./static/css/input.css -o ./static/css/style.css --watch
```
