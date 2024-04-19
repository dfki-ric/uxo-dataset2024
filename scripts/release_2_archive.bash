#!/usr/bin/bash

# Split the dataset into several archives, same as the ones officially released.

mydir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
indir=$(sed -n -e 's/^export_dir://p' $mydir/config.yaml | tr -d '"')
archive="$(dirname $indir)/$(basename $indir)"

trap "exit" INT

# Archive everything, excluding polar transformed images
7z a -mx=5 -r "${archive}.7z" $1 -xr'!*/aris_polar/*'

# Archive only the polar transformed images
7z a -mx=5 -r "${archive}_polar.7z" -ir"!${1}*/aris_polar/*"

echo "Created archive: $archive"
