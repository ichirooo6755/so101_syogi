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
fetch_one "$root/vendor/YaneuraOu" https://github.com/yaneurao/YaneuraOu.git 3b8d53fa8b976bf6d54656de43026e03f28722ce
fetch_one "$root/vendor/so101-manipulation-eval" https://github.com/FERBIN12/so101-manipulation-eval.git b02b8b2e300733dbe76cead4f3a57425c37955fe
