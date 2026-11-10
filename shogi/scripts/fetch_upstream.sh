#!/bin/sh
set -eu

# Clone only missing upstream dependencies. Never alter an existing checkout.
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
mkdir -p "$root/vendor"
fetch_one() {
  dest=$1
  url=$2
  revision=$3
  if [ -e "$dest" ]; then
    printf '%s\n' "Already exists; leaving unchanged: $dest"
    return
  fi
  git clone --filter=blob:none --no-checkout "$url" "$dest"
  git -C "$dest" checkout --detach "$revision"
}
fetch_one "$root/vendor/Fairy-Stockfish" https://github.com/fairy-stockfish/Fairy-Stockfish.git 53c1f2bd14a2d3b685904ccf8ec9dec8401800ff
fetch_one "$root/vendor/so101-manipulation-eval" https://github.com/FERBIN12/so101-manipulation-eval.git b02b8b2e300733dbe76cead4f3a57425c37955fe
