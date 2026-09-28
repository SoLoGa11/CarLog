# CarLog API — Car Expense Logbook

REST API built with Django REST Framework. Users register, add their cars and keep a log of expenses for each car: fuel, charging, service, repairs, insurance, parking, washing. The API also shows simple statistics per car.

Each user can see and change **only their own** profile, cars and records.

**Tech stack:** Python 3.13, Django 6.0.3, Django REST Framework, Simple JWT, drf-spectacular (Swagger), SQLite, Docker.

---

## 1. Quick start with Docker

```bash
git clone https://github.com/SoLoGa11/CarLog.git
cd CarLog
docker compose up --build
```

- Swagger: http://localhost:8000/api/docs/
- Admin panel: http://localhost:8000/admin/

On startup the container runs: `makemigrations users` → `makemigrations garage` → `migrate` → `runserver`.

**Test users** (the database already contains demo data):

| Role | Email | Password | Data |
|---|---|---|---|
| Admin | `admin@carlog.ge` | `admin` | Admin panel |
| User | `levan@carlog.ge` | `carlog2026` | 2 cars, 9 records |
| User | `nino@carlog.ge` | `carlog2026` | 1 car, 2 records |

Create your own admin: `docker compose exec web python manage.py createsuperuser`

## 2. Run without Docker

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations users
python manage.py makemigrations garage
python manage.py migrate
python manage.py runserver
```

> Migrations are not stored in the repository. Run `makemigrations` for `users` first, then `garage`, so the migrations match the existing database.

## 3. Using Swagger

1. `POST /api/users/login/` with email and password.
2. Copy the `access` token.
3. Click **Authorize** and paste the token.

---

## 4. Project structure

```
carlog_api/     settings, urls
users/          custom user, registration, JWT, profile
garage/         cars, records, statistics
db.sqlite3      database with demo data
```

## 5. Models

- **User** (`AbstractUser`) — `username` removed, login by `email`. `first_name` and `last_name` are required, `phone_number` is optional. Custom `UserManager`.
- **Car** — `owner` (FK User), `name`, `year`, `fuel_type` (petrol / diesel / hybrid / electric), `initial_odometer`, `service_interval_km`, `is_main`, `created_at`.
- **Record** — `car` (FK Car), `date`, `category` (petrol, diesel, charging, service, repair, insurance, parking, wash, other), `amount` (GEL), `odometer`, `quantity` (litres or kWh), `is_full`, `note`, `created_at`.

## 6. How it works

- **Authentication:** JWT. Access token — 60 minutes, refresh token — 7 days. All endpoints require a token, except registration and login.
- **Own data only:** `me/` has no id, the user is taken from the token. Cars and records are filtered by the current user; another user's object returns 404.
- **Password:** write-only, checked with Django password validators, changed only via `change-password/` (old password required).
- **Validation:** year from 1950 to next year; amount > 0; date not in the future; `quantity` is required for petrol, diesel and charging; records can be added only to your own cars.
- **Main car:** the first car is main automatically; only one car can be main.
- **Statistics:** current odometer, total spent, spending by category.
- **Records list:** pagination (10 per page), filters `?car=` and `?category=`.

## 7. API endpoints

| Method | URL | Description |
|---|---|---|
| POST | `/api/users/register/` | Register |
| POST | `/api/users/login/` | Get access and refresh tokens |
| POST | `/api/users/login/refresh/` | Refresh access token |
| GET / PUT / PATCH / DELETE | `/api/users/me/` | My profile |
| POST | `/api/users/me/change-password/` | Change password |
| GET / POST | `/api/cars/` | My cars / add a car |
| GET / PUT / PATCH / DELETE | `/api/cars/{id}/` | One car |
| POST | `/api/cars/{id}/set-main/` | Make the car main |
| GET | `/api/cars/{id}/stats/` | Car statistics |
| GET / POST | `/api/records/` | My records / add a record |
| GET / PUT / PATCH / DELETE | `/api/records/{id}/` | One record |

## 8. Assignment requirements

| Requirement | Where |
|---|---|
| JWT authentication | `users/urls.py`, `settings.py` |
| Custom Django user | `users/models.py` |
| User CRUD | `register/`, `me/` (GET, PUT, PATCH, DELETE) |
| User sees only own profile | `me/` — no id, user from token |
| APIView and generic views | APIView: `MeView`, `ChangePasswordView`, `CarSetMainView`, `CarStatsView`; generic: all other views |
| Docker | `Dockerfile`, `docker-compose.yml` |
| Swagger | `/api/docs/` |