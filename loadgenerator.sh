#!/bin/bash

echo "Starting continuous load generation..."

# Loop forever
while true; do

  # For a random time between 30 and 60 seconds...

  # Stress CPU
  DURATION=$((RANDOM % 31 + 30))
  echo "Stressing CPU for $DURATION seconds..."
  stress-ng --cpu 0 --cpu-method all -t ${DURATION}s --metrics-brief

  # Stress I/O
  DURATION=$((RANDOM % 31 + 30))
  echo "Stressing I/O for $DURATION seconds..."
  stress-ng --io 4 --io-ops 100000 -t ${DURATION}s --metrics-brief

  # Stress Memory
  DURATION=$((RANDOM % 31 + 30))
  echo "Stressing memory for $DURATION seconds..."
  stress-ng --vm 2 --vm-bytes 1G -t ${DURATION}s --metrics-brief

  # Stress Network
  DURATION=$((RANDOM % 31 + 30))
  echo "Stressing Network for $DURATION seconds..."
  stress-ng --sock 2 --sock-domain ipv4 -t ${DURATION}s --metrics-brief

  echo "Cycle complete. Waiting 15 seconds before next cycle."
  sleep 15
done
