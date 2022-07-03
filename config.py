URL_LIVESTATS = 'https://livestats.dcd.shared.geniussports.com/data'
URL_FIBA_LIVESTATS = 'http://www.fibalivestats.com/data'

DATA_DIR = "data/"

ACT_NON_STATS = ['period', 'game', 'substitution']
ACTSSUB_NON_STATS = ['startperiod']



######################################
# STAT FIELDS USED AND COLUMN ORDER
######################################
F_POSS = 'poss'
F_ORTG = 'ortg'
F_DRTG = 'drtg'
F_NRTG = 'nrtg'
F_FGA = 'fga'
F_FGM = 'fgm'
F_FGP = 'fgp'
F_PTS = 'pts'
F_PATR = 'patr'
F_PATRA = F_PATR + 'a'
F_PATRM = F_PATR + 'm'
F_PATRP = F_PATR + 'p'

F_3PTFG = '3pt_fg'
F_3PTFGA = F_3PTFG + 'a'
F_3PTFGM = F_3PTFG + 'm'
F_3PTFGP = F_3PTFG + 'p'
F_2PTFG = '2pt_fg'
F_2PTFGA = F_2PTFG + 'a'
F_2PTFGM = F_2PTFG + 'm'
F_2PTFGP = F_2PTFG + 'p'
F_FT = 'ft'
F_FTA = 'ft' + 'a'
F_FTM = 'ft' + 'm'
F_FTP = 'ft' + 'p'

F_AST = "ast"
F_ASTR = "ast_rate"
F_FGMASTP = "fgm_astp"
F_STL = 'stl'
F_STLR = 'stl_rate'
F_BLK = 'blk'
F_BLKR = 'blk_rate'
F_TOV = 'tovs'
F_TOVR = 'tov_rate'

F_REB = 'rebs'
F_OREB = 'oreb'
F_OREBP = 'orebp'
F_DREB = 'drebs'
F_DREBP = 'drebp'
F_TRB = 'trb'
F_TRBR = 'trbr'

F_BALLHAND = 'ballhand'
F_BADPASS = 'badpass'
F_OFOUL = 'ofoul'
F_3SEC = '3sec'
F_8SEC = '8sec'
F_24SEC = '24sec'

F_OPPFGABLK = 'opp_fga_blocked'

DATA_COLS = [ F_POSS, F_ORTG, F_DRTG, F_NRTG,
                F_FGA, F_FGM, F_FGP, F_PTS,
                F_PATRA, F_PATRM, F_PATRP,
                F_3PTFGA, F_3PTFGM, F_3PTFGP,
                F_2PTFGA, F_2PTFGM, F_2PTFGP,
                F_FTA, F_FTM, F_FTP, F_REB,
                F_AST, F_ASTR, F_FGMASTP,
                F_STL, F_STLR,
                F_BLK, F_BLKR,
                F_TOV, F_TOVR,
                F_DREB, F_DREBP,
                F_OREB, F_OREBP,
                F_TRB,  F_TRBR,
                F_BALLHAND, F_BADPASS,
                F_OFOUL,
                F_3SEC, F_8SEC, F_24SEC,
                F_OPPFGABLK]
