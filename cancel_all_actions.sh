#!/usr/bin/env bash

# Define variables for parameters
LIMIT=250
STATUS="queued"
STATUS_1="in_progress"

echo "Fetching list of GitHub Actions runs with status: $STATUS (limit: $LIMIT)..."

# Fetch the list of database IDs for queued runs
# RUN_IDS=$(gh run list --limit $LIMIT --json databaseId,status -q ".[] | select(.status == \"$STATUS\") | .databaseId")
RUN_IDS=$(gh run list -s $STATUS --limit $LIMIT --json databaseId,status -q ".[] | .databaseId")
RUN_IDS_1=$(gh run list -s $STATUS_1 --limit $LIMIT --json databaseId,status -q ".[] | .databaseId")

RUN_IDS="$RUN_IDS $RUN_IDS_1"

# reverse the order of the runs
RUN_IDS=$(echo $RUN_IDS | tr " " "\n" | tac | tr "\n" " ")


# Check if any runs were found
if [ -z "$RUN_IDS" ]; then
    echo "No runs with status '$STATUS' found."
    exit 0
fi

echo "Found the following queued runs: $RUN_IDS"

# Loop through each run ID and cancel it
for ID in $RUN_IDS; do
    echo "Cancelling run with ID: $ID..."
    gh run cancel $ID
    if [ $? -eq 0 ]; then
        echo "Successfully cancelled run with ID: $ID"
    else
        echo "Failed to cancel run with ID: $ID"
    fi
done

echo "All queued runs have been processed."
