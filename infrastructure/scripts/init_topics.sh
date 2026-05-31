#!/bin/bash
set -e

echo "Waiting for Redpanda..."
until docker exec agents-redpanda rpk cluster health > /dev/null 2>&1; do sleep 2; done

create_topic() {
    local topic=$1
    local partitions=$2
    if docker exec agents-redpanda rpk topic list 2>/dev/null | grep -q "^${topic}"; then
        echo "  [skip] ${topic}"
    else
        docker exec agents-redpanda rpk topic create "${topic}" --partitions "${partitions}" --replicas 1
        echo "  [created] ${topic}"
    fi
}

echo "Creating topics..."
create_topic "agent.task.requested" 3
create_topic "agent.task.resumed"   3
create_topic "agent.task.completed" 3
create_topic "agent.task.failed"    3

echo ""
docker exec agents-redpanda rpk topic list