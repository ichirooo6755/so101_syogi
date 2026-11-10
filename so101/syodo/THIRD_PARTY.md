# Third-party data

## KanjiVG

The optional stroke and radical curricula download selected SVG files from:

- Project: KanjiVG
- Authors: Ulrich Apel and KanjiVG contributors
- Repository: https://github.com/KanjiVG/kanjivg
- Pinned release: `r20250816`
- License: Creative Commons Attribution-ShareAlike 3.0 Unported
- License text: https://creativecommons.org/licenses/by-sa/3.0/

Downloaded files are stored in `data/kanjivg/` and are not included in this
repository. The project's MIT license does not replace or restrict the KanjiVG
license. Trajectories produced from those SVG files are adapted from KanjiVG
and should retain the required attribution and share-alike terms when
distributed.

The trained artifacts `models/education-kanji-ppo.zip` and
`models/beauty-techniques-ppo.zip` were learned from these trajectories. They
are not covered by the repository's MIT license. The KanjiVG-derived parts are
distributed under CC BY-SA 3.0 with the same KanjiVG attribution.

## AnimCJK

The realistic-brush curricula optionally download Japanese kaisho stroke
outlines and medians from:

- Project: AnimCJK
- Author: parsimonhi and AnimCJK contributors
- Repository: https://github.com/parsimonhi/animCJK
- Pinned revision: `ec5e17cca76c87587790bcbce5ea0b4d4fb753d6`
- File: `graphicsJa.txt`
- License: Arphic Public License
- License summary and source notice: https://github.com/parsimonhi/animCJK#licences

The data supplies one filled outline and one median per Japanese stroke. This
project uses the authored medians as the professional curriculum's executable
centre-lines and samples the distance from each median to its outline to obtain
a target line-width profile; it does not copy `graphicsJa.txt` into the repository. The
download is cached under `data/animcjk/`. AnimCJK states that the `graphics*`
files and kanji SVGs are distributed under the Arphic Public License. That
license and the upstream attribution continue to apply to derived data and
trained artifacts; the repository's MIT license does not replace them.

The trained artifact `models/beauty-techniques-ppo.zip` uses width profiles
derived from these outlines. It is a combined derivative of KanjiVG and
AnimCJK data, so both upstream notices and applicable license terms must be
retained when it is redistributed.

Professional Motoya-ready runs derive stroke count, order, and type from
KanjiVG and Japanese centre-lines and widths from AnimCJK. Motoya contours are
used only when the user explicitly supplies that licensed font.

## Aoyagi Kouzan Mouhitu Font

The default professional final-image exemplar is the freely distributed
Aoyagi Kouzan brush font:

- Calligrapher and creator: Kouzan Aoyagi
- Distributor: Musashi System
- Project and terms: https://opentype.jp/kouzanmouhitufont.htm
- Download: https://opentype.jp/bin/KouzanMouhituFont.zip
- ZIP SHA-256: `453a35f6ca1bd5863aa06827ebbd2c41d8676fc1d9d705e5a0eb027ce3907f9a`
- TTF SHA-256: `582f269574e71336f1ee8318664ff6cfafd84293b3267ddf39410015713c951e`

The official page describes the font as free to use, including commercial use,
logos, publication, and CD inclusion, without warranty. The project downloads
and verifies it into `data/professional/`; the font file itself is not committed.
Rendered glyphs provide the global/local image observation and reward. A tightly
bounded low-order normal fit also guides AnimCJK medians toward nearby exemplar
ink without changing the stroke count or order.

## KANJIDIC2

The education-kanji curriculum downloads current grade and stroke-count
metadata from:

- Project: KANJIDIC2
- Copyright: Electronic Dictionary Research and Development Group
- Project page: https://www.edrdg.org/kanjidic/kanjd2index_legacy.html
- Data URL: https://www.edrdg.org/kanjidic/kanjidic2.xml.gz
- License: Creative Commons Attribution-ShareAlike 4.0 International
- License statement: https://www.edrdg.org/edrdg/licence.html

The downloaded file is stored in `data/kanjidic2/` and is not included in this
repository. It is used to select the entries whose `grade` field is 1 through
6 or 8; the validated set contains all 2,136 joyo kanji. EDRDG does not endorse
this project and provides the data without warranty.

## S Motoya Seikaisho 5 ProN

Professional image-conditioned learning can optionally render from a locally licensed
copy of S Motoya Seikaisho 5 ProN:

- Vendor: Motoya Co., Ltd.
- Product: https://www.motoyafont.jp/font-list/seikai.html
- License information: https://www.motoyafont.jp/license/

This commercial font is not downloaded, cached, committed, or redistributed by
the project. Users must obtain the appropriate license and provide a local path.
The loader validates the font name table. If no Motoya path is supplied, the
verified Aoyagi teacher above is used explicitly; a wrong path is never silently
accepted. KanjiVG remains the source of stroke count, order, and type, and
AnimCJK remains the primary source of Japanese medians and widths.

## Morisawa fonts (local licensed exemplar)

Professional training can optionally use a locally licensed Morisawa teacher via
`--exemplar-font` or `SO101_EXEMPLAR_FONT`. This repository does not download,
cache, commit, or redistribute Morisawa font files. Users with a Morisawa
membership must provide an absolute path on their machine. The loader checks
joyo glyph coverage and a render smoke test only; font name verification is
not enforced for Morisawa paths (unlike the Motoya-specific validator).

## CalliRewrite

The modular image-to-motion calibration design was informed by CalliRewrite:

- Project: CalliRewrite
- Repository: https://github.com/LoYuXr/CalliRewrite
- License: MIT

No CalliRewrite source or its historical dependency stack is bundled. The
brush, ink, and reward implementation in this repository is an independent
MuJoCo/Gymnasium implementation.
