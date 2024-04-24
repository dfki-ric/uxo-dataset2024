#!/usr/bin/bash

# Split the dataset into several archives, same as the ones officially released.

mydir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
indir=$(sed -n -e 's/^export_dir://p' $mydir/config.yaml | tr -d '"' | xargs)
archive="$(dirname $indir)/archives/$(basename $indir)"

trap "exit" INT
mkdir -p "$(dirname $indir)/archives/"

# Recordings, excluding polar transformed images
7z a -mx=5 -r "${archive}_recordings.7z" $indir/recordings/ -xr'!*/aris_polar/*'

# Only the polar transformed images
7z a -mx=5 -r "${archive}_polar.7z" -ir'!'"${$indir}/*/aris_polar/*"

# 3d models
7z a -mx=5 -r "${archive}_3dmodels.7z" $indir/3d_models/

# Scripts
7z a -mx=5 -r "${archive}_scripts.7z" $indir/scripts/

echo "Created archive: $archive"
