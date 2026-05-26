#!/bin/bash
# Check if kokoro-tts is installed and models are available.
echo "=== Kokoro Verification $(date) ==="
if command -v kokoro-tts &> /dev/null; then
    echo "kokoro-tts found in PATH"
else
    echo "ERROR: kokoro-tts not found in PATH"
fi
MODEL_DIR="$HOME/.local/share/kokoro-tts"
ONNX="$MODEL_DIR/kokoro-v1.0.onnx"
VOICES="$MODEL_DIR/voices-v1.0.bin"
if [ -f "$ONNX" ]; then
    echo "Found ONNX model: $ONNX"
else
    echo "Missing ONNX model: $ONNX"
fi
if [ -f "$VOICES" ]; then
    echo "Found voices file: $VOICES"
else
    echo "Missing voices file: $VOICES"
fi
