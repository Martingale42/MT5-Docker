# MT5-Docker DevOps Tutorial Series

**Welcome!** This tutorial series will teach you everything you need to know about the DevOps tools used in the MT5-Docker project.

**Target audience:** Developers new to DevOps, CI/CD, monitoring, and observability.

---

## Learning Path

### 🎯 Prerequisites

Before starting these tutorials, you should have:
- ✓ Basic command line knowledge
- ✓ Basic Git knowledge
- ✓ Docker basics (what containers are)
- ✓ Basic Python knowledge

**Time commitment:** 4-6 hours total (can be split across multiple sessions)

---

## Tutorial Structure

Each tutorial includes:
- 📖 **Conceptual Understanding** - What and Why
- 🏗️ **Architecture** - How it works
- 💻 **Hands-On Exercises** - Learn by doing
- 🎯 **Real Examples** - From MT5-Docker project
- 🔧 **Troubleshooting** - Common issues and solutions
- 📚 **Quick Reference** - Cheat sheets

---

## Tutorials

### Tutorial 01: GitHub Actions - CI/CD Automation
**⏱️ Time:** 60-90 minutes
**📄 File:** [01_GITHUB_ACTIONS_GUIDE.md](01_GITHUB_ACTIONS_GUIDE.md)

**What you'll learn:**
- What CI/CD is and why it matters
- How GitHub Actions works (workflows, jobs, steps, runners)
- How to write workflow YAML files
- How to run automated tests
- How to build and deploy automatically
- How to use secrets and environment variables

**Hands-on exercises:**
- Create your first workflow
- Run automated tests on every push
- Build Docker images automatically
- Create custom workflows

**After this tutorial, you'll be able to:**
- ✓ Understand the `.github/workflows/` files in the project
- ✓ Modify existing workflows
- ✓ Create new workflows for automation
- ✓ Debug failing CI/CD pipelines

---

### Tutorial 02: Prometheus - Metrics & Monitoring
**⏱️ Time:** 90-120 minutes
**📄 File:** [02_PROMETHEUS_GUIDE.md](02_PROMETHEUS_GUIDE.md)

**What you'll learn:**
- What monitoring is and why it's critical
- How Prometheus collects and stores metrics
- Metric types (counter, gauge, histogram)
- PromQL query language
- How to create alerts
- Best practices for metrics

**Hands-on exercises:**
- Start Prometheus and explore the UI
- Understand metrics endpoints
- Write PromQL queries
- Create custom queries for your needs
- Generate metrics and watch them change

**After this tutorial, you'll be able to:**
- ✓ Understand the `monitoring/prometheus_exporter.py` code
- ✓ Write PromQL queries to get insights
- ✓ Create new metrics for your application
- ✓ Set up alerting rules
- ✓ Debug monitoring issues

---

### Tutorial 03: Grafana - Visualization & Dashboards
**⏱️ Time:** 60-90 minutes
**📄 File:** [03_GRAFANA_GUIDE.md](03_GRAFANA_GUIDE.md)

**What you'll learn:**
- What Grafana is and how it works with Prometheus
- Dashboard design principles
- Different visualization types (graphs, gauges, stats)
- How to create and customize panels
- How to set up alerts and notifications
- Best practices for dashboards

**Hands-on exercises:**
- Access and navigate Grafana
- Import existing dashboards
- Create your own dashboard from scratch
- Customize visualizations
- Set up color thresholds
- Create multi-panel layouts

**After this tutorial, you'll be able to:**
- ✓ Navigate the Grafana UI confidently
- ✓ Modify existing dashboards
- ✓ Create new dashboards for your metrics
- ✓ Choose the right visualization for your data
- ✓ Set up effective monitoring dashboards

---

## Quick Start

**Want to start immediately?** Follow these steps:

### Step 1: Clone and Setup (5 minutes)

```bash
# If you haven't already
cd /home/cy/Code/MT5/MT5-Docker

# Install Python dependencies
uv pip install pytest pytest-cov pyzmq pandas prometheus-client

# Verify everything is installed
pytest tests/unit/ -v
```

### Step 2: Start the Stack (2 minutes)

```bash
# Start MT5
docker-compose up -d mt5zmq

# Start monitoring stack
docker-compose --profile monitoring up -d

# Start API documentation
docker-compose --profile docs up swagger-ui

# Verify everything is running
docker-compose --profile monitoring ps
```

### Step 3: Access the Tools (1 minute)

Open these in your browser:
- **GitHub Actions:** https://github.com/[your-repo]/actions
- **Prometheus:** http://localhost:9091
- **Grafana:** http://localhost:3000 (admin/admin)
- **Swagger UI:** http://localhost:8080

### Step 4: Start Learning (3-6 hours)

Pick a tutorial and dive in! Recommend order:
1. GitHub Actions (if you'll be doing CI/CD)
2. Prometheus (foundation for monitoring)
3. Grafana (build on Prometheus knowledge)

---

## Suggested Learning Schedules

### Option A: One Day Intensive
**Total time:** 4-6 hours

**Morning (2-3 hours):**
- Tutorial 01: GitHub Actions
- Break (15 min)
- Start Tutorial 02: Prometheus (Sections 1-3)

**Afternoon (2-3 hours):**
- Continue Tutorial 02: Prometheus (Sections 4-7)
- Break (15 min)
- Tutorial 03: Grafana

### Option B: Spread Over Week
**~1 hour per day**

- **Day 1:** GitHub Actions (Part 1 - Concepts & basics)
- **Day 2:** GitHub Actions (Part 2 - Hands-on exercises)
- **Day 3:** Prometheus (Part 1 - Concepts & architecture)
- **Day 4:** Prometheus (Part 2 - PromQL & queries)
- **Day 5:** Prometheus (Part 3 - Advanced queries & alerts)
- **Day 6:** Grafana (Part 1 - Basics & first dashboard)
- **Day 7:** Grafana (Part 2 - Advanced dashboards)

### Option C: Just-In-Time Learning
**Learn what you need, when you need it**

**Need to fix a failing CI/CD pipeline?**
→ Tutorial 01: GitHub Actions → Troubleshooting section

**Need to understand why system is slow?**
→ Tutorial 02: Prometheus → Query metrics

**Need to create a new dashboard?**
→ Tutorial 03: Grafana → Building Dashboards

---

## Learning Tips

### For Best Results

**1. Follow Along**
Don't just read - actually do the exercises! Type the commands, run the code, break things and fix them.

**2. Take Notes**
Keep a notebook of:
- New concepts you learned
- Useful commands and queries
- Questions that come up
- Ideas for your own use cases

**3. Experiment**
After completing exercises, try variations:
- What happens if I change this parameter?
- Can I combine these queries?
- What other visualizations could work?

**4. Reference Often**
These tutorials have Quick Reference sections at the end. Bookmark them!

**5. Ask Questions**
If something isn't clear:
- Re-read the conceptual section
- Try the example in your environment
- Check the troubleshooting section
- Search online for more examples

### Common Pitfalls to Avoid

❌ **Skipping the conceptual sections**
→ You'll miss the "why" behind the "how"

❌ **Not doing the hands-on exercises**
→ Reading isn't enough - you need practice

❌ **Rushing through**
→ Take time to understand each concept

❌ **Getting discouraged by errors**
→ Errors are part of learning! Use the troubleshooting sections

---

## After Completing Tutorials

### You'll Understand

**GitHub Actions:**
- How CI/CD works in this project
- What `.github/workflows/*.yml` files do
- How to add new automated checks
- How to debug failing pipelines

**Prometheus:**
- What metrics are being collected
- How to query metrics for insights
- How alerting works
- How to add new metrics

**Grafana:**
- How dashboards are structured
- How to modify existing dashboards
- How to create new visualizations
- How to set up alerts

### Next Steps

**1. Customize for Your Needs**
- Modify workflows to run different tests
- Add metrics for your specific use case
- Create dashboards that matter to you

**2. Explore Advanced Topics**
- GitHub Actions: Matrix builds, caching, artifacts
- Prometheus: Recording rules, federation
- Grafana: Variables, annotations, templating

**3. Apply to Other Projects**
- Use these skills in other projects
- Set up monitoring for other applications
- Create CI/CD pipelines for other repos

**4. Share Knowledge**
- Help others learn these tools
- Contribute improvements to the project
- Write about your experiences

---

## Resources

### Official Documentation

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Docs](https://grafana.com/docs/)

### Community Resources

- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)
- [Prometheus Community](https://prometheus.io/community/)
- [Grafana Community](https://community.grafana.com/)

### Useful Tools

- [YAML Validator](https://www.yamllint.com/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)
- [Grafana Dashboard Gallery](https://grafana.com/grafana/dashboards/)

### Books (Optional Deep Dive)

- **Prometheus: Up & Running** by Brian Brazil
- **Continuous Delivery** by Jez Humble & David Farley
- **Site Reliability Engineering** (free online) - Google

---

## Project Structure Reference

Understanding where things are:

```
MT5-Docker/
├── .github/
│   └── workflows/          # GitHub Actions workflows
│       ├── test.yml        # Run tests
│       ├── docker-build.yml # Build images
│       ├── security.yml    # Security scans
│       └── deploy.yml      # Deployment
│
├── monitoring/
│   ├── prometheus_exporter.py  # Metrics exporter
│   ├── logging_config.py       # Structured logging
│   ├── prometheus/
│   │   ├── prometheus.yml      # Prometheus config
│   │   └── alerts.yml          # Alert rules
│   └── grafana/
│       └── dashboards/
│           └── mt5-dashboard.json  # Pre-built dashboard
│
├── tests/
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── conftest.py             # Test fixtures
│
├── scripts/
│   ├── zmq_client.py          # ZMQ client library
│   ├── healthcheck.py         # Docker health check
│   └── validate_openapi.py    # API spec validator
│
├── docs/
│   ├── tutorials/             # This directory!
│   │   ├── 01_GITHUB_ACTIONS_GUIDE.md
│   │   ├── 02_PROMETHEUS_GUIDE.md
│   │   └── 03_GRAFANA_GUIDE.md
│   └── openapi/               # API documentation
│
└── docker-compose.yml         # Service orchestration
```

---

## Getting Help

**If you get stuck:**

1. **Check the Troubleshooting section** in the relevant tutorial
2. **Review the Quick Reference** at the end of each tutorial
3. **Check the logs:**
```bash
# GitHub Actions: View in GitHub UI
# Prometheus: docker logs mt5-prometheus
# Grafana: docker logs mt5-grafana
```
4. **Verify services are running:**
```bash
docker-compose --profile monitoring ps
```
5. **Search the official docs** (links provided in each tutorial)

---

## Feedback & Improvements

Found something confusing? Have suggestions?
- These tutorials are designed to be improved based on feedback
- Comments and questions welcome!
- Contributions appreciated

---

## Ready to Start?

**Choose your path:**

- 👉 **[Tutorial 01: GitHub Actions →](01_GITHUB_ACTIONS_GUIDE.md)**
- 👉 **[Tutorial 02: Prometheus →](02_PROMETHEUS_GUIDE.md)**
- 👉 **[Tutorial 03: Grafana →](03_GRAFANA_GUIDE.md)**

**Or jump to specific topics using the table of contents in each tutorial.**

Happy learning! 🚀
