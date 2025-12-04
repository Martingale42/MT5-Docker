# GitHub Actions Tutorial - From Zero to Hero

**Time to complete:** 60-90 minutes
**Prerequisites:** Basic Git knowledge, GitHub account

---

## Table of Contents

1. [Conceptual Understanding](#conceptual-understanding)
2. [How GitHub Actions Works](#how-github-actions-works)
3. [Hands-On Tutorial](#hands-on-tutorial)
4. [Real Examples from MT5-Docker](#real-examples)
5. [Common Patterns](#common-patterns)
6. [Troubleshooting](#troubleshooting)

---

## Conceptual Understanding

### What is CI/CD?

**CI/CD** stands for Continuous Integration / Continuous Deployment.

**Continuous Integration (CI):**
- Automatically test your code every time you push changes
- Catch bugs early before they reach production
- Ensure code quality through automated checks

**Continuous Deployment (CD):**
- Automatically deploy your application when tests pass
- Reduce manual deployment errors
- Deploy faster and more frequently

### What is GitHub Actions?

**GitHub Actions** is GitHub's built-in automation tool that runs workflows when events happen in your repository.

**Think of it like this:**
```
When [something happens] → Do [these automated tasks]

Examples:
- When [code is pushed] → Run tests, build Docker image
- When [PR is opened] → Run linters, check code quality
- When [tag is created] → Deploy to production
```

### Why Use GitHub Actions?

**Before GitHub Actions:**
```
Developer pushes code
  ↓
Developer manually runs tests (might forget!)
  ↓
Developer manually builds Docker image
  ↓
Developer manually deploys to server
  ↓
Something breaks? Start over!
```

**With GitHub Actions:**
```
Developer pushes code
  ↓
GitHub Actions automatically:
  - Runs all tests
  - Checks code quality
  - Builds Docker images
  - Scans for security issues
  - Deploys to server
  ↓
Everything is documented and repeatable!
```

---

## How GitHub Actions Works

### Key Concepts

#### 1. Workflow
A workflow is a configurable automated process defined in a YAML file.

**Location:** `.github/workflows/filename.yml`

**Example:**
```yaml
name: My First Workflow
on: [push]  # When to run
jobs:
  my-job:
    runs-on: ubuntu-latest  # Where to run
    steps:
      - name: Say hello
        run: echo "Hello, World!"
```

#### 2. Events (Triggers)
Events are actions that trigger workflows.

**Common Events:**
- `push` - When code is pushed
- `pull_request` - When a PR is opened/updated
- `schedule` - Run on a schedule (like cron)
- `workflow_dispatch` - Manual trigger

**Example:**
```yaml
on:
  push:
    branches: [ main ]  # Only on main branch
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
```

#### 3. Jobs
A job is a set of steps that execute on the same runner.

**Jobs can:**
- Run in parallel (by default)
- Run sequentially (using `needs`)
- Run on different operating systems

**Example:**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Testing..."

  deploy:
    needs: test  # Wait for test to finish
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying..."
```

#### 4. Steps
Steps are individual tasks that run commands.

**Steps can:**
- Run shell commands
- Use pre-built actions from marketplace
- Set up tools (Python, Node, Docker, etc.)

**Example:**
```yaml
steps:
  - name: Checkout code
    uses: actions/checkout@v4  # Use an action

  - name: Run tests
    run: pytest tests/  # Run a command
```

#### 5. Runners
Runners are servers that execute your workflows.

**GitHub provides:**
- `ubuntu-latest` (most common)
- `windows-latest`
- `macos-latest`

**Example:**
```yaml
runs-on: ubuntu-latest  # Run on Ubuntu Linux
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Repository                     │
│                                                          │
│  ┌────────────────────────────────────────────────┐   │
│  │  .github/workflows/test.yml                    │   │
│  │                                                  │   │
│  │  on: push                 ← Event              │   │
│  │  jobs:                    ← Job                │   │
│  │    test:                                        │   │
│  │      runs-on: ubuntu     ← Runner              │   │
│  │      steps:              ← Steps               │   │
│  │        - checkout code                          │   │
│  │        - run tests                              │   │
│  └────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↓
              When code is pushed...
                          ↓
┌─────────────────────────────────────────────────────────┐
│              GitHub Actions Runner (VM)                  │
│                                                          │
│  1. Spins up fresh Ubuntu VM                           │
│  2. Checks out your code                               │
│  3. Runs your commands                                 │
│  4. Reports results back                               │
│  5. Shuts down VM                                      │
└─────────────────────────────────────────────────────────┘
```

---

## Hands-On Tutorial

### Exercise 1: Your First Workflow

**Goal:** Create a simple workflow that says hello

1. **Create the workflow file:**
```bash
mkdir -p .github/workflows
cd .github/workflows
```

2. **Create `hello.yml`:**
```yaml
name: Hello World

on:
  push:
    branches: [ main ]
  workflow_dispatch:  # Allow manual trigger

jobs:
  greet:
    runs-on: ubuntu-latest

    steps:
      - name: Print greeting
        run: |
          echo "Hello from GitHub Actions!"
          echo "Current time: $(date)"
          echo "Running on: $(uname -a)"
```

3. **Commit and push:**
```bash
git add .github/workflows/hello.yml
git commit -m "Add hello world workflow"
git push origin main
```

4. **View results:**
- Go to your GitHub repository
- Click "Actions" tab
- See your workflow running!
- Click on the workflow to see logs

**Expected output:**
```
Hello from GitHub Actions!
Current time: Mon Jan 13 10:30:00 UTC 2025
Running on: Linux runner-xyz 5.15.0-xxx
```

### Exercise 2: Running Tests

**Goal:** Automatically run pytest tests on every push

1. **Create `test-simple.yml`:**
```yaml
name: Run Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      # Step 1: Get the code
      - name: Checkout code
        uses: actions/checkout@v4

      # Step 2: Setup Python
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      # Step 3: Install dependencies
      - name: Install dependencies
        run: |
          pip install pytest pyzmq pandas

      # Step 4: Run tests
      - name: Run unit tests
        run: |
          pytest tests/unit/ -v
```

2. **Test it:**
```bash
git add .github/workflows/test-simple.yml
git commit -m "Add test workflow"
git push
```

3. **Watch it run:**
- Go to Actions tab
- Click on "Run Tests" workflow
- See each step execute in real-time

**What's happening:**
```
GitHub Actions Runner starts
  ↓
Checkout code (gets your repository)
  ↓
Setup Python 3.13
  ↓
Install dependencies (pytest, pyzmq, pandas)
  ↓
Run pytest tests/unit/ -v
  ↓
Report results (✓ pass or ✗ fail)
```

### Exercise 3: Building Docker Images

**Goal:** Build Docker image and verify it works

1. **Create `docker-test.yml`:**
```yaml
name: Docker Build Test

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build Docker image
        run: |
          docker build -t mt5zmq:test .

      - name: Verify image was built
        run: |
          docker images | grep mt5zmq

      - name: Test container startup
        run: |
          # Start container in background
          docker run -d --name test-container mt5zmq:test

          # Wait a bit
          sleep 10

          # Check if still running
          docker ps | grep test-container

          # Show logs
          docker logs test-container

          # Cleanup
          docker stop test-container
          docker rm test-container
```

2. **Run it:**
```bash
git add .github/workflows/docker-test.yml
git commit -m "Add Docker build test"
git push
```

**What this does:**
- Builds your Docker image
- Starts a container
- Verifies it's running
- Shows logs
- Cleans up

---

## Real Examples from MT5-Docker

### Example 1: Test Workflow (test.yml)

Let's break down the test workflow we created:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]  # Run on these branches
  pull_request:
    branches: [ main, develop ]  # Run on PRs
  workflow_dispatch:              # Allow manual trigger
```

**What this means:**
- Workflow runs when you push to `main` or `develop`
- Workflow runs when someone opens a PR
- You can manually trigger it from GitHub UI

```yaml
jobs:
  lint:
    name: Lint Code
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          pip install ruff

      - name: Run Ruff linter
        run: |
          ruff check scripts/ tests/ monitoring/
```

**What this does:**
1. **Checkout code:** Downloads your repository
2. **Set up Python:** Installs Python 3.13
3. **Install dependencies:** Installs ruff (linter)
4. **Run linter:** Checks code style

**Try it yourself:**
```bash
# Make a style error
echo "x=1" >> scripts/test_file.py  # No spaces around =

# Commit and push
git add scripts/test_file.py
git commit -m "Test linting"
git push

# GitHub Actions will fail and show you the error!
```

### Example 2: Security Scanning (security.yml)

```yaml
jobs:
  container-scan:
    name: Container Image Scan
    runs-on: ubuntu-latest

    steps:
      - name: Build Docker image
        run: docker build -t mt5zmq:scan .

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'mt5zmq:scan'
          format: 'table'
          severity: 'CRITICAL,HIGH'
```

**What this does:**
- Builds your Docker image
- Scans it for security vulnerabilities
- Reports CRITICAL and HIGH severity issues

**Why it matters:**
- Catches security issues before production
- Scans base images for known CVEs
- Checks for outdated packages

---

## Common Patterns

### Pattern 1: Matrix Builds (Test Multiple Versions)

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12', '3.13']

    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
```

**What this does:**
- Runs tests on Python 3.10, 3.11, 3.12, AND 3.13
- All run in parallel
- Ensures compatibility across versions

### Pattern 2: Caching Dependencies

```yaml
- name: Cache Python dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

**What this does:**
- Saves installed packages
- Reuses them in next run
- Makes workflows faster

### Pattern 3: Conditional Steps

```yaml
- name: Deploy to production
  if: github.ref == 'refs/heads/main'
  run: ./deploy.sh
```

**What this does:**
- Only runs on `main` branch
- Skips for other branches

### Pattern 4: Secrets Management

```yaml
- name: Deploy
  env:
    SSH_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
    API_TOKEN: ${{ secrets.API_TOKEN }}
  run: ./deploy.sh
```

**How to add secrets:**
1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add name and value
4. Use `${{ secrets.SECRET_NAME }}` in workflow

---

## Hands-On Exercise: Create Your Own Workflow

**Task:** Create a workflow that:
1. Runs on every push
2. Checks if Docker is installed
3. Lists all Python files in the project
4. Counts total lines of Python code

**Solution:**
```yaml
name: Code Statistics

on:
  push:
    branches: [ main ]

jobs:
  stats:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Check Docker
        run: |
          docker --version
          docker-compose --version

      - name: List Python files
        run: |
          echo "Python files in project:"
          find . -name "*.py" -type f

      - name: Count lines of code
        run: |
          echo "Total Python lines:"
          find . -name "*.py" -type f -exec wc -l {} + | tail -1
```

**Try it:**
```bash
# Create the file
cat > .github/workflows/stats.yml << 'EOF'
[paste the YAML above]
EOF

# Commit and push
git add .github/workflows/stats.yml
git commit -m "Add code statistics workflow"
git push

# Watch it run on GitHub!
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Workflow not running

**Problem:** Pushed code but workflow didn't trigger

**Solutions:**
1. Check if workflow file is in `.github/workflows/`
2. Check YAML syntax (use a YAML validator)
3. Check if trigger conditions match (e.g., correct branch)

**Debug:**
```bash
# Validate YAML syntax
python -m yaml .github/workflows/test.yml

# Check if file is committed
git ls-files .github/workflows/
```

#### Issue 2: Tests fail in CI but pass locally

**Problem:** Tests pass on your machine, fail in GitHub Actions

**Common causes:**
- Different Python versions
- Missing environment variables
- Different operating system (Mac vs Linux)
- Missing dependencies

**Solution:**
```yaml
# Add debug information
- name: Debug environment
  run: |
    echo "Python version:"
    python --version

    echo "Installed packages:"
    pip list

    echo "Environment variables:"
    env | sort
```

#### Issue 3: Slow workflows

**Problem:** Workflows take too long

**Solutions:**
1. Use caching:
```yaml
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

2. Run jobs in parallel
3. Use Docker layer caching

#### Issue 4: Permission denied

**Problem:** Can't push Docker images or create releases

**Solution:** Add permissions to workflow:
```yaml
jobs:
  build:
    permissions:
      contents: read
      packages: write
```

---

## Next Steps

**You've learned:**
- ✓ What CI/CD is and why it matters
- ✓ How GitHub Actions works (events, jobs, steps, runners)
- ✓ How to create and run workflows
- ✓ Common patterns and best practices

**Practice exercises:**
1. Modify `test.yml` to run tests on Python 3.11 and 3.12
2. Add a step to your workflow that prints "Tests passed!"
3. Create a workflow that runs only on Monday mornings
4. Add a workflow that comments on PRs with test results

**Continue learning:**
- Next tutorial: [Prometheus Monitoring](02_PROMETHEUS_GUIDE.md)
- Read: [GitHub Actions Documentation](https://docs.github.com/en/actions)
- Explore: [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)

---

## Quick Reference

### Essential Actions

```yaml
# Checkout code
- uses: actions/checkout@v4

# Setup Python
- uses: actions/setup-python@v5
  with:
    python-version: '3.13'

# Setup Docker
- uses: docker/setup-buildx-action@v3

# Cache dependencies
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

# Upload artifacts
- uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: test-results.xml
```

### Common Commands

```bash
# View workflow runs
gh run list

# View specific run
gh run view <run-id>

# Re-run failed jobs
gh run rerun <run-id>

# View workflow logs
gh run view <run-id> --log
```

### Useful Links

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Actions Marketplace](https://github.com/marketplace?type=actions)
- [Community Forum](https://github.community/c/code-to-cloud/github-actions/41)
