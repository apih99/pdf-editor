#!/bin/bash

# Start Xvfb
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
export DISPLAY=:99

# Create symbolic link to the wrapper script
ln -sf /usr/local/bin/wkhtmltopdf.sh /usr/local/bin/wkhtmltopdf

# Execute the main command
exec "$@" 