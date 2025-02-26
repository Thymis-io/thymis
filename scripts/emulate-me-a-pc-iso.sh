#!/usr/bin/env bash

qemu-system-x86_64 -boot d --enable-kvm -cpu host -smp 8 -m 2G \
  -cdrom $@
