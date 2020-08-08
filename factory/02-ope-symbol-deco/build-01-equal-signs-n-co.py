#! /usr/bin/env python3

import re

from mistool.os_use import PPath
from mistool.string_use import between, joinand
from orpyste.data import ReadBlock

BASENAME = PPath(__file__).stem.replace("build-", "")
BASENAME = BASENAME.replace("[slow]", "")

THIS_DIR = PPath(__file__).parent

DECO_TRANS_DIR  = THIS_DIR / BASENAME

STY_FILE = THIS_DIR / f'{BASENAME}.sty'
TEX_FILE = STY_FILE.parent / (STY_FILE.stem + "[fr].tex")

PATTERN_FOR_PEUF = re.compile("\d+-(.*)")
match            = re.search(PATTERN_FOR_PEUF, STY_FILE.stem)
PEUF_FILE        = STY_FILE.parent / (match.group(1).strip() + ".peuf")

DECO = " "*4


# ------------------ #
# -- TRANSLATIONS -- #
# ------------------ #

DEFAULT_LANG = "english"
ALL_LANGS    = {}

for onetranspeuf in DECO_TRANS_DIR.walk("file::*.peuf"):
    lang = onetranspeuf.stem

    with ReadBlock(
        content = onetranspeuf,
        mode    = 'keyval:: ='
    ) as data:
        ALL_LANGS[lang] = {
            k:(v if v else k)
            for k, v in data.mydict("std mini")["deco"].items()
        }

ALL_DECOS = list(ALL_LANGS[DEFAULT_LANG].keys())
ALL_DECOS.sort()
SET_ALL_DECOS = set(ALL_DECOS)

for lang, trans in ALL_LANGS.items():
    if lang != DEFAULT_LANG:
        if set(trans.keys()) != SET_ALL_DECOS:
            raise Exception(
                f"missing deco(s) in the file << {lang}.peuf >>"
            )


# -------------------------- #
# -- THE OPERATORS TO ADD -- #
# -------------------------- #

with ReadBlock(
    content = PEUF_FILE,
    mode    = {
        'verbatim'  : "decorations",
        'keyval:: =': ":default:"
    }
) as data:
    INFOS = data.mydict("std mini")

    INFOS["decorations"] = [
        d.strip()
        for d in INFOS["decorations"]
        if d.strip()
    ]


STAR_VERSIONS = {
    "*" : {},
    "**": {},
}

stardeco = ["**", "*"]
macromet = []

for macro, latexdef in INFOS["stars"].items():
    for onedeco in stardeco:
        if macro in macromet:
            continue

        nbstars = len(onedeco)

        if macro.endswith(onedeco):
            STAR_VERSIONS[onedeco][macro[:-nbstars]] = latexdef

            macromet.append(macro)

del INFOS["stars"]

ALL_LOCAL_DECOS = [
    d
    for d in INFOS["decorations"]
]

if not(set(ALL_LOCAL_DECOS) <= SET_ALL_DECOS):
    raise Exception("see the decorations used")

easydecos = {}

for symbnames, decos in INFOS["todecorate"].items():
    if decos == ":all:":
        decos = ALL_LOCAL_DECOS

    elif decos.startswith(":not:"):
        toignore = [
            d.strip()
            for d in decos[len(":not:"):].split(',')
        ]


        decos = [
            d
            for d in ALL_LOCAL_DECOS
            if d not in toignore
        ]

    else:
        decos = [
            d.strip()
            for d in decos.split(',')
        ]

    for onesymbname in symbnames.split(","):
        onesymbname = onesymbname.strip()

        easydecos[onesymbname] = decos

INFOS["todecorate"] = easydecos


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

ALL_OPES_DECO = []

newmacros = []

for symbname, decos in INFOS["todecorate"].items():
    symb = INFOS["latex"][symbname]
    newmacros.append('')

    for onedeco in decos:
        macroname   = symbname + onedeco
        textversion = f"\\tns@over@math@symbol{{\\txtop{onedeco}}}{{{symb}}}"

        ALL_OPES_DECO.append(macroname)

# Double star version
        if macroname in STAR_VERSIONS["**"]:
            onestarver  = STAR_VERSIONS["*"][macroname]
            twostarsver = STAR_VERSIONS["**"][macroname]

            ALL_OPES_DECO += [ALL_OPES_DECO[-1] + "*"]
            ALL_OPES_DECO += [ALL_OPES_DECO[-1] + "*"]

            newmacros += [
f"\\newcommand\\{macroname}{{\@ifstar{{\\tnslog@{macroname}@pre@star}}{{\\tnslog@{macroname}@no@star}}}}",
f"\\newcommand\\tnslog@{macroname}@pre@star{{\@ifstar{{\\tnslog@{macroname}@star@star}}{{\\tnslog@{macroname}@star}}}}",
f"\\newcommand\\tnslog@{macroname}@no@star{{{textversion}}}",
f"\\newcommand\\tnslog@{macroname}@star{{{onestarver}}}",
f"\\newcommand\\tnslog@{macroname}@star@star{{{twostarsver}}}",
""
            ]

# Simple star version
        elif macroname in STAR_VERSIONS["*"]:
            onestarver  = STAR_VERSIONS["*"][macroname]

            ALL_OPES_DECO += [ALL_OPES_DECO[-1] + "*"]

            newmacros += [
f"\\newcommand\\{macroname}{{\@ifstar{{\\tnslog@{macroname}@star}}{{\\tnslog@{macroname}@no@star}}}}",
f"\\newcommand\\tnslog@{macroname}@no@star{{{textversion}}}",
f"\\newcommand\\tnslog@{macroname}@star{{{onestarver}}}",
""
            ]

# No star version
        else:
            newmacros.append(
f"\\newcommand\\{macroname}{{{textversion}}}"
            )

newmacros = '\n'.join(newmacros[1:])

template_sty = text_start + f"""
{newmacros}
""" + text_end


# ---------------------- #
# -- UPDATING THE DOC -- #
# ---------------------- #

text_start, _, text_end = between(
    text = template_tex,
    seps = [
        "% == All texts - START == %\n",
        "\n% == All texts - END == %"
    ],
    keepseps = True
)

alldecos = [
    d
    for d in INFOS["decorations"]
]
alldecos.sort()

textversions = []

nbdecos = len(ALL_DECOS)

for pos in range(0, nbdecos, 2):
    onedeco  = ALL_DECOS[pos]

    textversions.append(
        f"{DECO*2}\\macro{{txtop{onedeco}\\{{\\}}}} "
        f"& donne \\emph{{\\og \\txtop{onedeco} \\fg}}"
    )

    if pos < nbdecos - 1:

        onedeco = ALL_DECOS[pos+1]

        textversions.append(
            f"{DECO*2}& \\macro{{txtop{onedeco}\\{{\\}}}} "
            f"& donne \\emph{{\\og \\txtop{onedeco} \\fg}} \\\\"
        )

    else:
        textversions.append(f"{DECO*2}& & \\\\")


textversions = "\n".join(textversions)

template_tex = text_start + textversions + text_end


text_start, _, text_end = between(
    text = template_tex,
    seps = [
        "% == Technical infos - Texts - START == %\n",
        "\n% == Technical infos - Texts - END == %"
    ],
    keepseps = True
)

alldecos = [
    f"txtop{d}"
    for d in ALL_DECOS
]

alldecos = ", ".join(alldecos)

template_tex = text_start + f"""
\\foreach \\k in {{{alldecos}}}{{

	\\IDmacro[n]{{\k}}

}}
""" + text_end


text_start, _, text_end = between(
text = template_tex,
seps = [
    "% == Technical infos - Operators - START == %\n",
    "\n% == Technical infos - Operators - END == %"
],
keepseps = True
)


template_tex = []
lastopes     = []
lastfirst    = ""

for oneope in ALL_OPES_DECO + ["ZZZZ-unsed-ZZZZ"]:
    if lastfirst:
        if lastfirst != oneope[0]:
            lastfirst = oneope[0]

            lastopes = ", ".join(lastopes)

            template_tex.append(
                f"""
\\begin{{multicols}}{{6}}
    \\foreach \\k in {{{lastopes}}}{{
        \\IDope{{\k}}

    }}
\\end{{multicols}}

\\separation
                """.rstrip()
            )

            lastopes     = []

    else:
        lastfirst = oneope[0]

    lastopes.append(oneope)

template_tex = "\n".join(template_tex[:-3])
template_tex = f"{text_start}{template_tex}{text_end}"


# ----------------------------------- #
# -- UPDATES THE TRANSLATED MACROS -- #
# ----------------------------------- #

for lang, trans in ALL_LANGS.items():
    lang = lang.upper()

    text_start, _, text_end = between(
        text = template_sty,
        seps = [
            f"% == Decorations - {lang} - START == %",
            f"% == Decorations - {lang} - END == %"
        ],
        keepseps = True
    )

    texlines = [
        f"\\newcommand\\txtop{word}{{{wtrans}}}"
        for word, wtrans in trans.items()
    ]

    texlines = "\n    ".join(texlines)

    template_sty = f"""
{text_start}
    {texlines}
{text_end}
    """.strip()


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
