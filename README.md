---
title: SRE Agent Sandbox
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
tags:
  - openenv
---

# SRE Agent Sandbox: DevOps Troubleshooting Environment

An OpenEnv-compliant Sandbox-as-a-Service designed for evaluating LLM agents on real-world Site Reliability Engineering (SRE) and DevOps tasks. This environment simulates broken Linux systems (Ubuntu 22.04) and challenges agents to diagnose and fix critical infrastructure issues.

## Environment Description and Motivation

The SRE Agent Sandbox provides a safe, isolated, and reproducible environment where an agent acts as a System Administrator. The motivation is to provide a standardized benchmark for evaluating the troubleshooting capabilities of Large Language Models (LLMs) in a realistic terminal-based setting.

The environment implements a dual-mode execution strategy:
1. Docker Mode: Spawns isolated Ubuntu containers for local or Docker-in-Docker testing.
2. Subprocess Fallback: Automatically detects and runs commands natively inside the host container, optimized for environments like Hugging Face Spaces where Docker-in-Docker is restricted.

### Core Features
- Typed Actions and Observations: Powered by Pydantic for strict schema validation.
- Checkpoint-based Rewards: Partial credit (0.0 to 1.0) for discovery and partial progress.
- Dynamic Penalties: Scores are reduced for inefficient behaviors such as brute-forcing, excessive command counts, or leaving temporary files.
- Automated Cleanup: Deep cleanup between episodes ensures a fresh state for every task.

## Spec Space Definitions

### Action Space (SreAgentAction)
The agent interacts with the sandbox via bash commands.
- **command** (string): The raw bash command to execute in the Ubuntu sandbox container.

### Observation Space (SreAgentObservation)
Returns a comprehensive snapshot of the terminal and task context.
- **terminal_output** (string): Combined stdout and stderr from the last executed command.
- **task_description** (string): Human-readable description of what needs to be fixed.
- **task_id** (string): Unique identifier for the current scenario.
- **current_step** (integer): Current step number in the episode (maximum 20).
- **reward** (float): Reward delta from the last action.
- **done** (boolean): True if the task is solved (score reaches 1.0) or maximum steps are reached.

## Task Scenarios and Problem Statements

The environment includes six tiered tasks ranging from basic permission fixes to complex service discovery issues.

| Level | Task ID | Name | Problem Statement |
| :--- | :--- | :--- | :--- |
| **Easy** | task_1_permissions | Fix File Permissions | A critical web page file has its permissions set to 000. Fix it so the web server can serve it. |
| **Medium** | task_2_service | Restart Crashed Web Server | Nginx has crashed and left a stale PID file. Clean up state and restart the service. |
| **Hard** | task_3_nginx_config | Fix Broken Nginx Configuration | Nginx has a syntax error in its configuration file preventing startup. |
| **Medium** | task_4_port_conflict | Resolve Port Conflict | Port 80 is occupied by a rogue Python process. Terminate it and start Nginx. |
| **Hard** | task_5_disk_pressure | Emergency Disk Clearance | A 10MB rogue log file has filled the expected disk space. Remove it and restart rsyslog. |
| **Hard** | task_6_dns_poisoning | Fix Local Service Discovery | Local hostname resolution for 'db.local' is poisoned in the hosts file. |

## Grading System (Rewards and Penalties)

Grading is deterministic and based on the internal state of the sandbox.

### Task 1: Fix File Permissions
- **Rewards**: 1.0 if file exists with permissions 644, 755, or 664; 0.5 for any other non-zero permissions.
- **Penalties**: -0.2 for leaving backup files in the directory; -0.1 for using more than 10 commands.

### Task 2: Restart Crashed Web Server
- **Rewards**: +0.3 for removing the stale PID or validating it; +0.3 for Nginx process running; +0.4 for port 80 listening.
- **Penalties**: -0.1 for using 'kill -9' brute-force; -0.2 if the specific placeholder '99999' PID value persists.

### Task 3: Fix Broken Nginx Configuration
- **Rewards**: +0.4 if 'nginx -t' passes; +0.3 for Nginx process running; +0.3 if curl to localhost returns 200 OK.
- **Penalties**: -0.15 for leaving backup/temporary files; -0.1 for installing unrelated software bloat.

### Task 4: Resolve Port Conflict
- **Rewards**: +0.4 for killing the rogue Python process; +0.6 for Nginx listening on port 80.

### Task 5: Emergency Disk Clearance
- **Rewards**: +0.5 if the rogue 10MB file is removed; +0.5 if rsyslog service is running.
- **Penalties**: -0.4 for deleting the entire /var/log/app directory instead of the specific file.

### Task 6: Fix Local Service Discovery
- **Rewards**: 1.0 if 'db.local' resolves to 127.0.0.1; 0.4 if the poisoned IP is removed but not correctly remapped.
- **Penalties**: -0.2 for using more than 5 commands for a single file edit.

## Setup & Installation

### Prerequisites
- Python 3.11+
- Docker (optional, but recommended for local isolation)

### Installation
```bash
git clone https://github.com/Shreyasjain2/MetaPytorch-Hackathon-SRE
cd MetaPytorch-Hackathon-SRE
pip install -e .
pip install -r server/requirements.txt
```

### Running the Environment Server
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
python -m uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Running with Docker (Recommended)
```bash
docker build -t sre-agent .
docker run -p 7860:7860 sre-agent
```

## Running Inference

Ensure environment variables are set (API_BASE_URL, MODEL_NAME, and HF_TOKEN/API_KEY).

```bash
python inference.py
```

## Baseline Scores

The following scores were obtained using llama-3.3-70b-versatile:
- **Task 1 (Easy):** 1.00 / 1.00
- **Task 2 (Medium):** 1.00 / 1.00
- **Task 3 (Hard):** 1.00 / 1.00
- **Task 4 (Medium):** 1.00 / 1.00
- **Task 5 (Hard):** 0.00 / 1.00 (Agent failure to pivot from Nginx focus)
- **Task 6 (Hard):** 1.00 / 1.00
- **Overall Average:** 0.83 / 1.00

## OpenEnv Standard

This project adheres to the OpenEnv standard for agent-environment interaction, ensuring compatibility with OpenEnv-compliant evaluation frameworks.

## License

This project is licensed under the BSD-style license found in the LICENSE file.
