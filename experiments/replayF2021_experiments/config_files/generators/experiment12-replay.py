from baseGenerator import *
import git
from os import listdir
from os.path import isfile, join

# EXPERIMENT SETUP FIELDS  ##################################################

outputFileNoRats = '../norats12.csv'
outputFile     = '../experiment12-replay.csv'     # relative to this folder
experiment     = 'experiments/setups/experiment_1.xml'  # relative to git root folder

# constants for all configs ################################################
mazes = [100,200]
mazeWidth   = 2.2
mazeHeight  = 3
episodesPerStartingLocation = 2000
group          = 'g1'

experiment_DF = dataFrame('experiment', experiment)
group_DF      = dataFrame('group',      group)
traces_DF     = dataFrame('traces',     [ 0 ])
replay_budget_DF = dataFrame('replay_budget', [0, 10000, 100000])
replay_memory_DF = dataFrame('replay_memory', [1])
# propagation_type_DF = dataFrame('propagation_type', ["max_connection","stochastic"])
propagation_type_DF = dataFrame('propagation_type', ["stochastic"])

dir_git_root = git.Repo('.', search_parent_directories=True).git.rev_parse("--show-toplevel")
dir_mazes = 'experiments/mazes/'
dir_mazes_replay = 'experiments/mazes/OneShotObsticles2/'
dir_unseen_paths = 'experiments/unseen_paths/'

dir_layers  = 'experiments/pc_layers/'
dir_layers_uniform = dir_layers +'OneShotMorris/'

def load_layers(folder):
    full_path = join(dir_git_root, folder)
    layers = [f for f in listdir(full_path) if isfile(join(full_path, f)) and f[-4:]=='.csv']
    return dataFrame('pc_files', [folder + f for f in layers])

layers_uniform_DF          = load_layers(dir_layers_uniform)

# mazes_basic_DF = generateMazeDF(dir_mazes, [ f'M0{m}.xml' for m in [1, 2, 3]])
mazes_basic_DF = generateMazeDF(dir_mazes_replay, [ f'M{m}.xml' for m in mazes])

init_configs = 0


# Replay experiment mazes 01,02: ###########################################
ratsPerConfig = 20
no_rats_replay_m01_02 = reduce(allXall , [experiment_DF, group_DF, mazes_basic_DF, layers_uniform_DF, traces_DF, replay_budget_DF, replay_memory_DF, propagation_type_DF])
no_rats_replay_m01_02 = createConfigColumn(no_rats_replay_m01_02, init_configs)
no_rats_replay_m01_02['numEpisodes'] = no_rats_replay_m01_02['numStartingPositions']*episodesPerStartingLocation
all_runs_m01_02 = allXall(no_rats_replay_m01_02, dataFrame('run_id', [i for i in range(ratsPerConfig)]));


no_rats    = pd.concat([no_rats_replay_m01_02],ignore_index=True)
with_rats    = pd.concat([all_runs_m01_02],ignore_index=True)


saveResult(with_rats, outputFile)
saveResult(no_rats, outputFileNoRats)




            







