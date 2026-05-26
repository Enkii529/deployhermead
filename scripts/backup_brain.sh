#!/bin/bash
# Backup the Brain directory to a dated tarball.
BACKUP_DIR="$HOME/hermes/backups"
BRAIN_DIR="/media/sf_ClawdbotShared/Brain"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE="$BACKUP_DIR/brain_backup_$TIMESTAMP.tar.gz"
mkdir -p "$BACKUP_DIR"
tar --exclude='*.tmp' --exclude='temp/*' --exclude='cache/*' --exclude='*.log' -czf "$ARCHIVE" -C "$BRAIN_DIR" .
echo "Brain backup created: $ARCHIVE"
