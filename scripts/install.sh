#!/bin/sh
# Get installation directory
# Create sub-directories 'code', 'extensions', 'profiles'
# Copy files from repository
# Copy launch and update scripts
# Make a venv and scripts packages
DEFAULT_DEST="$HOME/chattyboi"
DESTINATION=$DEFAULT_DEST
UPDATE_ON_COPY=$true

if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
  echo "This script will install ChattyBoi on your system."
  echo "Usage: ${basename $0} [destination] [--no-update]"
  echo "By default, files will be copied to $DEFAULT_DEST"
  echo "Any existing files will be overwritten."
  echo "Unless '--no-update' is passed, 'update.sh' will be launched automatically after copying files."
  echo "To launch ChattyBoi, execute 'launch.sh' in the installation directory."
  echo "Likewise, use 'update.sh' to update."
  exit 0
fi
if ! [ -z "$1" ] && ! [ "$1" = "--no-update" ]; then
  DESTINATION="$1"
  if [ "$2" = "--no-update" ]; then
    UPDATE_ON_COPY=$false
  fi
else
  if [ "$1" = "--no-update" ]; then
    UPDATE_ON_COPY=$false
  fi
fi

echo "Copying to $DESTINATION"
mkdir -p "$DESTINATION/code" "$DESTINATION/extensions" "$DESTINATION/profiles"
cp -r ../chattyboi/* "$DESTINATION/code"
python -m venv "$DESTINATION/code/venv"
$DESTINATION/code/venv/bin/python -m pip install -r "$DESTINATION/code/requirements.txt"
cp "launch.sh" "update.sh" "$DESTINATION"
if [ $UPDATE_ON_COPY = $true ]; then
  /bin/sh "$DESTINATION/update.sh"
fi
