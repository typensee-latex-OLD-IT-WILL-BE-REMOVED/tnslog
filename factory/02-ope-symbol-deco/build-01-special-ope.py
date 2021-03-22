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

STY_CONTENT = []
TEX_CONTENT = []

PATTERN_FOR_PEUF = re.compile("\d+-(.*)")
match            = re.search(PATTERN_FOR_PEUF, STY_FILE.stem)
PEUF_FILE        = STY_FILE.parent / (match.group(1).strip() + ".peuf")

DECO = " "*4


# -------------------------- #
# -- THE OPERATORS TO ADD -- #
# -------------------------- #

with ReadBlock(
    content = PEUF_FILE,
    mode    = 'keyval:: ='
) as data:
    INFOS = data.mydict("std mini")


# ------------------- #
# -- SHORT SYMBOLS -- #
# ------------------- #

if 'short' in INFOS:
    STY_CONTENT.append("""
    % Source for the short sysmbols.
    %    * https://tex.stackexchange.com/a/585267/6880
    """.strip())

    template_sty = """
    \\newcommand\short{macroname}{{\mathrel{{\mathpalette\short{macroname}@{{.55}}}}}}
    \\newcommand{{\short{macroname}@}}[2]{{%
    \\resizebox{{#2\width}}{{\height}}{{$\m@th#1{latexsymbol}$}}%
    }}
    """.strip()

    for macroname, latexsymbol in INFOS['short'].items():
        STY_CONTENT.append(
            template_sty.format(
                macroname = macroname,
                latexsymbol = latexsymbol
            )
        )

    del INFOS['short']


# ------------------------------------ #
# -- NEGATIVE VERSIONS OF OPERATORS -- #
# ------------------------------------ #

ALL_OPERATORS      = []
EXISTING_OPERATORS = []
NEW_OPERATORS      = {}

for macroname, latexsymbol in INFOS['operators'].items():
    if macroname[-1] == "*":
        macroname                = f"n{macroname[:-1]}"
        NEW_OPERATORS[macroname] = latexsymbol
        ALL_OPERATORS.append(macroname)

    else:
        ALL_OPERATORS.append(macroname)

        if f"{macroname}*" not in INFOS['operators']:
            EXISTING_OPERATORS.append(f"n{macroname}")
            ALL_OPERATORS.append(f"n{macroname}")

        if not latexsymbol:
            EXISTING_OPERATORS.append(macroname)

        else:
            NEW_OPERATORS[macroname] = latexsymbol

del INFOS['operators']


# ---------------------------------- #
# -- SYMBOLIC DECORATED OPERATORS -- #
# ---------------------------------- #

SYMBO_DECO_OPE = {}

startkind    = len("symbolic-")
template_sty = " "*4*3 + "{{{onedeco}}}{{{latexcode}}}%"

for symbolic_kind, symbolic_decos in INFOS.items():
    this_ope    = symbolic_kind[startkind:]
    notversions = {}

# Positive versions.
    sty_code = []

    for onedeco, latexcode in symbolic_decos.items():
        if onedeco[-1] == "*":
            notversions[onedeco[:-1]] = latexcode

        else:
            sty_code.append(
                template_sty.format(
                    onedeco   = onedeco,
                    latexcode = latexcode
                )
            )

    SYMBO_DECO_OPE[this_ope] = "\n".join(sty_code)

# Negative versions.
    this_ope = "n" + this_ope

    sty_code = []

    for onedeco, latexcode in symbolic_decos.items():
        if onedeco[-1] == "*":
            continue

        elif onedeco in notversions:
            latexcode = notversions[onedeco]

        else:
            latexcode = f"\\centernot{latexcode}"

        sty_code.append(
            template_sty.format(
                onedeco   = onedeco,
                latexcode = latexcode
            )
        )

    SYMBO_DECO_OPE[this_ope] = "\n".join(sty_code)


# ------------------------- #
# -- DECORABLE OPERATORS -- #
# ------------------------- #

STY_CONTENT.append("""
% Decorable operators.

\\newcommand\\coldecoope{blue}

\\newcommand\\txtdecoope[1]{%
	\\textscale{.75}{\\text{\\color{\\coldecoope}#1}}%
}
""".strip())

template_let_old = """
\\let\\old{macroname}\\{macroname}
\\renewcommand\\{macroname}{{\\@ifstar{{\\tnslog@{macroname}@star}}{{\\tnslog@{macroname}@no@star}}}}
""".strip()

template_new = """
\\newcommand\\{macroname}{{\\@ifstar{{\\tnslog@{macroname}@star}}{{\\tnslog@{macroname}@no@star}}}}
""".strip()

template_stars_no_switch = """
\\newcommand\\tnslog@{macroname}@no@star[1][]{{%
    \\if\\relax\\detokenize{{#1}}\\relax%
    	{latexsymbol}%
    \\else%
        \\tns@over@math@symbol{{\\txtdecoope{{#1}}}}{{{latexsymbol}}}%
    \\fi%
}}

\\newcommand\\tnslog@{macroname}@star[1][]{{%
    \\if\\relax\\detokenize{{#1}}\\relax%
    	{latexsymbol}%
    \\else%
        \\tns@over@math@symbol{{\\txtdecoope{{#1}}}}{{{latexsymbol}}}%
    \\fi%
}}
""".strip()

template_stars_switch = """
\\newcommand\\tnslog@{macroname}@no@star[1][]{{%
    \\if\\relax\\detokenize{{#1}}\\relax%
    	{latexsymbol}%
    \\else%
        \\tns@over@math@symbol{{\\txtdecoope{{#1}}}}{{{latexsymbol}}}%
    \\fi%
}}

\\newcommand\\tnslog@{macroname}@star[1][]{{%
    \\if\\relax\\detokenize{{#1}}\\relax%
    	{latexsymbol}%
    \\else%
        \\IfEqCase{{#1}}{{%
{swithcases}
        }}[%
            \\tns@over@math@symbol{{\\txtdecoope{{#1}}}}{{{latexsymbol}}}%
        ]%
    \\fi%
}}
""".strip()

for macroname in ALL_OPERATORS:
    if macroname in EXISTING_OPERATORS:
        latexsymbol = f"\\old{macroname}"

        STY_CONTENT.append(
            template_let_old.format(macroname = macroname)
        )

    else:
        latexsymbol = NEW_OPERATORS[macroname]

        STY_CONTENT.append(
            template_new.format(macroname = macroname)
        )


    if macroname in SYMBO_DECO_OPE:
        STY_CONTENT.append(
            template_stars_switch.format(
                macroname   = macroname,
                latexsymbol = latexsymbol,
                swithcases  = SYMBO_DECO_OPE[macroname]
            )
        )

    else:
        STY_CONTENT.append(
            template_stars_no_switch.format(
                macroname   = macroname,
                latexsymbol = latexsymbol
            )
        )

STY_CONTENT = "\n\n".join(STY_CONTENT)


# -------------------------- #
# -- UPDATES OF THE FILES -- #
# -------------------------- #

with open(
    file     = STY_FILE,
    mode     = 'r',
    encoding = 'utf-8'
) as styfile:
    template_sty = styfile.read()


text_start, _, text_end = between(
    text = template_sty,
    seps = [
        f"% == Decorations - START == %",
        f"% == Decorations - END == %"
    ],
    keepseps = True
)

template_sty = f"""
{text_start}

{STY_CONTENT}

{text_end}
""".strip()

with open(
    file     = STY_FILE,
    mode     = 'w',
    encoding = 'utf-8'
) as docfile:
    docfile.write(template_sty)
