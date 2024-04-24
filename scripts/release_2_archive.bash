#!/usr/bin/bash

# Split the dataset into several archives, same as the ones officially released.

mydir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
indir=$(sed -n -e 's/^export_dir://p' $mydir/config.yaml | tr -d '"' | xargs)
archive="$(dirname $indir)/$(basename $indir)"

trap "exit" INT

# Archive everything, excluding polar transformed images
7z a -mx=5 -r "${archive}.7z" $indir -xr'!*/aris_polar/*'

# Archive only the polar transformed images
# the xargs above makes sure that $indir doesn't contain any whitespaces
7z a -mx=5 -r "${archive}_polar.7z" -ir'!'"${$indir}/*/aris_polar/*"

echo "Created archive: $archive"
