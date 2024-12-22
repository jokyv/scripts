#!/usr/bin/env bash

set -e
exec grub-mkconfig -o /boot/grub/grub.cfg "$@"
