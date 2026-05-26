#!/bin/bash
# Media fallback: when ffmpeg is missing, directly copy audio files to destination.
# Usage: media_fallback.sh <source_file> <dest_file>
set -e
if ! command -v ffmpeg &> /dev/null; then
    echo "ffmpeg not found, using direct file delivery fallback" >&2
    cp "$1" "$2"
else
    echo "ffmpeg found, converting" >&2
    ffmpeg -i "$1" -codec:a libmp3lame -qscale:a 2 "$2"
fi
