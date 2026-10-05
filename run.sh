#!/bin/bash
sudo systemctl start docker
sudo docker compose -f rumqttd/docker-compose.yml up -d
sudo sysctl kernel.yama.ptrace_scope=0 # so we can hook dolphin
sudo -K
watchfiles "./.venv/bin/python main.py"
