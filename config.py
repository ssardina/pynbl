URL_LIVESTATS = 'https://livestats.dcd.shared.geniussports.com/data'
URL_FIBA_LIVESTATS = 'http://www.fibalivestats.com/data'

# where already processed data is saved
DATA_DIR = "data-22_23/"

# action types and subtypes that should be ignored for stats
ACT_NON_STATS = ['period', 'game', 'substitution']
ACTSSUB_NON_STATS = ['startperiod']


SHOOTS_TYPES = ["3pt", "2pt", "freethrow"]

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
F_TSP = 'tsp'   # true shooting percentage,

F_AST = "ast"
F_ASTR = "astr"
F_FGMASTP = "fgm_astp"
F_STL = 'stl'
F_STLR = 'stlr'
F_BLK = 'blk'
F_BLKR = 'blkr'

# rebounds
F_REB = 'reb'
F_OREB = 'oreb'
F_OREBC= 'odrec'
F_OREBP = 'orebp'
F_ODREB= 'odreb'

F_DREB = 'dreb'
F_DREBC = 'drebc'
F_DREBP = 'drebp'
F_TRB = 'trb'   # total rebounds
F_TRBR = 'trbr' # total rebounds rate

# turn-overs
F_TOV = 'tov'
F_TOVR = 'tovr'
F_BALLHAND = 'tov_bh'
F_BADPASS = 'tov_bp'
F_OFOUL = 'tov_ofoul'
F_3SEC = 'tov_3sec'
F_8SEC = 'tov_8sec'
F_24SEC = 'tov_24sec'

F_OPPFGABLK = 'opp_fga_blocked'

DATA_COLS = [ F_POSS, F_ORTG, F_DRTG, F_NRTG,
                #  Shooting
                F_FGA, F_FGM, F_FGP, F_PTS,
                F_PATRA, F_PATRM, F_PATRP,
                F_3PTFGA, F_3PTFGM, F_3PTFGP,
                F_2PTFGA, F_2PTFGM, F_2PTFGP,
                F_FTA, F_FTM, F_FTP, 
                F_TSP,
                # positive plays
                F_AST, F_ASTR, F_FGMASTP,
                F_STL, F_STLR,
                F_BLK, F_BLKR,
                F_TOV, F_TOVR,
                F_REB,
                F_DREB, F_DREBC, F_DREBP,
                F_OREB, F_OREBC, F_OREBP,
                F_TRB,  F_TRBR,
                # neg plays
                F_BALLHAND, F_BADPASS,
                F_OFOUL,
                F_3SEC, F_8SEC, F_24SEC,
                F_OPPFGABLK]
