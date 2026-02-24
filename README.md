[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=22831414&assignment_repo_type=AssignmentRepo)
# Student Grading System – Primer

**This is an individual exercise.**

### Due Week 3 Lab Time

This primer extends upon basic knowledge of **Docker**, **Git/GitHub**, and **Python** in one mini-project. If you have not used these before, refer to the pre-requisite section.

**Marks:** Part 1 (Docker) 2%, Part 2 (Backend) 1.5%, Part 3 (Git) 1.5% - **total 5%**



---

## Pre-requisite
The following repositories contain simple exercises which should help you with the exercise (these will not be marked and are optional)
- **Docker:** https://github.com/unsw-cse-comp99-3900/Language-Primer
- **Python:** https://github.com/unsw-cse-comp99-3900/Docker-Primer
- **Git:** https://github.com/unsw-cse-comp99-3900/Git-Primer

---

## Setup (do this first)

1. **Install Docker**  
   Download and install from https://docs.docker.com/get-docker/  
   Ensure Docker is running whenever you are developing, this has been tested with the latest version of Docker Desktop (4.60.1)

2. **Clone this repo**  
   If you have not used Git before, refer to the Git primer.

3. **Use your own GitHub repo for submission**  
   - Create a **private** repo (e.g. `student-grading-primer`) on your GitHub account. **Do not fork** this repo.  
   - Clone this (course) repo, then point the remote to your repo:
     ```bash
     git remote set-url origin git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git
     ```
   - Run `git push` so your repo has the starter code. You will work in this repo for the rest of the exercise.

   *Note: Do not clone and work on your private repo, all changes should be made from the course primer you have cloned, and pushed remotely to your private repo.*

---

## Part 1: Docker – Mounting volumes and database initialisation (2%)

You must complete the `docker-compose.yml` file. A mock SQL database has been provided at `./db/init.sql`. We need to initialise this in our docker container and mount it to a persistent volume.

Requirements:
1. Configure the **backend** and **frontend** based on the provided ports in the `running the application` section



#### Resources:
- https://docs.docker.com/guides/databases/

### 1. Backend service

The **`backend`** service is currently a stub. You need to complete it so the backend container builds, runs, and can connect to the database.

- The backend **reads connection parameters from environment variables** (see **`backend/db.py`** for the exact names)

<details>
   <summary>Hint #1:</summary>

   Running the backend container will depend on the db. Check what environment variables are required to connect to the db, as these will be required when initialising the db.
</details>

<details>
   <summary>Hint #2:</summary>

   The DB_HOST should be "db", the rest of these environment variables should match the credentials for the db service.
</details>

### 2. Frontend service

The **`frontend`** service is currently a stub. Complete it so the frontend builds and runs correctly on the port `8080`.


<details>
   <summary>Hint #1:</summary>

   Check the Frontend dockerfile to see what port the service is running on. You may notice this is different to the expected port `8080`. We need to map these ports in the docker compose file.
</details>

### 3. Mounting the volume
1. Add the **pre-seed script** (`./db/init.sql`) so the database is initialised on the first-build of the container. This should be mounted to `/docker-entrypoint-initdb.d/`(PostgreSQL container's initialisation directory)

2. Add a **volume** so the database’s data persists when the container is recreated.

<details>
<summary>Hint #1:</summary>

In our compose file, we can define a volume under the db service and map the pre-seed script to a file in the provided database initialisation directory ie. `/docker-entrypoint-initdb.d/init.sql`
</details>

<details>
<summary>Hint #2:</summary>

To make data persistent, we need to create a named volume for the service and map this volume to the SQL data directory. Refer to the linked resources to see how this is done.
</details>

### 4. Sanity check
To run the app, execute this command:
```bash
docker compose up --build
```
Check the links in `running the application` work, and that the data persists when creating a student and restarting the application

Note: It is normal to see errors in the backend at this stage as the function stubs have not been implemented. On build however after adding the init.sql script you should see this line:
```docker
db-1        | /usr/local/bin/docker-entrypoint.sh: running /docker-entrypoint-initdb.d/init.sql
```
If you do not see this, you may need to delete the container and re-build as it may have already mounted to the initialisation directory on a prior buid.

---

## Part 2: Backend stub implementation (1%)

Implement the backend from the provided **stubs**. Each route in **`backend/app.py`** is a stub with instructions.

Do not modify **`backend/db.py`**. You are provided with abstract methods to fetch and insert data into the DB. ie. `get_all_students()`, `get_student_by_id(id)`, `insert_student(name, course, mark)`, etc.

The requirement is that all data is persistent. You can utilise additional data structures/methods to achieve this. 

You must also add error handling where appropriate. For simplicity all errors will return a 404 code, and success will return 200.

### What to implement

- **GET /students** — Fetch all students from the database and return as JSON.
- **POST /students** — Creates a student with `name`, `course`, optionally `mark`. Return the created student and status 200
- **PUT /students/{id}** — Update the student details. Return 404 if the id does not exist
- **DELETE /students/{id}** — Delete the student. Return 404 if student not found.
- **GET /stats** — Return `count`, `average`, `min`, `max` of all student marks.

The spec is deliberately **abstract**: you choose validation rules, error messages, and use any additional data structures/methods. Implement each stub so the API is consistent and data is persistent via the db module.

### Edge case (required for full marks)

Identify **one edge case** not fully specified in the primer spec, and document in **`EDGE_CASE.md`** how you chose to handle it and why.

### Check your work

- Run: `docker compose up --build`  
- Run the public automark: `docker compose --profile debug up --build automark`  
- You should see **`SANITY CHECK PASSED`**. Note that this is only a dry-run, and a test suite will be run against your work on the submission date.

---

## Part 3: Git – Resolving conflicts and safe practices (2%)

Your friend Eric has volunteered to implement the Frontend for your /stats endpoint. Upon merging his changes, you run into some merge conflicts and discover some unsafe git practices.

#### Step 1: Committing and pushing your work

Create a new branch named `docker_and_backend`, and commit and push your changes from Part 1 & Part 2.

Ensure your commit message is meaningful ie. `feat: Initialise docker from pre-seed script and implement function stubs`

```bash
git checkout -b docker_and_backend

... commit and push your changes
```

**Do not merge this branch into `main`.** Push your branch to the remote.

If you are unsure about how to do any of these steps, refer to the git primer.

#### Step 2: Pull from Eric's feature branch

Eric's changes are located on branch eric/stats-feature, merge these changes into the `docker_and_backend` branch and resolve any merge conflicts.
While you are merging the changes, you notice there are a couple of typos in the frontend as the button says `add tutor` and the table says `tutor` rather than students.

You should fix these typos located in `frontend/src/App.jsx` (Do NOT commit/push your changes at this stage!!)
Note: Upon completion, there should not be any merge conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).

#### Step 3: Remove .env and add .gitignore file

While merging, you realise that Eric has accidentally merged a `.env` file containing a secret. You must remove it from the staged changes and ensure it is not commited!

To do so, you first run:

```bash
git rm --cached .env
```

Create a **`.gitignore`** file in the project root that excludes `.env` (and optionally other files like `node_modules`). Then:

```bash
git add .gitignore
git commit -m "chore: Fix typo and remove .env from repo and add .gitignore"
```

Note: You can use a [conventional commit](https://www.conventionalcommits.org/en/v1.0.0/) style message to increase readibility in your commits.

### Step 4: Push and open a pull request

Push your changes to the remote branch, and open a pull request for both your branches on github.

 Do **NOT** merge the pull request. You need to show your tutor the **open** pull request to receive marks.

---

## Running the application (summary)

From the project root:

```bash
docker compose up --build
```

- Frontend: http://localhost:8080  
- Backend: http://localhost:5000  
- Health: http://localhost:5000/  
- Students: http://localhost:5000/students  
- Stats: http://localhost:5000/stats  

---

## Autotests

At any time after Part 2, you can run the public tests:

```bash
docker compose --profile debug up --build automark
```

You must see **`SANITY CHECK PASSED`**. These tests check: backend health, database connectivity, list of students, `/stats` response shape, and that creating a student persists.

These are only basic tests, you must ensure you add proper error handling/validation according to the spec for full marks. A private test suite will be run on the deadline.
