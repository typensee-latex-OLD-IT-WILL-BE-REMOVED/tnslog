#! /usr/bin/env python3

import re

from mistool.os_use import PPath
from mistool.string_use import between, joinand
from orpyste.data import ReadBlock

BASENAME = PPath(__file__).stem.replace("build-", "")
BASENAME = BASENAME.replace("[slow]", "")

THIS_DIR = PPath(__file__).parent
STY_FILE = THIS_DIR / f'{BASENAME}.sty'
TEX_FILE = STY_FILE.parent / (STY_FILE.stem + "[fr].tex")

PATTERN_FOR_PEUF = re.compile("\d+-(.*)")
match            = re.search(PATTERN_FOR_PEUF, STY_FILE.stem)
PEUF_FILE        = STY_FILE.parent / (match.group(1).strip() + ".peuf")

DECO = " "*4


# -------------------------- #
# -- THE OPERATORS TO ADD -- #
# -------------------------- #

with ReadBlock(
    content = PEUF_FILE,
    mode    = {
        'verbatim'  : "decorations",
        'keyval:: =': ["latex", "todecorate"]
    }
) as data:
    infos = data.mydict("std mini")

    infos["decorations"] = [
        d.strip()
        for d in infos["decorations"]
        if d.strip()
    ]


# ------------------------- #
# -- TEMPLATES TO UPDATE -- #
# ------------------------- #

with open(
    file     = STY_FILE,
    mode     = 'r',
    encoding = 'utf-8'
) as styfile:
    template_sty = styfile.read()


with open(
    file     = TEX_FILE,
    mode     = 'r',
    encoding = 'utf-8'
) as docfile:
    template_tex = docfile.read()


# --------------------- #
# -- UPDATING MACROS -- #
# --------------------- #

text_start, _, text_end = between(
    text = template_sty,
    seps = [
        "% == Decorated versions - START == %\n",
        "\n% == Decorated versions - END == %"
    ],
    keepseps = True
)

newmacros   = []
latexmacros = []

for symb, assocdecos in infos["todecorate"].items():
    if symb in infos["latex"]:
        latexmacros.append(
            f"\\newcommand\\{symb}{{{infos['latex'][symb]}}}"
        )

    newmacros.append("")

    if assocdecos == ":all:":
        for onedeco in infos["decorations"]:
            newmacros.append(
f"\\newcommand\\{symb}{onedeco}{{\\tns@over@math@symbol{{\\txtop{onedeco}}}{{\\{symb}}}}}"
            )


newmacros   = '\n'.join(newmacros[1:])
latexmacros = '\n'.join(latexmacros)

template_sty = text_start + f"""
{latexmacros}

{newmacros}
""" + text_end


# ---------------------- #
# -- UPDATING THE DOC -- #
# ---------------------- #

text_start, _, text_end = between(
    text = template_tex,
    seps = [
        "% == Decorated versions - START == %\n",
        "\n% == Decorated versions - END == %"
    ],
    keepseps = True
)

texforidmacros = []

for symb, assocdecos in infos["todecorate"].items():
    if texforidmacros:
        texforidmacros.append("\\separation")

    somemacros = [symb]

    if assocdecos == ":all:":
        for onedeco in infos["decorations"]:
            somemacros.append(f"{symb}{onedeco}")

    somemacros = ", ".join(somemacros)

    texforidmacros.append(f"""
\\begin{{multicols}}{{4}}
    \\foreach \\k in {{{somemacros}}}{{
	   \\IDope{{\k}}

    }}
\\end{{multicols}}
    """)

texforidmacros = "\n".join(texforidmacros)
template_tex = text_start + texforidmacros + text_end


text_start, _, text_end = between(
    text = template_tex,
    seps = [
        "% == Vertical versions - START == %\n",
        "\n% == Vertical versions - END == %"
    ],
    keepseps = True
)

allmacros = [
    "v" + m
    for m in infos["todecorate"]
    if not m.startswith("n")
]

allmacros = ", ".join(allmacros)

template_tex = text_start + f"""
\\begin{{multicols}}{{4}}
    \\foreach \\k in {{{allmacros}}}{{

	   \\IDope{{\k}}

	   \\IDope{{n\k}}
    }}
\\end{{multicols}}
""" + text_end

# -------------------------- #
# -- UPDATES OF THE FILES -- #
# -------------------------- #

with open(
    file     = STY_FILE,
    mode     = 'w',
    encoding = 'utf-8'
) as docfile:
    docfile.write(template_sty)

with open(
    file     = TEX_FILE,
    mode     = 'w',
    encoding = 'utf-8'
) as docfile:
    docfile.write(template_tex)
