# ChickenHub 🍗🔥
**Business Management and Online Ordering System**

ChickenHub is a web-based business management and online ordering system designed for a South African small business specialising in chicken dust (braaied chicken), fresh whole chickens, and chicken portions.

The platform digitises daily operations, replacing physical paper books with secure digital record keeping for inventory, purchases, sales, expenses, reporting, and customer online ordering.

---

## 🚀 Foundation Stage Overview

This initial release establishes the architectural and security foundation of ChickenHub:

- **Django Project Architecture**: Modular layout with independent apps under `apps/`.
- **Database**: SQLite database configuration for rapid development and reliability.
- **Custom Authentication & RBAC**: Custom user model supporting three staff roles:
  - **Owner**: Complete system control, user management, and executive financial reports.
  - **Manager**: Oversight of daily operations, purchasing, stock, sales, expenses, and order processing.
  - **Employee**: Operational sales recording and customer collection processing.
- **Customer Access**: Public access for customers to browse the menu and order without requiring an account.
- **Responsive UI Framework**: Bootstrap 5 with Bootstrap Icons, styled with ChickenHub's brand identity:
  - **Dark Charcoal** for navigation and sidebar panels.
  - **Braai Orange** for buttons, badges, and accents.
  - Light backgrounds and clean card layouts for legibility.
- **Staff Dashboard**: Responsive sidebar navigation, summary metric cards (sales, pending orders, stock items, low-stock alerts), quick actions, and recent activity log.

---

## 📁 Project Structure

```text
ChickenHub/
│
├── manage.py                  # Django CLI management script
├── requirements.txt           # Python project dependencies
├── .env.example               # Example environment variables
├── .gitignore                 # Git ignore rules for Django & Python
├── README.md                  # Project documentation and guide
│
├── config/                    # Django configuration package
│   ├── __init__.py
│   ├── settings.py            # Project settings, database & app registration
│   ├── urls.py                # Main URL routing and public/staff endpoints
│   ├── views.py               # Public customer landing view
│   ├── asgi.py                # ASGI entrypoint
│   └── wsgi.py                # WSGI entrypoint
│
├── apps/                      # Modular business applications
│   ├── accounts/              # Custom User model, login/logout, RBAC decorators
│   ├── dashboard/             # Staff management dashboard & stats
│   ├── inventory/             # Stock items & inventory adjustments (Foundation stub)
│   ├── purchases/             # Chicken & ingredient purchasing (Foundation stub)
│   ├── products/              # Meal recipes, portions & prices (Foundation stub)
│   ├── sales/                 # POS walk-in transaction recording (Foundation stub)
│   ├── orders/                # Online customer orders & collection (Foundation stub)
│   ├── expenses/              # Operating expenses tracking (Foundation stub)
│   └── reports/               # Revenue, costs & profit analytics (Foundation stub)
│
├── templates/                 # Django HTML templates
│   ├── base.html              # Core reusable base with Bootstrap 5 & alerts
│   ├── public/
│   │   └── home.html          # Public landing, menu showcase & business info
│   ├── accounts/
│   │   └── login.html         # Staff login portal with validation alerts
│   └── dashboard/
│       ├── base_dashboard.html# Dashboard layout with sidebar & top nav
│       └── index.html         # Staff dashboard home, metrics & quick actions
│
└── static/                    # Static assets
    ├── css/
    │   └── style.css          # ChickenHub custom styling & CSS variables
    ├── js/
    │   └── main.js            # Responsive sidebar toggle & UI behaviors
    └── images/                # Static image assets
```

---

## 🛠️ Technology Stack

- **Backend**: Python 3, Django 5+ / 6+
- **Database**: SQLite (`db.sqlite3`)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5.3, Bootstrap Icons
- **Security**: Django built-in PBKDF2 password hashing, CSRF protection, role-based decorators

---

## 💻 Setup & Installation Guide

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

### 2. Clone the Repository & Create Virtual Environment
```bash
# Clone the repository
git clone <repository-url>
cd chickenhub_base_foundation

# Create a virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (Command Prompt / PowerShell):
.\.venv\Scripts\activate

# macOS / Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
# Windows:
copy .env.example .env

# macOS / Linux:
cp .env.example .env
```

### 5. Run Database Migrations
Create and apply database migrations for the custom user model:
```bash
python manage.py makemigrations accounts
python manage.py migrate
```

### 6. Create the First Administrator (Owner) Account
Run the interactive command to create your first superuser account:
```bash
python manage.py createsuperuser
```
Follow the prompts to enter:
- **Username** (e.g., `admin` or `owner`)
- **Email address**
- **Password** (min 8 characters)

*Note: Accounts created via `createsuperuser` are automatically assigned the **Owner** role with full administrative privileges.*

### 7. Run the Development Server
```bash
python manage.py runserver
```

Once running, access the application in your browser:
- **Public Home Page**: `http://127.0.0.1:8000/`
- **Staff Login Portal**: `http://127.0.0.1:8000/accounts/login/`
- **Staff Dashboard**: `http://127.0.0.1:8000/dashboard/`
- **Django Admin**: `http://127.0.0.1:8000/admin/`

---

## 👥 Staff Roles & Access Control

ChickenHub implements role-based access control (RBAC):
- **Owner (`OWNER`)**: Full access to all business modules, user management, and financial reports.
- **Manager (`MANAGER`)**: Manages daily operations including stock levels, purchases, walk-in sales, customer orders, and expenses.
- **Employee (`EMPLOYEE`)**: Access to point-of-sale recording and customer order status updates.
- **Customer (Public)**: Can browse the menu and place collection orders without needing an account.

Staff views are protected by custom decorators (`@owner_required`, `@manager_required`, `@staff_required`) and `RoleRequiredMixin` located in `apps/accounts/decorators.py`.

---

## 🔄 Development Approach & Next Modules

Development is carried out incrementally according to the project specifications:
1. **Foundation (Current)**: Project structure, custom User model, Bootstrap 5 UI, public page, staff authentication, and dashboard.
2. **Module 1 - Inventory Management**: Managing chicken quantities, ingredients, units of measure, and stock movement logs.
3. **Module 2 - Purchasing Management**: Supplier details, chicken batch purchases, purchase items, and average cost calculations.
4. **Module 3 - Product & Menu Management**: Full, half, quarter chicken dust meals, portions, and accompaniments.
5. **Module 4 - Sales & POS**: Walk-in sales capturing, receipts, and revenue totals.
6. **Module 5 - Online Customer Ordering**: Public customer shopping cart, order submission, reference generation, and staff order tracking.
7. **Module 6 - Expenses & Reporting**: Operating expense tracking, daily/weekly/monthly profit estimates.
