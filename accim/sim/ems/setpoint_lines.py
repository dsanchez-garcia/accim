# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Erl lines that set the adaptive setpoints (ACST and AHST) of each comfort standard (ComfStand)
and comfort mode (ComfMod), as in accim 0.x.

The key ``(ComfStand, None)`` holds the lines of a comfort standard whose lines do not depend on
the comfort mode, or that it uses for the comfort modes without their own key. The lines of every
combination are followed by :data:`ROUNDING`.
"""

from typing import Dict, Optional, Tuple, Union

__all__ = ['ROUNDING', 'SETPOINT_LINES']


def _lines(text: str) -> Tuple[str, ...]:
    return tuple(text.strip('\n').split('\n'))


#: Lines of each (ComfStand, ComfMod), or (ComfStand, None).
SETPOINT_LINES: Dict[Tuple[int, Optional[Union[int, float]]], Tuple[str, ...]] = {
    (0, None): _lines("""
if (ComfStand == 0) && (CurrentTime < 8)
set ACST = 27+ACSTtol
set AHST = 17+AHSTtol
elseif (ComfStand == 0) && (CurrentTime < 16)
set ACST = 25+ACSTtol
set AHST = 20+AHSTtol
elseif (ComfStand == 0) && (CurrentTime < 23)
set ACST = 25+ACSTtol
set AHST = 20+AHSTtol
elseif (ComfStand == 0) && (CurrentTime < 24)
set ACST = 27+ACSTtol
set AHST = 17+AHSTtol
endif
"""),
    (1, 0): _lines("""
if CoolingSeason == 1
if (CAT==1)
set ACST = 25.5+ACSTtol
elseif (CAT==2)
set ACST = 26+ACSTtol
elseif (CAT==3)
set ACST = 27+ACSTtol
endif
else
if (CAT==1)
set ACST = 25+ACSTtol
elseif (CAT==2)
set ACST = 25+ACSTtol
elseif (CAT==3)
set ACST = 25+ACSTtol
endif
endif
if CoolingSeason == 1
if (CAT==1)
set AHST = 23.5+AHSTtol
elseif (CAT==2)
set AHST = 23+AHSTtol
elseif (CAT==3)
set AHST = 22+AHSTtol
endif
else
if (CAT==1)
set AHST = 21+AHSTtol
elseif (CAT==2)
set AHST = 20+AHSTtol
elseif (CAT==3)
set AHST = 18+AHSTtol
endif
endif
"""),
    (1, 1): _lines("""
if (RMOT >= ACSTall) && (RMOT <= ACSTaul)
set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol
elseif CurrentTime < 7
set ACST = 27+ACSTtol
elseif CurrentTime < 15
set ACST = 50
elseif CurrentTime < 23
set ACST = 25+ACSTtol
elseif CurrentTime < 24
set ACST = 27+ACSTtol
endif
if (RMOT >= AHSTall) && (RMOT <= AHSTaul)
set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol
elseif CurrentTime < 7
set AHST = 17+AHSTtol
elseif CurrentTime < 23
set AHST = 20+AHSTtol
elseif CurrentTime < 24
set AHST = 17+AHSTtol
endif
"""),
    (1, 2): _lines("""
if (RMOT >= ACSTall) && (RMOT <= ACSTaul)
set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol
elseif (RMOT < ACSTall) && (CAT==1)
set ACST = 25+ACSTtol
elseif (RMOT > ACSTaul) && (CAT==1)
set ACST = 25.5+ACSTtol
elseif (RMOT < ACSTall) && (CAT==2)
set ACST = 25+ACSTtol
elseif (RMOT > ACSTaul) && (CAT==2)
set ACST = 26+ACSTtol
elseif (RMOT < ACSTall) && (CAT==3)
set ACST = 25+ACSTtol
elseif (RMOT > ACSTaul) && (CAT==3)
set ACST = 27+ACSTtol
endif
if (RMOT >= AHSTall) && (RMOT <= AHSTaul)
set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol
elseif (RMOT < AHSTall) && (CAT==1)
set AHST = 21+AHSTtol
elseif (RMOT > AHSTaul) && (CAT==1)
set AHST = 23.5+AHSTtol
elseif (RMOT < AHSTall) && (CAT==2)
set AHST = 20+AHSTtol
elseif (RMOT > AHSTaul) && (CAT==2)
set AHST = 23+AHSTtol
elseif (RMOT < AHSTall) && (CAT==3)
set AHST = 18+AHSTtol
elseif (RMOT > AHSTaul) && (CAT==3)
set AHST = 22+AHSTtol
endif
"""),
    (1, 3): _lines("""
if (RMOT >= ACSTall) && (RMOT <= ACSTaul)
set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol
elseif RMOT < ACSTall
set ACST = ACSTall*0.33+18.8+ACSToffset+ACSTtol
elseif RMOT > ACSTaul
set ACST = ACSTaul*0.33+18.8+ACSToffset+ACSTtol
endif
if (RMOT >= AHSTall) && (RMOT <= AHSTaul)
set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol
elseif RMOT < AHSTall
set AHST = AHSTall*0.33+18.8+AHSToffset+AHSTtol
elseif RMOT > AHSTaul
set AHST = AHSTaul*0.33+18.8+AHSToffset+AHSTtol
endif
"""),
    (2, 0): _lines("""
if CoolingSeason == 1
if (CAT==80)
set ACST = 27+ACSTtol
elseif (CAT==90)
set ACST = 26+ACSTtol
endif
else
if (CAT==80)
set ACST = 25+ACSTtol
elseif (CAT==90)
set ACST = 24+ACSTtol
endif
endif
if CoolingSeason == 1
if (CAT==80)
set AHST = 22+AHSTtol
elseif (CAT==90)
set AHST = 23+AHSTtol
endif
else
if (CAT==80)
set AHST = 19+AHSTtol
elseif (CAT==90)
set AHST = 20+AHSTtol
endif
endif
"""),
    (2, 1): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol
elseif CurrentTime < 7
set ACST = 27+ACSTtol
elseif CurrentTime < 15
set ACST = 50
elseif CurrentTime < 23
set ACST = 25+ACSTtol
elseif CurrentTime < 24
set ACST = 27+ACSTtol
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol
elseif CurrentTime < 7
set AHST = 17+AHSTtol
elseif CurrentTime < 23
set AHST = 20+AHSTtol
elseif CurrentTime < 24
set AHST = 17+AHSTtol
endif
"""),
    (2, 2): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol
elseif CAT==80
if PMOT < ACSTall
set ACST = 25+ACSTtol
elseif PMOT > ACSTaul
set ACST = 27+ACSTtol
endif
elseif CAT==90
if PMOT < ACSTall
set ACST = 24+ACSTtol
elseif PMOT > ACSTaul
set ACST = 26+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol
elseif CAT==80
if PMOT < AHSTall
set AHST = 19+AHSTtol
elseif PMOT > AHSTaul
set AHST = 22+AHSTtol
endif
elseif CAT==90
if PMOT < AHSTall
set AHST = 20+AHSTtol
elseif PMOT > AHSTaul
set AHST = 23+AHSTtol
endif
endif
"""),
    (2, 3): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.31+17.8+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.31+17.8+ACSToffset+ACSTtol
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.31+17.8+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.31+17.8+AHSToffset+AHSTtol
endif
"""),
    (3, 0): _lines("""
if (CAT==80)
set ACST = 28+ACSTtol
elseif (CAT==90)
set ACST = 27+ACSTtol
endif
if (CAT==80)
set AHST = 18+AHSTtol
elseif (CAT==90)
set AHST = 19+AHSTtol
endif
"""),
    (3, 1): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.48+14.4+ACSToffset+ACSTtol
elseif CAT==80
if PMOT < ACSTall
set ACST = 28+ACSTtol
elseif PMOT > ACSTaul
set ACST = 28+ACSTtol
endif
elseif CAT==90
if PMOT < ACSTall
set ACST = 27+ACSTtol
elseif PMOT > ACSTaul
set ACST = 27+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.48+14.4+AHSToffset+AHSTtol
elseif CAT==80
if PMOT < AHSTall
set AHST = 18+AHSTtol
elseif PMOT > AHSTaul
set AHST = 18+AHSTtol
endif
elseif CAT==90
if PMOT < AHSTall
set AHST = 19+AHSTtol
elseif PMOT > AHSTaul
set AHST = 19+AHSTtol
endif
endif
"""),
    (3, 2): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.48+14.4+ACSToffset+ACSTtol
elseif CAT==80
if PMOT < ACSTall
set ACST = 25+ACSTtol
elseif PMOT > ACSTaul
set ACST = 27+ACSTtol
endif
elseif CAT==90
if PMOT < ACSTall
set ACST = 24+ACSTtol
elseif PMOT > ACSTaul
set ACST = 26+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.48+14.4+AHSToffset+AHSTtol
elseif CAT==80
if PMOT < AHSTall
set AHST = 19+AHSTtol
elseif PMOT > AHSTaul
set AHST = 22+AHSTtol
endif
elseif CAT==90
if PMOT < AHSTall
set AHST = 20+AHSTtol
elseif PMOT > AHSTaul
set AHST = 23+AHSTtol
endif
endif
"""),
    (3, 3): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.48+14.4+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.48+14.4+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.48+14.4+ACSToffset+ACSTtol
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.48+14.4+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.48+14.4+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.48+14.4+AHSToffset+AHSTtol
endif
"""),
    (4, 3): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
if CAT == 1
set ACST = PMOT*0.77+12.04+ACSTtol
elseif CAT == 2
set ACST = PMOT*0.73+15.28+ACSTtol
endif
elseif PMOT < ACSTall
if CAT == 1
set ACST = ACSTall*0.77+12.04+ACSTtol
elseif CAT == 2
set ACST = ACSTall*0.73+15.28+ACSTtol
endif
elseif PMOT > ACSTaul
if CAT == 1
set ACST = ACSTaul*0.77+12.04+ACSTtol
elseif CAT == 2
set ACST = ACSTaul*0.73+15.28+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
if CAT == 1
set AHST = PMOT*0.87+2.76+AHSTtol
elseif CAT == 2
set AHST = PMOT*0.91-0.48+AHSTtol
endif
elseif PMOT < AHSTall
if CAT == 1
set AHST = AHSTall*0.87+2.76+AHSTtol
elseif CAT == 2
set AHST = AHSTall*0.91-0.48+AHSTtol
endif
elseif PMOT > AHSTaul
if CAT == 1
set AHST = AHSTaul*0.87+2.76+AHSTtol
elseif CAT == 2
set AHST = AHSTaul*0.91-0.48+AHSTtol
endif
endif
"""),
    (5, 3): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
if CAT == 1
set ACST = PMOT*0.77+9.34+ACSTtol
elseif CAT == 2
set ACST = PMOT*0.73+12.72+ACSTtol
endif
elseif PMOT < ACSTall
if CAT == 1
set ACST = ACSTall*0.77+9.34+ACSTtol
elseif CAT == 2
set ACST = ACSTall*0.73+12.72+ACSTtol
endif
elseif PMOT > ACSTaul
if CAT == 1
set ACST = ACSTaul*0.77+9.34+ACSTtol
elseif CAT == 2
set ACST = ACSTaul*0.73+12.72+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
if CAT == 1
set AHST = PMOT*0.87-0.31+AHSTtol
elseif CAT == 2
set AHST = PMOT*0.91-3.69+AHSTtol
endif
elseif PMOT < AHSTall
if CAT == 1
set AHST = AHSTall*0.87-0.31+AHSTtol
elseif CAT == 2
set AHST = AHSTall*0.91-3.69+AHSTtol
endif
elseif PMOT > AHSTaul
if CAT == 1
set AHST = AHSTaul*0.87-0.31+AHSTtol
elseif CAT == 2
set AHST = AHSTaul*0.91-3.69+AHSTtol
endif
endif
"""),
    (6, 2): _lines("""
if CAT==80
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.30+25.9+ACSTtol
elseif PMOT < ACSTall
set ACST = 25+ACSTtol
elseif PMOT > ACSTaul
set ACST = 27+ACSTtol
endif
elseif CAT==90
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.30+23.6+ACSTtol
elseif PMOT < ACSTall
set ACST = 24+ACSTtol
elseif PMOT > ACSTaul
set ACST = 26+ACSTtol
endif
endif
if CAT==80
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.32+14.88+AHSTtol
elseif PMOT < AHSTall
set AHST = 19+AHSTtol
elseif PMOT > AHSTaul
set AHST = 22+AHSTtol
endif
elseif CAT==90
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.31+17.14+AHSTtol
elseif PMOT < AHSTall
set AHST = 20+AHSTtol
elseif PMOT > AHSTaul
set AHST = 23+AHSTtol
endif
endif
"""),
    (6, 3): _lines("""
if CAT == 80
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.30+25.9+ACSTtol
elseif (PMOT < ACSTall)
set ACST = ACSTall*0.30+25.9+ACSTtol
elseif (PMOT > ACSTaul)
set ACST = ACSTaul*0.30+25.9+ACSTtol
endif
elseif CAT == 90
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.30+23.6+ACSTtol
elseif (PMOT < ACSTall)
set ACST = ACSTall*0.30+23.6+ACSTtol
elseif (PMOT > ACSTaul)
set ACST = ACSTaul*0.30+23.6+ACSTtol
endif
endif
if CAT == 80
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.32+14.88+AHSTtol
elseif (PMOT < AHSTall)
set AHST = AHSTall*0.32+14.88+AHSTtol
elseif (PMOT > AHSTaul)
set AHST = AHSTaul*0.32+14.88+AHSTtol
endif
elseif CAT == 90
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.31+17.14+AHSTtol
elseif (PMOT < AHSTall)
set AHST = AHSTall*0.31+17.14+AHSTtol
elseif (PMOT > AHSTaul)
set AHST = AHSTaul*0.31+17.14+AHSTtol
endif
endif
"""),
    (7, 0): _lines("""
if CAT==80
set ACST = PMOT*0.078+23.25+2.72+ACSTtol
elseif CAT==85
set ACST = PMOT*0.078+23.25+2.11+ACSTtol
elseif CAT==90
set ACST = PMOT*0.078+23.25+1.5+ACSTtol
endif
if CAT==80
set AHST = PMOT*0.078+23.25-2.72+AHSTtol
elseif CAT==85
set AHST = PMOT*0.078+23.25-2.11+AHSTtol
elseif CAT==90
set AHST = PMOT*0.078+23.25-1.5+AHSTtol
endif
"""),
    (7, 1): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.54+12.83+ACSToffset+ACSTtol
else
if CAT==80
set ACST = PMOT*0.078+23.25+2.72+ACSTtol
elseif CAT==85
set ACST = PMOT*0.078+23.25+2.11+ACSTtol
elseif CAT==90
set ACST = PMOT*0.078+23.25+1.5+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.54+12.83+AHSToffset+AHSTtol
else
if CAT==80
set AHST = PMOT*0.078+23.25-2.72+AHSTtol
elseif CAT==85
set AHST = PMOT*0.078+23.25-2.11+AHSTtol
elseif CAT==90
set AHST = PMOT*0.078+23.25-1.5+AHSTtol
endif
endif
"""),
    (7, 2): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.54+12.83+ACSToffset+ACSTtol
elseif CAT==80
if PMOT < ACSTall
set ACST = 25+ACSTtol
elseif PMOT > ACSTaul
set ACST = 27+ACSTtol
endif
elseif CAT==85
if PMOT < ACSTall
set ACST = 25.72+ACSTtol
elseif PMOT > ACSTaul
set ACST = 27.89+ACSTtol
endif
elseif CAT==90
if PMOT < ACSTall
set ACST = 24+ACSTtol
elseif PMOT > ACSTaul
set ACST = 26+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.54+12.83+AHSToffset+AHSTtol
elseif CAT==80
if PMOT < AHSTall
set AHST = 19+AHSTtol
elseif PMOT > AHSTaul
set AHST = 22+AHSTtol
endif
elseif CAT==85
if PMOT < AHSTall
set AHST = 20.77+AHSTtol
elseif PMOT > AHSTaul
set AHST = 24.26+AHSTtol
endif
elseif CAT==90
if PMOT < AHSTall
set AHST = 20+AHSTtol
elseif PMOT > AHSTaul
set AHST = 23+AHSTtol
endif
endif
"""),
    (7, 3): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.54+12.83+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.54+12.83+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.54+12.83+ACSToffset+ACSTtol
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.54+12.83+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.54+12.83+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.54+12.83+AHSToffset+AHSTtol
endif
"""),
    (8, 0): _lines("""
if CAT==80
set ACST = PMOT*0.078+23.25+2.72+ACSTtol
elseif CAT==85
set ACST = PMOT*0.078+23.25+2.11+ACSTtol
elseif CAT==90
set ACST = PMOT*0.078+23.25+1.5+ACSTtol
endif
if CAT==80
set AHST = PMOT*0.078+23.25-2.72+AHSTtol
elseif CAT==85
set AHST = PMOT*0.078+23.25-2.11+AHSTtol
elseif CAT==90
set AHST = PMOT*0.078+23.25-1.5+AHSTtol
endif
"""),
    (8, 1): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.28+17.87+ACSToffset+ACSTtol
else
if CAT==80
set ACST = PMOT*0.078+23.25+2.72+ACSTtol
elseif CAT==85
set ACST = PMOT*0.078+23.25+2.11+ACSTtol
elseif CAT==90
set ACST = PMOT*0.078+23.25+1.5+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.28+17.87+AHSToffset+AHSTtol
else
if CAT==80
set AHST = PMOT*0.078+23.25-2.72+AHSTtol
elseif CAT==85
set AHST = PMOT*0.078+23.25-2.11+AHSTtol
elseif CAT==90
set AHST = PMOT*0.078+23.25-1.5+AHSTtol
endif
endif
"""),
    (8, 2): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.28+17.87+ACSToffset+ACSTtol
elseif CAT==80
if PMOT < ACSTall
set ACST = 25+ACSTtol
elseif PMOT > ACSTaul
set ACST = 27+ACSTtol
endif
elseif CAT==85
if PMOT < ACSTall
set ACST = 25.72+ACSTtol
elseif PMOT > ACSTaul
set ACST = 27.89+ACSTtol
endif
elseif CAT==90
if PMOT < ACSTall
set ACST = 24+ACSTtol
elseif PMOT > ACSTaul
set ACST = 26+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.28+17.87+AHSToffset+AHSTtol
elseif CAT==80
if PMOT < AHSTall
set AHST = 19+AHSTtol
elseif PMOT > AHSTaul
set AHST = 22+AHSTtol
endif
elseif CAT==85
if PMOT < AHSTall
set AHST = 20.77+AHSTtol
elseif PMOT > AHSTaul
set AHST = 24.26+AHSTtol
endif
elseif CAT==90
if PMOT < AHSTall
set AHST = 20+AHSTtol
elseif PMOT > AHSTaul
set AHST = 23+AHSTtol
endif
endif
"""),
    (8, 3): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.28+17.87+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.28+17.87+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.28+17.87+ACSToffset+ACSTtol
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.28+17.87+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.28+17.87+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.28+17.87+AHSToffset+AHSTtol
endif
"""),
    (9, 0): _lines("""
if CAT==80
set ACST = PMOT*0.078+23.25+2.72+ACSTtol
elseif CAT==85
set ACST = PMOT*0.078+23.25+2.11+ACSTtol
elseif CAT==90
set ACST = PMOT*0.078+23.25+1.5+ACSTtol
endif
if CAT==80
set AHST = PMOT*0.078+23.25-2.72+AHSTtol
elseif CAT==85
set AHST = PMOT*0.078+23.25-2.11+AHSTtol
elseif CAT==90
set AHST = PMOT*0.078+23.25-1.5+AHSTtol
endif
"""),
    (9, 1): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.39+18.42+ACSToffset+ACSTtol
else
if CAT==80
set ACST = PMOT*0.078+23.25+2.72+ACSTtol
elseif CAT==90
set ACST = PMOT*0.078+23.25+1.5+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.39+18.42+AHSToffset+AHSTtol
else
if CAT==80
set AHST = PMOT*0.078+23.25+2.72+AHSTtol
elseif CAT==90
set AHST = PMOT*0.078+23.25+1.5+AHSTtol
endif
endif
"""),
    (9, 2): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.39+18.42+ACSToffset+ACSTtol
elseif CAT==80
if PMOT < ACSTall
set ACST = 25+ACSTtol
elseif PMOT > ACSTaul
set ACST = 27+ACSTtol
endif
elseif CAT==90
if PMOT < ACSTall
set ACST = 24+ACSTtol
elseif PMOT > ACSTaul
set ACST = 26+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.39+18.42+AHSToffset+AHSTtol
elseif CAT==80
if PMOT < AHSTall
set AHST = 19+AHSTtol
elseif PMOT > AHSTaul
set AHST = 22+AHSTtol
endif
elseif CAT==90
if PMOT < AHSTall
set AHST = 20+AHSTtol
elseif PMOT > AHSTaul
set AHST = 23+AHSTtol
endif
endif
"""),
    (9, 3): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.39+18.42+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.39+18.42+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.39+18.42+ACSToffset+ACSTtol
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.39+18.42+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.39+18.42+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.39+18.42+AHSToffset+AHSTtol
endif
"""),
    (10, 0): _lines("""
if CAT==80
set ACST = PMOT*0.078+23.25+2.72+ACSTtol
elseif CAT==85
set ACST = PMOT*0.078+23.25+2.11+ACSTtol
elseif CAT==90
set ACST = PMOT*0.078+23.25+1.5+ACSTtol
endif
if CAT==80
set AHST = PMOT*0.078+23.25-2.72+AHSTtol
elseif CAT==85
set AHST = PMOT*0.078+23.25-2.11+AHSTtol
elseif CAT==90
set AHST = PMOT*0.078+23.25-1.5+AHSTtol
endif
"""),
    (10, 1): _lines("""
if (RMOT >= ACSTall) && (RMOT <= ACSTaul)
set ACST = RMOT*0.42+17.6+ACSToffset+ACSTtol
else
if CAT==80
set ACST = RMOT*0.078+23.25+2.72+ACSTtol
elseif CAT==90
set ACST = RMOT*0.078+23.25+1.5+ACSTtol
endif
endif
if (RMOT >= AHSTall) && (RMOT <= AHSTaul)
set AHST = RMOT*0.42+17.6+AHSToffset+AHSTtol
else
if CAT==80
set AHST = RMOT*0.078+23.25-2.72+AHSTtol
elseif CAT==90
set AHST = RMOT*0.078+23.25-1.5+AHSTtol
endif
endif
"""),
    (10, 2): _lines("""
if (RMOT >= ACSTall) && (RMOT <= ACSTaul)
set ACST = RMOT*0.42+17.6+ACSToffset+ACSTtol
elseif CAT==80
if RMOT < ACSTall
set ACST = 25+ACSTtol
elseif RMOT > ACSTaul
set ACST = 27+ACSTtol
endif
elseif CAT==90
if RMOT < ACSTall
set ACST = 24+ACSTtol
elseif RMOT > ACSTaul
set ACST = 26+ACSTtol
endif
endif
if (RMOT >= AHSTall) && (RMOT <= AHSTaul)
set AHST = RMOT*0.42+17.6+AHSToffset+AHSTtol
elseif CAT==80
if RMOT < AHSTall
set AHST = 19+AHSTtol
elseif RMOT > AHSTaul
set AHST = 22+AHSTtol
endif
elseif CAT==90
if RMOT < AHSTall
set AHST = 20+AHSTtol
elseif RMOT > AHSTaul
set AHST = 23+AHSTtol
endif
endif
"""),
    (10, 3): _lines("""
if (RMOT >= ACSTall) && (RMOT <= ACSTaul)
set ACST = RMOT*0.42+17.6+ACSToffset+ACSTtol
elseif RMOT < ACSTall
set ACST = ACSTall*0.42+17.6+ACSToffset+ACSTtol
elseif RMOT > ACSTaul
set ACST = ACSTaul*0.42+17.6+ACSToffset+ACSTtol
endif
if (RMOT >= AHSTall) && (RMOT <= AHSTaul)
set AHST = RMOT*0.42+17.6+AHSToffset+AHSTtol
elseif RMOT < AHSTall
set AHST = AHSTall*0.42+17.6+AHSToffset+AHSTtol
elseif RMOT > AHSTaul
set AHST = AHSTaul*0.42+17.6+AHSToffset+AHSTtol
endif
"""),
    (11, 1): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.75+5.37+ACSToffset+ACSTtol
else
if CAT==80
set ACST = PMOT*0.078+23.25+2.72+ACSTtol
elseif CAT==90
set ACST = PMOT*0.078+23.25+1.5+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.75+5.37+AHSToffset+AHSTtol
else
if CAT==80
set AHST = PMOT*0.078+23.25-2.72+AHSTtol
elseif CAT==90
set AHST = PMOT*0.078+23.25-1.5+AHSTtol
endif
endif
"""),
    (11, 2): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.75+5.37+ACSToffset+ACSTtol
elseif CAT==80
if PMOT < ACSTall
set ACST = 25+ACSTtol
elseif PMOT > ACSTaul
set ACST = 27+ACSTtol
endif
elseif CAT==90
if PMOT < ACSTall
set ACST = 24+ACSTtol
elseif PMOT > ACSTaul
set ACST = 26+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.75+5.37+AHSToffset+AHSTtol
elseif CAT==80
if PMOT < AHSTall
set AHST = 19+AHSTtol
elseif PMOT > AHSTaul
set AHST = 22+AHSTtol
endif
elseif CAT==90
if PMOT < AHSTall
set AHST = 20+AHSTtol
elseif PMOT > AHSTaul
set AHST = 23+AHSTtol
endif
endif
"""),
    (11, 3): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.75+5.37+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.75+5.37+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.75+5.37+ACSToffset+ACSTtol
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.75+5.37+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.75+5.37+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.75+5.37+AHSToffset+AHSTtol
endif
"""),
    (12, 0): _lines("""
if (CAT==80)
set ACST = 27+ACSTtol
elseif (CAT==90)
set ACST = 25.5+ACSTtol
endif
if (CAT==80)
set AHST = 20+AHSTtol
elseif (CAT==90)
set AHST = 21.5+AHSTtol
endif
"""),
    (12, 1): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.25+19.7+ACSToffset+ACSTtol
elseif CAT==80
if PMOT < ACSTall
set ACST = 27+ACSTtol
elseif PMOT > ACSTaul
set ACST = 27+ACSTtol
endif
elseif CAT==90
if PMOT < ACSTall
set ACST = 25.5+ACSTtol
elseif PMOT > ACSTaul
set ACST = 25.5+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.25+19.7+AHSToffset+AHSTtol
elseif CAT==80
if PMOT < AHSTall
set AHST = 20+AHSTtol
elseif PMOT > AHSTaul
set AHST = 20+AHSTtol
endif
elseif CAT==90
if PMOT < AHSTall
set AHST = 21.5+AHSTtol
elseif PMOT > AHSTaul
set AHST = 21.5+AHSTtol
endif
endif
"""),
    (12, 2): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.25+19.7+ACSToffset+ACSTtol
elseif CAT==80
if PMOT < ACSTall
set ACST = 25+ACSTtol
elseif PMOT > ACSTaul
set ACST = 27+ACSTtol
endif
elseif CAT==90
if PMOT < ACSTall
set ACST = 24+ACSTtol
elseif PMOT > ACSTaul
set ACST = 26+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.25+19.7+AHSToffset+AHSTtol
elseif CAT==80
if PMOT < AHSTall
set AHST = 19+AHSTtol
elseif PMOT > AHSTaul
set AHST = 22+AHSTtol
endif
elseif CAT==90
if PMOT < AHSTall
set AHST = 20+AHSTtol
elseif PMOT > AHSTaul
set AHST = 23+AHSTtol
endif
endif
"""),
    (12, 3): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.25+19.7+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.25+19.7+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.25+19.7+ACSToffset+ACSTtol
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.25+19.7+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.25+19.7+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.25+19.7+AHSToffset+AHSTtol
endif
"""),
    (13, None): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 23+ACSTtol
endif
endif
"""),
    (13, 0.1): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 27+ACSTtol
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 26+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
if (CAT==80)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
elseif (CAT==90)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
"""),
    (13, 0.2): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 26+ACSTtol
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 25+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
if (CAT==80)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
elseif (CAT==90)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
"""),
    (13, 0.3): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 25+ACSTtol
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 24+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
if (CAT==80)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
elseif (CAT==90)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
"""),
    (13, 0.4): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 24+ACSTtol
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 23+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
if (CAT==80)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
elseif (CAT==90)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
"""),
    (13, 0.5): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 23+ACSTtol
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 22+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
if (CAT==80)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
elseif (CAT==90)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
"""),
    (13, 1.1): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 23+ACSTtol
endif
endif
if CAT == 80
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 27+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 23+ACSTtol
else
set ACST = 24+ACSTtol
endif
endif
elseif CAT==90
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 23+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 22+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
endif
if CAT == 80
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
endif
elseif CAT==90
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
endif
"""),
    (13, 1.2): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 23+ACSTtol
endif
endif
if CAT == 80
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 27+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 23+ACSTtol
else
set ACST = 24+ACSTtol
endif
endif
elseif CAT==90
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 23+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 22+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
endif
if CAT == 80
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
endif
elseif CAT==90
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
endif
"""),
    (13, 1.3): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 23+ACSTtol
endif
endif
if CAT == 80
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 27+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 23+ACSTtol
else
set ACST = 24+ACSTtol
endif
endif
elseif CAT==90
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 23+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 22+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
endif
if CAT == 80
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
endif
elseif CAT==90
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
endif
"""),
    (13, 1.4): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 23+ACSTtol
endif
endif
if CAT == 80
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 27+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 23+ACSTtol
else
set ACST = 24+ACSTtol
endif
endif
elseif CAT==90
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 23+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 22+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
endif
if CAT == 80
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
endif
elseif CAT==90
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
endif
"""),
    (13, 1.5): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 23+ACSTtol
endif
endif
if CAT == 80
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 27+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 23+ACSTtol
else
set ACST = 24+ACSTtol
endif
endif
elseif CAT==90
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 23+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 22+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
endif
if CAT == 80
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
endif
elseif CAT==90
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
endif
"""),
    (13, 2): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 23+ACSTtol
endif
endif
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol
elseif CAT==80
if PMOT < ACSTall
set ACST = 25+ACSTtol
elseif PMOT > ACSTaul
set ACST = 27+ACSTtol
endif
elseif CAT==90
if PMOT < ACSTall
set ACST = 24+ACSTtol
elseif PMOT > ACSTaul
set ACST = 26+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol
elseif CAT==80
if PMOT < AHSTall
set AHST = 19+AHSTtol
elseif PMOT > AHSTaul
set AHST = 22+AHSTtol
endif
elseif CAT==90
if PMOT < AHSTall
set AHST = 20+AHSTtol
elseif PMOT > AHSTaul
set AHST = 23+AHSTtol
endif
endif
"""),
    (13, 3): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 23+ACSTtol
endif
endif
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.26+15.9+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.26+15.9+ACSToffset+ACSTtol
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.26+15.9+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.26+15.9+AHSToffset+AHSTtol
endif
"""),
    (14, None): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 23+ACSTtol
endif
endif
"""),
    (14, 0.1): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 27+ACSTtol
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 26+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
if (CAT==80)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
elseif (CAT==90)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
"""),
    (14, 0.2): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 26+ACSTtol
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 25+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
if (CAT==80)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
elseif (CAT==90)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
"""),
    (14, 0.3): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 25+ACSTtol
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 24+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
if (CAT==80)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
elseif (CAT==90)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
"""),
    (14, 0.4): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 24+ACSTtol
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 23+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
if (CAT==80)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
elseif (CAT==90)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
"""),
    (14, 0.5): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 23+ACSTtol
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
set ACST = 22+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
if (CAT==80)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
elseif (CAT==90)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
"""),
    (14, 1.1): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 23+ACSTtol
endif
endif
if CAT == 80
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 27+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 23+ACSTtol
else
set ACST = 24+ACSTtol
endif
endif
elseif CAT==90
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 23+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 22+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
endif
if CAT == 80
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
endif
elseif CAT==90
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
endif
"""),
    (14, 1.2): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 23+ACSTtol
endif
endif
if CAT == 80
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 27+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 23+ACSTtol
else
set ACST = 24+ACSTtol
endif
endif
elseif CAT==90
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 23+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 22+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
endif
if CAT == 80
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
endif
elseif CAT==90
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
endif
"""),
    (14, 1.3): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 23+ACSTtol
endif
endif
if CAT == 80
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 27+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 23+ACSTtol
else
set ACST = 24+ACSTtol
endif
endif
elseif CAT==90
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 23+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 22+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
endif
if CAT == 80
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
endif
elseif CAT==90
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
endif
"""),
    (14, 1.4): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 23+ACSTtol
endif
endif
if CAT == 80
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 27+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 23+ACSTtol
else
set ACST = 24+ACSTtol
endif
endif
elseif CAT==90
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 23+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 22+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
endif
if CAT == 80
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
endif
elseif CAT==90
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
endif
"""),
    (14, 1.5): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 23+ACSTtol
endif
endif
if CAT == 80
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 27+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 23+ACSTtol
else
set ACST = 24+ACSTtol
endif
endif
elseif CAT==90
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol
elseif (PMOT < ACSTall) || (PMOT > ACSTaul)
if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)
set ACST = 26+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)
set ACST = 25+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)
set ACST = 24+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)
set ACST = 23+ACSTtol
elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)
set ACST = 22+ACSTtol
else
set ACST = 23+ACSTtol
endif
endif
endif
if CAT == 80
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 20+AHSTtol
else
set AHST = 18+AHSTtol
endif
endif
elseif CAT==90
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol
elseif (PMOT < AHSTall) || (PMOT > AHSTaul)
if (CurrentTime >6) && (CurrentTime < 12)
set AHST = 21+AHSTtol
else
set AHST = 19+AHSTtol
endif
endif
endif
"""),
    (14, 2): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 23+ACSTtol
endif
endif
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol
elseif CAT==80
if PMOT < ACSTall
set ACST = 25+ACSTtol
elseif PMOT > ACSTaul
set ACST = 27+ACSTtol
endif
elseif CAT==90
if PMOT < ACSTall
set ACST = 24+ACSTtol
elseif PMOT > ACSTaul
set ACST = 26+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol
elseif CAT==80
if PMOT < AHSTall
set AHST = 19+AHSTtol
elseif PMOT > AHSTaul
set AHST = 22+AHSTtol
endif
elseif CAT==90
if PMOT < AHSTall
set AHST = 20+AHSTtol
elseif PMOT > AHSTaul
set AHST = 23+AHSTtol
endif
endif
"""),
    (14, 3): _lines("""
if (CAT==80)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 24+ACSTtol
endif
elseif (CAT==90)
if (CurrentTime > 6) && (CurrentTime < 23)
else
set ACST = 23+ACSTtol
endif
endif
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.26+16.75+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.26+16.75+ACSToffset+ACSTtol
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.26+16.75+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.26+16.75+AHSToffset+AHSTtol
endif
"""),
    (15, 0): _lines("""
set ACST = 25+ACSTtol
set AHST = 20+AHSTtol
"""),
    (15, 1): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.56+12.74+ACSToffset+ACSTtol
elseif CAT==80
if PMOT < ACSTall
set ACST = 23.5+ACSTtol
elseif PMOT > ACSTaul
set ACST = 25.5+ACSTtol
endif
elseif CAT==90
if PMOT < ACSTall
set ACST = 23+ACSTtol
elseif PMOT > ACSTaul
set ACST = 25+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.56+12.74+AHSToffset+AHSTtol
elseif CAT==80
if PMOT < AHSTall
set AHST = 21+AHSTtol
elseif PMOT > AHSTaul
set AHST = 22.5+AHSTtol
endif
elseif CAT==90
if PMOT < AHSTall
set AHST = 23+AHSTtol
elseif PMOT > AHSTaul
set AHST = 23+AHSTtol
endif
endif
"""),
    (15, 2): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.56+12.74+ACSToffset+ACSTtol
elseif CAT==80
if PMOT < ACSTall
set ACST = 25+ACSTtol
elseif PMOT > ACSTaul
set ACST = 27+ACSTtol
endif
elseif CAT==90
if PMOT < ACSTall
set ACST = 24+ACSTtol
elseif PMOT > ACSTaul
set ACST = 26+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.56+12.74+AHSToffset+AHSTtol
elseif CAT==80
if PMOT < AHSTall
set AHST = 19+AHSTtol
elseif PMOT > AHSTaul
set AHST = 22+AHSTtol
endif
elseif CAT==90
if PMOT < AHSTall
set AHST = 20+AHSTtol
elseif PMOT > AHSTaul
set AHST = 23+AHSTtol
endif
endif
"""),
    (15, 3): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.56+12.74+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.56+12.74+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.56+12.74+ACSToffset+ACSTtol
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.56+12.74+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.56+12.74+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.56+12.74+AHSToffset+AHSTtol
endif
"""),
    (16, 0): _lines("""
set ACST = 25+ACSTtol
set AHST = 20+AHSTtol
"""),
    (16, 1): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.09+22.32+ACSToffset+ACSTtol
elseif CAT==80
if PMOT < ACSTall
set ACST = 23.5+ACSTtol
elseif PMOT > ACSTaul
set ACST = 25.5+ACSTtol
endif
elseif CAT==90
if PMOT < ACSTall
set ACST = 23+ACSTtol
elseif PMOT > ACSTaul
set ACST = 25+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.09+22.32+AHSToffset+AHSTtol
elseif CAT==80
if PMOT < AHSTall
set AHST = 21+AHSTtol
elseif PMOT > AHSTaul
set AHST = 22.5+AHSTtol
endif
elseif CAT==90
if PMOT < AHSTall
set AHST = 23+AHSTtol
elseif PMOT > AHSTaul
set AHST = 23+AHSTtol
endif
endif
"""),
    (16, 2): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.09+22.32+ACSToffset+ACSTtol
elseif CAT==80
if PMOT < ACSTall
set ACST = 25+ACSTtol
elseif PMOT > ACSTaul
set ACST = 27+ACSTtol
endif
elseif CAT==90
if PMOT < ACSTall
set ACST = 24+ACSTtol
elseif PMOT > ACSTaul
set ACST = 26+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.09+22.32+AHSToffset+AHSTtol
elseif CAT==80
if PMOT < AHSTall
set AHST = 19+AHSTtol
elseif PMOT > AHSTaul
set AHST = 22+AHSTtol
endif
elseif CAT==90
if PMOT < AHSTall
set AHST = 20+AHSTtol
elseif PMOT > AHSTaul
set AHST = 23+AHSTtol
endif
endif
"""),
    (16, 3): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.09+22.32+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.09+22.32+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.09+22.32+ACSToffset+ACSTtol
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.09+22.32+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.09+22.32+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.09+22.32+AHSToffset+AHSTtol
endif
"""),
    (17, 0): _lines("""
set ACST = 25+ACSTtol
set AHST = 20+AHSTtol
"""),
    (17, 1): _lines("""
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.48+13.9+ACSToffset+ACSTtol
else
set ACST = 25+ACSTtol
endif
else
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.59+9.6+ACSToffset+ACSTtol
else
set ACST = 25+ACSTtol
endif
endif
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.48+13.9+AHSToffset+AHSTtol
else
set AHST = 20+AHSTtol
endif
else
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.59+9.6+AHSToffset+AHSTtol
else
set AHST = 20+AHSTtol
endif
endif
"""),
    (17, 2): _lines("""
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.48+13.9+ACSToffset+ACSTtol
elseif PMOT < ACSTall
if CAT == 90
set ACST = 24+ACSTtol
elseif CAT == 80
set ACST = 25+ACSTtol
endif
elseif PMOT > ACSTaul
if CAT == 90
set ACST = 26+ACSTtol
elseif CAT == 80
set ACST = 27+ACSTtol
endif
endif
else
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.59+9.6+ACSToffset+ACSTtol
elseif PMOT < ACSTall
if CAT == 90
set ACST = 24+ACSTtol
elseif CAT == 80
set ACST = 25+ACSTtol
endif
elseif PMOT > ACSTaul
if CAT == 90
set ACST = 26+ACSTtol
elseif CAT == 80
set ACST = 27+ACSTtol
endif
endif
endif
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.48+13.9+AHSToffset+AHSTtol
elseif PMOT < AHSTall
if CAT == 90
set AHST = 20+AHSTtol
elseif CAT == 80
set AHST = 19+AHSTtol
endif
elseif PMOT > AHSTaul
if CAT == 90
set AHST = 23+AHSTtol
elseif CAT == 80
set AHST = 22+AHSTtol
endif
endif
else
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.59+9.6+AHSToffset+AHSTtol
elseif PMOT < AHSTall
if CAT == 90
set AHST = 20+AHSTtol
elseif CAT == 80
set AHST = 19+AHSTtol
endif
elseif PMOT > AHSTaul
if CAT == 90
set AHST = 23+AHSTtol
elseif CAT == 80
set AHST = 22+AHSTtol
endif
endif
endif
"""),
    (17, 3): _lines("""
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.48+13.9+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.48+13.9+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.48+13.9+ACSToffset+ACSTtol
endif
else
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.59+9.6+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.59+9.6+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.59+9.6+ACSToffset+ACSTtol
endif
endif
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.48+13.9+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.48+13.9+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.48+13.9+AHSToffset+AHSTtol
endif
else
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.59+9.6+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.59+9.6+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.59+9.6+AHSToffset+AHSTtol
endif
endif
"""),
    (18, 0): _lines("""
set ACST = 25+ACSTtol
set AHST = 20+AHSTtol
"""),
    (18, 1): _lines("""
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.84+5.3+ACSToffset+ACSTtol
else
set ACST = 25+ACSTtol
endif
else
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.96-3.6+ACSToffset+ACSTtol
else
set ACST = 25+ACSTtol
endif
endif
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.84+5.3+AHSToffset+AHSTtol
else
set AHST = 20+AHSTtol
endif
else
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.96-3.6+AHSToffset+AHSTtol
else
set AHST = 20+AHSTtol
endif
endif
"""),
    (18, 2): _lines("""
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.84+5.3+ACSToffset+ACSTtol
elseif PMOT < ACSTall
if CAT == 90
set ACST = 24+ACSTtol
elseif CAT == 80
set ACST = 25+ACSTtol
endif
elseif PMOT > ACSTaul
if CAT == 90
set ACST = 26+ACSTtol
elseif CAT == 80
set ACST = 27+ACSTtol
endif
endif
else
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.96-3.6+ACSToffset+ACSTtol
elseif PMOT < ACSTall
if CAT == 90
set ACST = 24+ACSTtol
elseif CAT == 80
set ACST = 25+ACSTtol
endif
elseif PMOT > ACSTaul
if CAT == 90
set ACST = 26+ACSTtol
elseif CAT == 80
set ACST = 27+ACSTtol
endif
endif
endif
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.84+5.3+AHSToffset+AHSTtol
elseif PMOT < AHSTall
if CAT == 90
set AHST = 20+AHSTtol
elseif CAT == 80
set AHST = 19+AHSTtol
endif
elseif PMOT > AHSTaul
if CAT == 90
set AHST = 23+AHSTtol
elseif CAT == 80
set AHST = 22+AHSTtol
endif
endif
else
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.96-3.6+AHSToffset+AHSTtol
elseif PMOT < AHSTall
if CAT == 90
set AHST = 20+AHSTtol
elseif CAT == 80
set AHST = 19+AHSTtol
endif
elseif PMOT > AHSTaul
if CAT == 90
set AHST = 23+AHSTtol
elseif CAT == 80
set AHST = 22+AHSTtol
endif
endif
endif
"""),
    (18, 3): _lines("""
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.84+5.3+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.84+5.3+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.84+5.3+ACSToffset+ACSTtol
endif
else
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.96-3.6+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.96-3.6+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.96-3.6+ACSToffset+ACSTtol
endif
endif
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.84+5.3+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.84+5.3+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.84+5.3+AHSToffset+AHSTtol
endif
else
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.96-3.6+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.96-3.6+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.96-3.6+AHSToffset+AHSTtol
endif
endif
"""),
    (19, 0): _lines("""
set ACST = 25+ACSTtol
set AHST = 20+AHSTtol
"""),
    (19, 1): _lines("""
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.27+17.9+ACSToffset+ACSTtol
else
set ACST = 25+ACSTtol
endif
else
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.53+10.3+ACSToffset+ACSTtol
else
set ACST = 25+ACSTtol
endif
endif
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.27+17.9+AHSToffset+AHSTtol
else
set AHST = 20+AHSTtol
endif
else
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.53+10.3+AHSToffset+AHSTtol
else
set AHST = 20+AHSTtol
endif
endif
"""),
    (19, 2): _lines("""
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.27+17.9+ACSToffset+ACSTtol
elseif PMOT < ACSTall
if CAT == 90
set ACST = 24+ACSTtol
elseif CAT == 80
set ACST = 25+ACSTtol
endif
elseif PMOT > ACSTaul
if CAT == 90
set ACST = 26+ACSTtol
elseif CAT == 80
set ACST = 27+ACSTtol
endif
endif
else
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.53+10.3+ACSToffset+ACSTtol
elseif PMOT < ACSTall
if CAT == 90
set ACST = 24+ACSTtol
elseif CAT == 80
set ACST = 25+ACSTtol
endif
elseif PMOT > ACSTaul
if CAT == 90
set ACST = 26+ACSTtol
elseif CAT == 80
set ACST = 27+ACSTtol
endif
endif
endif
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.27+17.9+AHSToffset+AHSTtol
elseif PMOT < AHSTall
if CAT == 90
set AHST = 20+AHSTtol
elseif CAT == 80
set AHST = 19+AHSTtol
endif
elseif PMOT > AHSTaul
if CAT == 90
set AHST = 23+AHSTtol
elseif CAT == 80
set AHST = 22+AHSTtol
endif
endif
else
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.53+10.3+AHSToffset+AHSTtol
elseif PMOT < AHSTall
if CAT == 90
set AHST = 20+AHSTtol
elseif CAT == 80
set AHST = 19+AHSTtol
endif
elseif PMOT > AHSTaul
if CAT == 90
set AHST = 23+AHSTtol
elseif CAT == 80
set AHST = 22+AHSTtol
endif
endif
endif
"""),
    (19, 3): _lines("""
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.27+17.9+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.27+17.9+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.27+17.9+ACSToffset+ACSTtol
endif
else
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.53+10.3+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.53+10.3+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.53+10.3+ACSToffset+ACSTtol
endif
endif
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.27+17.9+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.27+17.9+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.27+17.9+AHSToffset+AHSTtol
endif
else
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.53+10.3+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.53+10.3+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.53+10.3+AHSToffset+AHSTtol
endif
endif
"""),
    (20, 0): _lines("""
set ACST = 25+ACSTtol
set AHST = 20+AHSTtol
"""),
    (20, 1): _lines("""
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.38+15.7+ACSToffset+ACSTtol
else
set ACST = 25+ACSTtol
endif
else
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.47+9.07+ACSToffset+ACSTtol
else
set ACST = 25+ACSTtol
endif
endif
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.38+15.7+AHSToffset+AHSTtol
else
set AHST = 20+AHSTtol
endif
else
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.47+9.07+AHSToffset+AHSTtol
else
set AHST = 20+AHSTtol
endif
endif
"""),
    (20, 2): _lines("""
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.38+15.7+ACSToffset+ACSTtol
elseif PMOT < ACSTall
if CAT == 90
set ACST = 24+ACSTtol
elseif CAT == 80
set ACST = 25+ACSTtol
endif
elseif PMOT > ACSTaul
if CAT == 90
set ACST = 26+ACSTtol
elseif CAT == 80
set ACST = 27+ACSTtol
endif
endif
else
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.47+9.07+ACSToffset+ACSTtol
elseif PMOT < ACSTall
if CAT == 90
set ACST = 24+ACSTtol
elseif CAT == 80
set ACST = 25+ACSTtol
endif
elseif PMOT > ACSTaul
if CAT == 90
set ACST = 26+ACSTtol
elseif CAT == 80
set ACST = 27+ACSTtol
endif
endif
endif
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.38+15.7+AHSToffset+AHSTtol
elseif PMOT < AHSTall
if CAT == 90
set AHST = 20+AHSTtol
elseif CAT == 80
set AHST = 19+AHSTtol
endif
elseif PMOT > AHSTaul
if CAT == 90
set AHST = 23+AHSTtol
elseif CAT == 80
set AHST = 22+AHSTtol
endif
endif
else
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.47+9.07+AHSToffset+AHSTtol
elseif PMOT < AHSTall
if CAT == 90
set AHST = 20+AHSTtol
elseif CAT == 80
set AHST = 19+AHSTtol
endif
elseif PMOT > AHSTaul
if CAT == 90
set AHST = 23+AHSTtol
elseif CAT == 80
set AHST = 22+AHSTtol
endif
endif
endif
"""),
    (20, 3): _lines("""
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.38+15.7+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.38+15.7+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.38+15.7+ACSToffset+ACSTtol
endif
else
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.47+9.07+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.47+9.07+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.47+9.07+ACSToffset+ACSTtol
endif
endif
if (DayOfYear <= 121) || (DayOfYear > 295)
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.38+15.7+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.38+15.7+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.38+15.7+AHSToffset+AHSTtol
endif
else
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.47+9.07+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.47+9.07+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.47+9.07+AHSToffset+AHSTtol
endif
endif
"""),
    (21, 2): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.678+13.51+ACSToffset+ACSTtol
elseif CAT==80
if PMOT < ACSTall
set ACST = 25+ACSTtol
elseif PMOT > ACSTaul
set ACST = 27+ACSTtol
endif
elseif CAT==90
if PMOT < ACSTall
set ACST = 24+ACSTtol
elseif PMOT > ACSTaul
set ACST = 26+ACSTtol
endif
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.678+13.51+AHSToffset+AHSTtol
elseif CAT==80
if PMOT < AHSTall
set AHST = 19+AHSTtol
elseif PMOT > AHSTaul
set AHST = 22+AHSTtol
endif
elseif CAT==90
if PMOT < AHSTall
set AHST = 20+AHSTtol
elseif PMOT > AHSTaul
set AHST = 23+AHSTtol
endif
endif
"""),
    (21, 3): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*0.678+13.51+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*0.678+13.51+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*0.678+13.51+ACSToffset+ACSTtol
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*0.678+13.51+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*0.678+13.51+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*0.678+13.51+AHSToffset+AHSTtol
endif
"""),
    (22, None): _lines("""
if CoolingSeason == 1
if (CAT==3)
set ACST = 24.5+2.5+ACSTtol
elseif (CAT==2)
set ACST = 24.5+1.5+ACSTtol
elseif (CAT==1)
set ACST = 24.5+1+ACSTtol
endif
else
if (CAT==3)
set ACST = 22+3+ACSTtol
elseif (CAT==2)
set ACST = 22+2+ACSTtol
elseif (CAT==1)
set ACST = 22+1+ACSTtol
endif
endif
if CoolingSeason == 1
if (CAT==3)
set AHST = 24.5-2.5+AHSTtol
elseif (CAT==2)
set AHST = 24.5-1.5+AHSTtol
elseif (CAT==1)
set AHST = 24.5-1+AHSTtol
endif
else
if (CAT==3)
set AHST = 22-3+AHSTtol
elseif (CAT==2)
set AHST = 22-2+AHSTtol
elseif (CAT==1)
set AHST = 22-1+AHSTtol
endif
endif
"""),
    # JPN Aqilah 2025 (Aqilah, Rijal, Yoshida & Nicol, 2025, equation 8): 0.38·RMOT + 16.9, with the static setpoints of
    # 20 and 28 °C of comfort modes 0 and 1, a choice of the user (decision D2 of the brief of 1.2.0), and those of ISO
    # 7730 of the categories 80 and 90 in comfort mode 2, as the other comfort standards
    (23, 0): _lines("""
set ACST = 28+ACSTtol
set AHST = 20+AHSTtol
"""),
    (23, 1): _lines("""
if (RMOT >= ACSTall) && (RMOT <= ACSTaul)
set ACST = RMOT*0.38+16.9+ACSToffset+ACSTtol
elseif RMOT < ACSTall
set ACST = 28+ACSTtol
elseif RMOT > ACSTaul
set ACST = 28+ACSTtol
endif
if (RMOT >= AHSTall) && (RMOT <= AHSTaul)
set AHST = RMOT*0.38+16.9+AHSToffset+AHSTtol
elseif RMOT < AHSTall
set AHST = 20+AHSTtol
elseif RMOT > AHSTaul
set AHST = 20+AHSTtol
endif
"""),
    (23, 2): _lines("""
if (RMOT >= ACSTall) && (RMOT <= ACSTaul)
set ACST = RMOT*0.38+16.9+ACSToffset+ACSTtol
elseif CAT==80
if RMOT < ACSTall
set ACST = 25+ACSTtol
elseif RMOT > ACSTaul
set ACST = 27+ACSTtol
endif
elseif CAT==90
if RMOT < ACSTall
set ACST = 24+ACSTtol
elseif RMOT > ACSTaul
set ACST = 26+ACSTtol
endif
endif
if (RMOT >= AHSTall) && (RMOT <= AHSTaul)
set AHST = RMOT*0.38+16.9+AHSToffset+AHSTtol
elseif CAT==80
if RMOT < AHSTall
set AHST = 19+AHSTtol
elseif RMOT > AHSTaul
set AHST = 22+AHSTtol
endif
elseif CAT==90
if RMOT < AHSTall
set AHST = 20+AHSTtol
elseif RMOT > AHSTaul
set AHST = 23+AHSTtol
endif
endif
"""),
    (23, 3): _lines("""
if (RMOT >= ACSTall) && (RMOT <= ACSTaul)
set ACST = RMOT*0.38+16.9+ACSToffset+ACSTtol
elseif RMOT < ACSTall
set ACST = ACSTall*0.38+16.9+ACSToffset+ACSTtol
elseif RMOT > ACSTaul
set ACST = ACSTaul*0.38+16.9+ACSToffset+ACSTtol
endif
if (RMOT >= AHSTall) && (RMOT <= AHSTaul)
set AHST = RMOT*0.38+16.9+AHSToffset+AHSTtol
elseif RMOT < AHSTall
set AHST = AHSTall*0.38+16.9+AHSToffset+AHSTtol
elseif RMOT > AHSTaul
set AHST = AHSTaul*0.38+16.9+AHSToffset+AHSTtol
endif
"""),
    (99, 3): _lines("""
if (PMOT >= ACSTall) && (PMOT <= ACSTaul)
set ACST = PMOT*m+n+ACSToffset+ACSTtol
elseif PMOT < ACSTall
set ACST = ACSTall*m+n+ACSToffset+ACSTtol
elseif PMOT > ACSTaul
set ACST = ACSTaul*m+n+ACSToffset+ACSTtol
endif
if (PMOT >= AHSTall) && (PMOT <= AHSTaul)
set AHST = PMOT*m+n+AHSToffset+AHSTtol
elseif PMOT < AHSTall
set AHST = AHSTall*m+n+AHSToffset+AHSTtol
elseif PMOT > AHSTaul
set AHST = AHSTaul*m+n+AHSToffset+AHSTtol
endif
"""),
}

#: Rounding of the setpoints to the accuracy SetpointAcc (cooling setpoints down, heating setpoints up).
ROUNDING = _lines("""
set ACSTx2 = ACST*SetpointAcc
set AHSTx2 = AHST*SetpointAcc
set roundedACSTx2 = @Round ACSTx2
set roundedAHSTx2 = @Round AHSTx2
if roundedACSTx2 - ACSTx2 < 0
set ACSTroundedUp = 0
else
set ACSTroundedUp = 1
endif
if roundedAHSTx2 - AHSTx2 < 0
set AHSTroundedUp = 0
else
set AHSTroundedUp = 1
endif
if ACSTroundedUp == 0
set roundedACST = roundedACSTx2 / SetpointAcc
else
set roundedACST = (roundedACSTx2 - 1) / SetpointAcc
endif
if AHSTroundedUp == 0
set roundedAHST = (roundedAHSTx2 + 1) / SetpointAcc
else
set roundedAHST = roundedAHSTx2 / SetpointAcc
endif
""")
