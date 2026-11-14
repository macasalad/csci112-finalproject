# CSCI 112 Final Project

## Getting Started

Before starting development, read the project documentation [here](https://docs.google.com/document/d/1rUY36Ixol_GqdYNsP_TJx4izjwvitSFfRul9IvN6oFU/edit?tab=t.ym1llqggm5o).

It contains the task assignments, resources, to-do lists, and Git branching guidelines. These guidelines must be strictly followed :)

## Project Structure
**Note:** After following the installation guide, your local project structure should look something like this:

```text
csci112/
├── event_platform/
│   ├── database/
│   ├── event_platform/
│   ├── events/
│   ├── .env
│   └── manage.py
├── venv/
├── .gitignore
├── README.md
└── requirements.txt
```
## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/macasalad/csci112-finalproject.git
    ```

2. Navigate to the project folder:
    ```bash
    cd csci112-finalproject
    ```

3. Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    
    For Windows:
    ```bash
    venv\Scripts\activate
    ```

4. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

5. Create a `.env` file in the project folder (same directory as `manage.py`):
    ```env
    DB_USERNAME=db_username
    DB_PASSWORD=db_password
    MONGO_URI=mongo_uri
    ```

    Replace the placeholders with the credentials I'll send in our GC.

## Running the Project

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser. For now, only http://127.0.0.1:8000/events/ has a working page.

## Git Branching Guidelines

**Always branch out from `develop`, unless it's a hotfix (refer to the project documentation).**

1. Update your local `develop` branch:
    ```bash
    git checkout develop
    git pull origin develop
    ```

2. Create a feature branch using the `feature/feature-name` naming convention:
    ```bash
    git checkout -b feature/feature-name
    ```

3. Commit and push your changes:
    ```bash
    git add .
    git commit -m "Describe your changes"
    git push origin feature/feature-name
    ```

4. Create a Pull Request targeting `develop`.

### Important Rules

- Always branch out from `develop`.
- Use `feature/feature-name` for branch names.
- Do not push directly to `develop`.
- Do not develop directly on `develop`.
- All changes must go through a Pull Request.