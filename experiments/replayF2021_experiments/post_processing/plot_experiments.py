import os, sys, git, time, re, ntpath, tracemalloc, sqlite3, pandas as pd, numpy as np
from pandas.api.types import CategoricalDtype



import matplotlib.pyplot as plt

git_root = git.Repo('.', search_parent_directories=True).git.rev_parse("--show-toplevel")
sys.path.append(git_root)
from scripts.log_processing.plotting import *
from scripts.log_processing.mazeAndPcsPlotter import *
from scripts.log_processing.data_loader import *


layers_folder = 'experiments/pc_layers/'
layer_metrics_file = os.path.join(git_root, layers_folder , 'layer_metrics.csv')

# Converts np.array to TEXT when inserting
sqlite3.register_adapter(np.ndarray, adapt_array)

# Converts TEXT to np.array when selecting
sqlite3.register_converter("array", convert_array)

def adapt_array(arr):
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    return sqlite3.Binary(out.read())

def convert_array(text):
    out = io.BytesIO(text)
    out.seek(0)
    return np.load(out)

def lastEpisode(configs, sample_rate):
    num_episodes = configs['numEpisodes'].max() / configs['numStartingPositions'].max()
    last_episode = -sample_rate % num_episodes
    return last_episode

def getDataEpisodeAndSummaries(db, configs, fields_to_add, episode, location, skip_runtimes = False, skip_summary = False):
    # GET INDICES TO BE RETRIEVED AND EXTRA DATA TO BE MERGED
    indices = [np.uint16(c[1:]) for c in configs.index]  # config numbers

    # GET SUMMARIZED RUNTIME DATA
    summaries = None if skip_summary else augment_data(load_summaries(db, indices, location)[0], configs, fields_to_add)

    # GET EPISODE DATA:
    runtimes_episode = None if skip_runtimes else augment_data(load_episode_runtimes(db, indices, location, episode), configs, fields_to_add)

    return summaries, runtimes_episode

def getReplayData(db, configs, fields_to_add, episode, location, skip_runtimes = False, skip_summary = False):
    # GET INDICES TO BE RETRIEVED AND EXTRA DATA TO BE MERGED
    indices = [np.uint16(c[1:]) for c in configs.index]  # config numbers

    # GET Replay DATA
    summaries = None if skip_summary else augment_data(load_summaries(db, indices, location)[1], configs, fields_to_add)

    return summaries

def getLearningTimes(db, configs, location, threshold, fields_to_add):
    indices = [np.uint16(c[1:]) for c in configs.index]  # config numbers
    
    runtimes_all_episodes = load_all_runtimes_smaller_than_threshold(db, indices, location, threshold)  
    
    # learning rat defined as min episode with error < threshold
    learning_times = runtimes_all_episodes.loc[runtimes_all_episodes.groupby(['config', 'location', 'rat'])['episode'].idxmin()]
    
    return augment_data(learning_times, configs, fields_to_add)

def getMazeAndPcsFolder():
    basepath = path.dirname('')
    rootpath = path.abspath(path.join(basepath, ".."))
    # maze_folder = path.abspath(path.join(basepath,"logs/experiment12-replay/mazes/"))
    # pc_folder = path.abspath(path.join(basepath,"logs/experiment12-replay/pc_layers/"))

    maze_folder = path.abspath(path.join(basepath,"experiments/replayF2021_experiments/logs/experiment12-replay/mazes/"))
    pc_folder = path.abspath(path.join(basepath,"experiments/replayF2021_experiments/logs/experiment12-replay/pc_layers/"))

    return maze_folder, pc_folder

def getLearningTimesThresholded(db, configs, location, threshold, fields_to_add):
    indices = [np.uint16(c[1:]) for c in configs.index]  # config numbers
    
    runtimes_all_episodes = load_all_runtimes_smaller_than_threshold(db, indices, location, threshold)  
    
    # learning rat defined as min episode with error < threshold
    learning_times = runtimes_all_episodes.loc[runtimes_all_episodes.groupby(['config', 'location', 'rat'])['episode'].idxmin()]
    
    return augment_data(learning_times, configs, fields_to_add)

def augment_data(data, configs, fields):
    return pd.merge(data, configs[ ['c_id'] + fields ], left_on='config', right_on='c_id', how='left')

def addCatigoricalData(data, field):
    catigorical_name = field + '_c'
    data[catigorical_name] = data[field].astype(CategoricalDtype(data[field].unique(), ordered=True))
#########################################################################################################################################################
# PLOT FUNCTIONS:
#########################################################################################################################################################


# box plots (x vs y) separating each x into multiple groups (used in locally uniform experiment to compare before vs after)
def plot_grouped_box_plot(data, x_column, y_column, fill_column, x_title, y_title, legend_title, plot_title, ylim):
    p0 = ggplot(data, aes(x_column, y_column))
    # p0 += geom_jitter(alpha=0.3, position=position_jitterdodge(dodge_width=0.75), mapping=aes(group=fill_column))
    p0 += geom_boxplot(alpha=0.7, notch=False, outlier_alpha=0)
    p0 += labs(x=x_title, y=y_title, title=plot_title, fill=legend_title)
    p0 += theme(axis_text_x=element_text(rotation=45, hjust=0.5))
    p0 += scale_fill_brewer(type="qual", palette=1)
    # p0 += coord_cartesian(ylim=ylim)              
    return p0

# boxplots (x vs y) - single group for each x value
def plot_box_plot(data, x_column, y_column, x_title, y_title, plot_title, ylim, box_colors):
    # print(data)
    p0 = ggplot(data, aes(x_column, y_column ))
    p0 += geom_jitter(alpha=0.3)
    p0 += geom_boxplot(alpha=0.7, notch=False, outlier_alpha=0, color = box_colors )
    p0 += labs(x=x_title, y=y_title, title=plot_title)
    p0 += theme(axis_text_x=element_text(rotation=45, hjust=1))
    p0 += coord_cartesian(ylim=ylim)              
    return p0

# boxplots (x vs y) - divided by facets
def plot_faceted_box_plot(data, x_column, y_column, facet_column, x_title, y_title, plot_title, lims):
    p0 = ggplot(data, aes(x_column, y_column, fill=x_column ))
    p0 += facet_grid(f'. ~ {facet_column}', scales='free')
    p0 += geom_jitter(alpha=0.3, position=position_jitterdodge(), mapping=aes(group=x_column))
    p0 += geom_boxplot(alpha=0.7, notch=False, outlier_alpha=0)
    p0 += labs(x=x_title, y=y_title, title=plot_title, fill=x_title)
    p0 += theme(axis_text_x=element_text(rotation=45, hjust=0.5))
    #     p0 += p0 + scale_fill_brewer(type="seq", palette=1, name=legend_title)
    # p0 += scale_fill_brewer(type="qual", palette=1, name=legend_title)
    p0 += coord_cartesian(ylim=lims)  + coord_fixed(ratio=0.1)
    p0 += theme(axis_text_x=element_text(rotation=90, hjust=0.5))
    return p0

def plot_time_series(data, x_column, y_column, color_column, x_title, y_title, legend_title, plot_title, xlim, ylim):
    p0 = ggplot(data, aes(x_column, y_column))
    p0 += geom_line()
    p0 += labs(x=x_title, y=y_title, color=legend_title, title=plot_title, caption='smt')
    # p0 += coord_cartesian(ylim=ylim, xlim=xlim)
    p0 += scale_color_brewer(type="qual", palette=1) 
    return p0

def plot_replay_budget_boxplot(folder_lu, db, configs, merge_fields, sample_rate, location, mazes, replay_budgets):


    for m in mazes:
        experiment_configs = configs[ configs.mazeFile.str.contains(m + '.xml')].copy()
        episode = lastEpisode(experiment_configs, sample_rate)
        summaries, runtimes_last_episode = getDataEpisodeAndSummaries(db, experiment_configs, merge_fields, episode, location)
        for rat_id in range(len(summaries.groupby(['rat']))):
            plot_data = summaries[summaries['rat']==rat_id]
            data = []
            labels = []
            for r in replay_budgets:
                plot_data1 = plot_data[plot_data['replay_budget']==r]
                data.append(plot_data1['steps'])
                labels.append('Replay' + str(r))
            # print(data)
            fig, ax = plt.subplots()
            ax.boxplot(data, showmeans=True)
            ax.set_xticklabels(labels)
            fig.suptitle(f'boxplot: {m} Rat: {rat_id}')
            save_name = folder_lu + f'boxplot-{m}-Rat{rat_id}.pdf'
            fig.savefig(save_name)
            # fig.show()

def plot_replay_budget_scatter(folder_lu_runtimes, db, configs, merge_fields, sample_rate, location, mazes, replay_budgets):


    for m in mazes:
        experiment_configs = configs[ configs.mazeFile.str.contains(m + '.xml')].copy()
        episode = lastEpisode(experiment_configs, sample_rate)
        summaries, runtimes_last_episode = getDataEpisodeAndSummaries(db, experiment_configs, merge_fields, episode, location)
        for rat_id in range(len(summaries.groupby(['rat']))):
            plot_data = summaries[summaries['rat']==rat_id]
            fig, axs = plt.subplots(1,1)
            fig.suptitle('Maze: '+ str(m) + ' Rat: ' + str(rat_id))
            axs.set_xlabel('Episodes')
            axs.set_ylabel('Steps')
            for r in replay_budgets:
                plot_data1 = plot_data[plot_data['replay_budget']==r]
                plt.plot(plot_data1['episode'], plot_data1['steps'], '.-', label='Replay_Budget: ' +str(r))
            axs.legend()
            save_name = folder_lu_runtimes + f'runtimes-{m}-Rat{rat_id}.pdf'
            fig.savefig(save_name)
            plt.close(fig)

# TODO: Plot the sums of the number of steps taken
def plot_boxplot_trial_sums():


    return None

# TODO: Plot Average replay length per trial
def plot_average_replay_length():


    return None

# TODO: plot the average connectivity of place cells (found in Replay Matrix)
def plot_cell_connectivity():


    return None

# TODO: plot a measure of spread of cell connectivity
# TODO: Find a messure of spread for cell connectivity
def plot_cell_spread():


    return None
#########################################################################################################################################################
# PLOT EXPERIMENTS:
#########################################################################################################################################################

def plot_experiment_11(figure_folder, configs, sample_rate, db):

    # toggle plots:
    plot_locally_uniform = True
    plot_non_uniform = False
    plot_density_same_maze = False
    plot_best_densities = False

    # layers of minimum coverage:
    min_layers = ['u04_40', 'u08_21', 'u12_14', 'u16_11', 'u20_09', 'u24_07', 'u28_06', 'u32_06', 'u36_06', 'u40_05', 'u44_05', 'u48_04', 'u52_04', 'u56_04']

    # ADD COLUMNS TO CONFIGS
    configs['c_id'] = configs.index.map(lambda v : int(v[1:]))
    configs['pc_files'] = configs.pc_files.map(os.path.normpath )
    configs['pcs'] = configs.pc_files.map(lambda v : ntpath.basename(v)[0:-4])
    configs['maze']= configs.mazeFile.map(lambda v : ntpath.basename(v)[0:-4])

    # GET LAYER METRICS 
    layer_metrics = pd.read_csv(layer_metrics_file)
    layer_metrics['layer'] = layer_metrics.layer.map(lambda l : os.path.normpath(layers_folder + l) ) # normalize path and prepend location


    #########################################################################################################################################################
    # LOCALLY UNIFORM EXPERIMENT:
    #########################################################################################################################################################
    if plot_locally_uniform:

        # CREATE FOLDERS FOR EXPERIMENT
        folder_lu = os.path.join(figure_folder,'locally_uniform/')
        folder_lu_runtimes = os.path.join(folder_lu, 'runtimes/')
        make_folder(folder_lu)
        make_folder(folder_lu_runtimes)

        for m in ['M1', 'M2']:
            print(f'PLOTTING LOCALLY UNIFORM: {m}')
            
            for t in [0, 0.7]:

                # GENERATE CATEGORIES FOR DATA
                categories = ['original', 'goal', 'goal and gap']
                categories = CategoricalDtype(categories[0:-1] if m == 'M0' else categories , ordered=True)

                # GET CONFIGS RELEVANT TO EXPERIMENT
                experiment_configs = configs[ configs.mazeFile.str.contains(m + '.xml') & ( configs.traces == t ) & configs.pc_files.str.contains('|'.join(['lu'] + min_layers[4:])) ].copy()
                experiment_configs['base layer'] = experiment_configs.pcs.map(lambda l : re.findall('\d+', l)[-2])
                experiment_configs['legend groups'] = experiment_configs.pcs.map(lambda l : 'original' if l[0]=='u' else 'goal' if l[2] == '0' else 'goal and gap').astype(categories)

                print(experiment_configs)

                # GET AND AUGMENT DATA
                merge_fields = ['base layer', 'legend groups']
                episode = lastEpisode(experiment_configs, sample_rate)
                location = -1
                summaries, runtimes_last_episode = getDataEpisodeAndSummaries(db, experiment_configs, merge_fields, episode, location)

                threshold = 1
                learning_times = getLearningTimes(db, experiment_configs, location, threshold, merge_fields)


                # PLOT BOXPLOT
                group_name = f'{m}'
                plot_title = f'Maze {m[1:]} - Trace {t}'
                ylim = [0, 1]

                box_plot = plot_grouped_box_plot(runtimes_last_episode, 'base layer', 'steps', 'legend groups', 'Base Layer', 'Extra Steps', 'Group', plot_title, ylim)
                ggsave(box_plot, folder_lu + f'Boxplots-{m}-T{int(t*10)}-l{ylim[1]}.pdf', dpi=300, verbose = False)


                # PLOT LEAR TIME
                group_name = f'{m}'
                plot_title = f'Maze {m[1:]} - Trace {t}'
                ylim = [0, 250]

                learn_time_plot = plot_grouped_box_plot(learning_times, 'base layer', 'episode', 'legend groups', 'Base Layer', 'Episodes', 'Group', plot_title, ylim)
                ggsave(learn_time_plot, folder_lu + f'Learn_time-{m}-T{int(t*10)}-l{ylim[1]}-Th{threshold}.pdf', dpi=300, verbose = False)


                # PLOT RUNTIME - ONLY ONE BASE LAYER PER PLOT
                for base_layer, plot_data in summaries.groupby(['base layer']):
                    group_name = f'{m}'
                    plot_title = f'Maze {m[1:]} - Trace {t} - Base layer {base_layer}'
                    xlim = [0, 1000]
                    ylim = [0, 2]

                    save_name = folder_lu_runtimes + f'runtimes-{m}-T{int(t*10)}-L{base_layer}-y{ylim[1]}-x{xlim[1]}.pdf'
                    print(f'    Plot layer: {base_layer}   -   file: {ntpath.basename(save_name)}')
                    runtime_plot = plot_time_series(plot_data, 'episode', 'steps', 'legend groups', 'Episode', 'Extra Steps', 'Group', plot_title, xlim, ylim )
                    ggsave(runtime_plot, save_name, dpi=300, verbose = False)


    #########################################################################################################################################################
    # NON UNIFORM EXPERIMENT:
    #########################################################################################################################################################
    if plot_non_uniform:
        folder_nu = os.path.join(figure_folder,'non_uniform/')
        # folder_nu_runtimes = os.path.join(folder_nu, 'runtimes/')
        make_folder(folder_nu)
        # make_folder(folder_nu_runtimes)

        for m in ['M0', 'M1', 'M8']:
            print(f'PLOTTING NON UNIFORM: {m}')
            for t in [0, 0.7]:
                # GET CONFIGS RELEVANT TO EXPERIMENT
                experiment_configs = configs[ configs.mazeFile.str.contains(m + '.xml') & ( configs.traces == t ) & configs.pc_files.str.contains('|'.join(['non_uniform'] + min_layers)) ].copy()
                experiment_configs = pd.merge(experiment_configs.reset_index(), layer_metrics, left_on='pc_files', right_on='layer', how='left').set_index('config')

                # add column layer alias
                alias = lambda l : l[0:3] if l[0] == 'u' else 'nu'
                cells = lambda r : r['number of cells']
                alias_column = experiment_configs.apply( lambda r : f'{alias(r["pcs"])} ({cells(r)})' , axis = 1 )
                aliases = list(alias_column.values)
                aliases = [aliases[-1]] + aliases[0:-1]
                aliases2 = sorted(aliases, key = lambda v : int(re.search(r'\((\d+)\)', v).group(1)), reverse=True )
                for i in range(len(aliases2)):
                    if 'nu' in aliases2[i]:
                        position = i
                        break
                experiment_configs['layer_alias'] = alias_column.astype(CategoricalDtype(aliases, ordered=True))
                experiment_configs['layer_alias2'] = alias_column.astype(CategoricalDtype(aliases2, ordered=True))


                # GET AND AUGMENT DATA
                merge_fields = ['layer_alias', 'layer_alias2']
                episode = lastEpisode(experiment_configs, sample_rate)
                location = -1
                summaries, runtimes_last_episode = getDataEpisodeAndSummaries(db, experiment_configs, merge_fields, episode, location)

                threshold = 1
                learning_times = getLearningTimes(db, experiment_configs, location, threshold, merge_fields)


                # PLOT BOXPLOTS
                plot_title = f'Maze {m[1:]} - Trace {t}'
                lims = [0, 1]
                box_plot_colors = ['black' for i in range(len(aliases))]
                box_plot_colors[position] = 'red'

                save_name = f'Boxplots-{m}-T{int(t*10)}-l{lims[1]}.pdf'
                print(f'      PLOT: BOXPLOT - {save_name}')
                box_plot = plot_box_plot(runtimes_last_episode, 'layer_alias2', 'steps', 'Layer', 'Extra Steps', plot_title, lims, box_plot_colors)
                ggsave(box_plot, folder_nu + save_name, dpi=300, verbose = False)


                # PLOT LEARN TIME
                lims = [0, 1000]
                save_name = f'Learn_time-{m}-T{int(t*10)}-l{lims[1]}-Th{threshold}.pdf'
                print(f'      PLOT: BOXPLOT - {save_name}')
                learn_time_plot = plot_box_plot(learning_times, 'layer_alias2', 'episode', 'Layer', 'Episodes', plot_title, lims, box_plot_colors)
                ggsave(learn_time_plot, folder_nu + save_name, dpi=300, verbose = False)


                # PLOT RUN TIMES
                plot_title = f'Maze {m[1:]} - Trace {t}'
                ylims = [0, 1]
                xlims = [0, 10000]

                save_name = f'runtimes-{m}-T{int(t*10)}-y{ylims[1]}-x{xlims[1]}.pdf'
                print(f'      PLOT: RUNTIME - {save_name}')
                runtime_plot = plot_time_series(summaries, 'episode', 'steps' , 'layer_alias', 'Episode', 'Extra Steps', 'Group', plot_title , xlims, ylims )
                runtime_plot += scale_color_discrete()
                ggsave(runtime_plot, folder_nu + save_name, dpi=300, verbose = False)


    #########################################################################################################################################################
    # DENSITY EXPERIMENT - FIXED NUMBER OF OBSTACLES:
    ######################################################################################################################################################### 

    if plot_density_same_maze:
        # CREATE FOLDERS FOR EXPERIMENT
        folder_density_obstacle_num = os.path.join(figure_folder, 'density_fixed_obstacle_num/')
        make_folder(folder_density_obstacle_num)

        # mazes for this experiment
        mazes = ['M0'] + [f'M{i}{j:02d}' for i in range(1,7) for j in range(19)]
        # layers = [f'u{4*i:02d}' for i in range(1,15)]

        for  o in [i*10 for i in range(7)]:
            print(f'PLOTTING DENSITY: {o}')
            for t in [0, 0.7]:

                # GET CONFIGS RELEVANT TO EXPERIMENT
                # keep mazes with varying number of obstacles only (all but M1 and M8), and only uniform layers
                experiment_configs = configs[configs.maze.isin(mazes) & configs.pcs.map(lambda v: v[0] == 'u') & (configs.traces == t)].copy()
                experiment_configs['num_obstacles'] = experiment_configs.maze.map(lambda m : int(m[1])*10)
                experiment_configs['scale'] = experiment_configs.pcs.map(lambda v : int(v[1:3]) )
                experiment_configs = pd.merge(experiment_configs.reset_index(), layer_metrics, left_on='pc_files', right_on='layer', how='left').set_index('config')
                experiment_configs = experiment_configs[(experiment_configs.num_obstacles == o) & (experiment_configs.scale % 8 == 0)]

                # GET AND AUGMENT DATA
                merge_fields = ['num_obstacles', 'scale', 'number of cells']
                episode = lastEpisode(experiment_configs, sample_rate)
                location = -1
                summaries, runtimes_last_episode = getDataEpisodeAndSummaries(db, experiment_configs, merge_fields, episode, location)

                threshold = 1
                learning_times = getLearningTimes(db, experiment_configs, location, threshold, merge_fields)


                # PLOT BOXPLOTS SCALE
                plot_title = f'Obstacles {o} - Trace {t}'
                lims = [0, 1.5]
                save_name = f'Boxplots_Scale-O{o}-T{int(t*10)}-l{lims[1]}.pdf'
                print(f'      PLOT: BOXPLOT - {save_name}')

                r2 = runtimes_last_episode[runtimes_last_episode.scale > 4].copy()
                r2['num_cells'] = pd.Categorical(r2['number of cells'], np.sort(r2['number of cells'].unique())[::-1])
                r2['scale_d'] = pd.Categorical(r2['scale'], np.sort(r2['scale'].unique())) 

                box_plot_scale = plot_faceted_box_plot(r2, 'num_cells', 'steps', 'scale_d', 'Number of cells', 'Extra Steps' , plot_title, lims)
                ggsave(box_plot_scale, folder_density_obstacle_num + save_name, dpi=300, verbose = False, width = 10, height =5)


                # PLOT LEARN TIME SCALE
                lims = [0, 5000]
                save_name = f'Learn_time_Scale-O{o}-T{int(t*10)}-l{lims[1]}.pdf'
                print(f'      PLOT: BOXPLOT - {save_name}')

                learn_times_2 = learning_times[learning_times.scale > 4].copy()
                learn_times_2['num_cells'] = pd.Categorical(learn_times_2['number of cells'], np.sort(learn_times_2['number of cells'].unique())[::-1])
                learn_times_2['scale_d'] = pd.Categorical(learn_times_2['scale'], np.sort(learn_times_2['scale'].unique())) 

                learn_time_plot_scale = plot_faceted_box_plot(learn_times_2, 'num_cells', 'episode', 'scale_d', 'Number of Cells', 'Episodes' , plot_title, lims)      
                ggsave(learn_time_plot_scale, folder_density_obstacle_num + save_name, dpi=300, verbose = False, width = 10, height =5)


                # PLOT BOXPLOT CELLS
                lims = [0, 1.5]
                save_name = f'Boxplots_Cells-O{o}-T{int(t*10)}-l{lims[1]}.pdf'
                print(f'      PLOT: BOXPLOT - {save_name}')

                counts = runtimes_last_episode['number of cells'].value_counts()
                filtered_runtimes = runtimes_last_episode[runtimes_last_episode['number of cells'].isin(counts[counts>100].index)].reset_index(drop=True).copy()
                filtered_runtimes['num_cells'] = pd.Categorical(filtered_runtimes['number of cells'], np.sort(filtered_runtimes['number of cells'].unique())[::-1])
                filtered_runtimes['scale_d'] = pd.Categorical(filtered_runtimes['scale'], np.sort(filtered_runtimes['scale'].unique())) 

                box_plot_cells = plot_faceted_box_plot(filtered_runtimes, 'scale_d', 'steps', 'num_cells', 'PC Radius (cm)', 'Extra Steps' , plot_title, lims)
                ggsave(box_plot_cells, folder_density_obstacle_num + save_name, dpi=300, verbose = False, width = 10, height =5)


                # PLOT LEARN TIME CELLS
                lims = [0, 5000]
                save_name = f'Learn_Time_Cells-O{o}-T{int(t*10)}-l{lims[1]}.pdf'
                print(f'      PLOT: BOXPLOT - {save_name}')

                counts = learning_times['number of cells'].value_counts()
                filtered_learn_times = learning_times[learning_times['number of cells'].isin(counts[counts>100].index)].reset_index(drop=True).copy()
                filtered_learn_times['num_cells'] = pd.Categorical(filtered_learn_times['number of cells'], np.sort(filtered_learn_times['number of cells'].unique())[::-1])
                filtered_learn_times['scale_d'] = pd.Categorical(filtered_learn_times['scale'], np.sort(filtered_learn_times['scale'].unique())) 

                learn_time_plot_cells = plot_faceted_box_plot(filtered_learn_times, 'scale_d', 'episode', 'num_cells', 'PC Radius (cm)', 'Episodes', plot_title, lims)
                ggsave(learn_time_plot_cells, folder_density_obstacle_num + save_name, dpi=300, verbose = False, width = 10, height =5)


    #########################################################################################################################################################
    # DENSITY EXPERIMENT - Finding best density for each density / scale:
    ######################################################################################################################################################### 

    if plot_best_densities:

        # CREATE FOLDERS FOR EXPERIMENT
        folder_density_best_densities = os.path.join(figure_folder, 'density_best_densities/')
        make_folder(folder_density_best_densities)

        # mazes for this experiment
        mazes = ['M0'] + [f'M{i}{j:02d}' for i in range(1,7) for j in range(19)]

        for t in [0, 0.7]:

            # FIND BEST NUMBER OF CELLS FOR EACH LAYER FOR EACH OBSTACLE NUMBER:
            experiment_configs = configs[configs.maze.isin(mazes) & configs.pcs.map(lambda v: v[0] == 'u') & (configs.traces == t)].copy()
            experiment_configs['num_obstacles'] = experiment_configs.maze.map(lambda m : int(m[1])*10)
            experiment_configs['scale'] = experiment_configs.pcs.map(lambda v : int(v[1:3]) )
            experiment_configs = pd.merge(experiment_configs.reset_index(), layer_metrics, left_on='pc_files', right_on='layer', how='left').set_index('config')

            merge_fields = ['num_obstacles', 'scale', 'maze' ,'number of cells']
            episode = lastEpisode(experiment_configs, sample_rate)
            location = -1
            summaries, _ = getDataEpisodeAndSummaries(db, experiment_configs, merge_fields, episode, location, skip_runtimes= True)
            summaries = summaries[summaries.episode == episode].copy().reset_index()

            # FIND BEST NUMBER OF CELLS FOR EACH SCALE AND NUMBER OF OBSTACLES, 
            average_results = summaries.groupby(['num_obstacles','scale','number of cells']).steps.mean().reset_index()
            best_num_cells = average_results.loc[average_results.groupby(['num_obstacles','scale']).steps.idxmin()].reset_index(drop=True)
            mean_num_cells = best_num_cells.groupby(['num_obstacles'])['number of cells'].agg(['mean','std']).reset_index()
            best_num_cells2 = best_num_cells.loc[best_num_cells.scale % 8 == 0].astype('category')  


            # PLOTS:
            p0 = ggplot(best_num_cells2, aes('num_obstacles', 'number of cells', color='num_obstacles'))
            p0 += geom_point(position=position_dodge(width=0.5))
            p0 += labs(x='Obstacles', y='Number of cells', color="Obstacles", title=f'Optimal number of cells - Trace {t}')
            p0 += facet_grid(". ~ scale")
            p0 += scale_color_brewer(type="seq", palette=1, name='Obstacles', limits = (-20,-10, 0, 10, 20, 30, 40, 50, 60), breaks=(0, 10, 20, 30, 40, 50, 60)) 
            # p0 += theme_dark()
            p0 += theme(axis_text_x=element_text(rotation=90, hjust=0.5))

            p1 = ggplot(best_num_cells2, aes('scale', 'number of cells', color='scale'))
            p1 += labs(x='Scale', y='Number of cells', color="Scale", title=f'Optimal number of cells - Trace {t}')
            p1 += geom_point(position=position_dodge(width=0.5))
            p1 += facet_grid(". ~ num_obstacles")
            # p1 += theme_dark()
            p1 += theme(axis_text_x=element_text(rotation=90, hjust=0.5))

            p2 = ggplot(mean_num_cells, aes('num_obstacles', 'mean'))
            p2 += labs(x='Obstacles', y='Number of cells', title=f'Optimal number of cells - Trace {t}')
            p2 += geom_point()


            ggsave(p0, folder_density_best_densities + f'cells_vs_obstacles_per_scale-T{int(t*10)}.pdf', dpi=300, verbose = False, width=8, height=4)
            ggsave(p1, folder_density_best_densities + f'cells_vs_scale_per_obstacles-T{int(t*10)}.pdf', dpi=300, verbose = False, width=8, height=4)
            ggsave(p2, folder_density_best_densities + f'cells_vs_obstacles-T{int(t*10)}.pdf', dpi=300, verbose = False)



    # # first plot locally uniform experiment: 


def plot_experiment_12(figure_folder, configs, sample_rate, db):

    plot_locally_uniform = True
    
    sample_rate = 1
    mazes = ["M100"]
    replay_budgets = [0,100,1000]
    location = -1
    

    # ADD COLUMNS TO CONFIGS
    configs['c_id'] = configs.index.map(lambda v : int(v[1:]))
    configs['pc_files'] = configs.pc_files.map(os.path.normpath )
    configs['pcs'] = configs.pc_files.map(lambda v : ntpath.basename(v)[0:-4])
    configs['maze']= configs.mazeFile.map(lambda v : ntpath.basename(v)[0:-4])

    # GET LAYER METRICS 
    layer_metrics = pd.read_csv(layer_metrics_file)
    layer_metrics['layer'] = layer_metrics.layer.map(lambda l : os.path.normpath(layers_folder + l) ) # normalize path and prepend location


    #########################################################################################################################################################
    # Plotting Functions:
    #########################################################################################################################################################
    def plot_box_plot(data, x_column, y_column, x_title, y_title, plot_title, ylim, box_colors):
        # print(data)
        p0 = ggplot(data, aes(x_column, y_column ))
        p0 += geom_jitter(alpha=0.3)
        p0 += geom_boxplot(alpha=0.7, notch=False, outlier_alpha=0, color = box_colors )
        p0 += xlab(x_title)
        p0 += ylab(y_title)
        p0 += ggtitle(plot_title)
        # p0 += labs(x=x_title, y=y_title, title=plot_title)
        # p0 += theme(axis_text_x=element_text(rotation=45, hjust=1))
        # p0 += coord_cartesian(ylim=ylim)
        return p0

    def plot_time_series(data, x_column, y_column, fill_column, x_title, y_title, legend_title, plot_title):
        p0 = ggplot(data, aes(x_column, y_column, color=fill_column))
        p0 += geom_line()
        p0 += labs(x=x_title, y=y_title, color=legend_title, title=plot_title, caption='smt')
        # p0 += coord_cartesian(ylim=ylim, xlim=xlim)
        p0 += scale_color_discrete()
        return p0

    def plot_replay_matrix(data,maze_folder,pcs_folder):

        # Defines map for labels
        my_labels = {'sc' : 'Stongest Connection',
                     'gl' : 'Goal Location',
                     'sp' : 'Starting Locations',
                     'pc' : 'Place Cells'}

        # Plots the maze and Place Cells
        maze_file = os.path.join(maze_folder, data['maze']+'.xml')
        walls, feeders, start_positions = parse_maze(maze_file)
        pc_file = os.path.join(pcs_folder, data['pcs']+'.csv')
        cells = parse_all_cells(pc_file)
        fig, ax = plt.subplots()
        x = walls.loc[:, walls.columns[::2]]
        y = walls.loc[:, walls.columns[1::2]]
        for i in range(len(walls)):
            ax.plot(x.iloc[i,:], y.iloc[i,:], color='black', alpha=1.0)
        x = feeders['x']
        y = feeders['y']
        for i in range(len(x)):
            ax.plot(x,y,'rx', label=my_labels['gl'])
            my_labels['gl']= '_nolegend_'
        x = start_positions['x']
        y = start_positions['y']
        for i in range(len(x)):
            ax.plot(x,y,'bo', label=my_labels['sp'])
            my_labels['sp']= '_nolegend_'

        x = cells['x']
        y = cells['y']
        r = cells['r']
        xy = tuple(zip(x,y))
        coll = matplotlib.collections.EllipseCollection(r, r,
                                                        np.zeros_like(r),
                                                        offsets=xy, units='x',
                                                        transOffset=ax.transData,
                                                        color= 'b',
                                                        alpha= 0)
        ax.add_collection(coll)

        # Gets Replay Matrix and Ignores Self Connected Place Cells
        cell_data = data['replay_matrix']
        np.fill_diagonal(cell_data,0.0)

        # Plots the Replay Matrix
        nonconnected_cells = []
        nonconnected_cells_r = []

        # Gets the index and value of max connection for each place cell
        max_index = np.argmax(cell_data, axis = 1)
        max_value = np.amax(cell_data,axis = 1)

        # Adds a line connection cells to their max connection
        for cell_index in range(len(cell_data)):
            # Plot a connection if it exsists
            if max_value[cell_index] != 0:
                # Connected to another Place Cell
                x=cells.values[cell_index][0]
                y=cells.values[cell_index][1]
                dx=cells.values[max_index[cell_index]][0] - x
                dy=cells.values[max_index[cell_index]][1] - y
                ax.arrow(x,y,dx,dy,width=.01, length_includes_head = True, label= my_labels['sc'],color = 'b',alpha=.5)
                my_labels['sc'] = '_nolegend_'

            # Has no connection
            else:
                nonconnected_cells.append((cells.values[cell_index][0], cells.values[cell_index][1]))
                nonconnected_cells_r.append(cells.values[cell_index][2])


        # Adds red circles for non connected PCs
        coll = matplotlib.collections.EllipseCollection(nonconnected_cells_r, nonconnected_cells_r,
                                                        np.zeros_like(nonconnected_cells_r),
                                                        offsets=nonconnected_cells, units='x',
                                                        transOffset=ax.transData,
                                                        color= 'r',
                                                        alpha= .5
                                                        )
        ax.add_collection(coll)

        # Save Plot
        lg = plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
        name = 'ReplayMatrix: Maze '+ data['maze'] + ', Rat'+ str(data['rat']) + ', Replay Budget' + str(data['replay_budget'])
        tit = fig.suptitle(name, fontsize=14)
        ax.set_aspect(1)
        #plt.show()
        return fig
    #########################################################################################################################################################
    # LOCALLY UNIFORM EXPERIMENT:
    #########################################################################################################################################################
    if plot_locally_uniform:

        # CREATE FOLDERS FOR EXPERIMENT
        folder_lu = os.path.join(figure_folder,'replay_with_uniform_layers/')
        folder_lu_runtimes = os.path.join(folder_lu, 'runtimes/')
        folder_lu_learntimes = os.path.join(folder_lu, 'learntimes/')
        folder_lu_replayMatrix = os.path.join(folder_lu, 'replay_matrix/')
        folder_lu_replayStats = os.path.join(folder_lu, 'replay_stats/')
        make_folder(folder_lu)
        make_folder(folder_lu_runtimes)
        make_folder(folder_lu_learntimes)
        make_folder(folder_lu_replayMatrix)
        make_folder(folder_lu_replayStats)



        # experiment_configs = configs[ configs.mazeFile.str.contains(m + '.xml')].copy()

        for m in mazes:
            # GET CONFIGS RELEVANT TO EXPERIMENT
            # EX:
            # experiment_configs = configs[configs.maze.isin(mazes) & configs.pcs.map(lambda v: v[0:3] == l) & (configs.traces == t)].copy()
            experiment_configs = configs[configs.maze == m ].copy()

            # GET AND AUGMENT DATA
            threshold = 1
            location = -1

            merge_fields = ['mazeFile', 'replay_budget']
            episode = lastEpisode(experiment_configs, sample_rate)
            
            summaries, runtimes_last_episode = getDataEpisodeAndSummaries(db, experiment_configs, merge_fields, episode, location)
            learning_times = getLearningTimes(db, experiment_configs, location, threshold, merge_fields)

            # GET REPLAY Matrix
            merge_fields = ['maze', 'replay_budget', 'pcs']
            replay_summaries = getReplayData(db, experiment_configs, merge_fields, episode, location)

            # Redefines replay_budget as catigorical for plotting purposes
            addCatigoricalData(summaries,'replay_budget')
            addCatigoricalData(runtimes_last_episode,'replay_budget')
            addCatigoricalData(replay_summaries,'replay_budget')
            addCatigoricalData(learning_times,'replay_budget')

            # # Redefines replay_budget as catigorical for plotting purposes
            # summaries['replay_budget_c'] = summaries['replay_budget'].astype(CategoricalDtype(summaries['replay_budget'].unique(), ordered=True))
            # learning_times['replay_budget_c'] = learning_times['replay_budget'].astype(CategoricalDtype(learning_times['replay_budget'].unique(), ordered=True))

            save_name = folder_lu_learntimes + f'learntimes-{m}.pdf'
            learn_time_plot = plot_box_plot(learning_times, 'replay_budget_c', 'episode', 'Replay Budget', 'Learn Time', "Learn Time Maze: "+ str(m), [0, 200], 'black' )
            ggsave(learn_time_plot, save_name, dpi=300, verbose = False)

            save_name = folder_lu_learntimes + f'optimalityRatio-{m}.pdf'
            learn_time_plot = plot_box_plot(runtimes_last_episode, 'replay_budget_c', 'steps', 'Replay Budget', 'Extra Steps', 'Extra Steps '+ str(m) ,[0, 200], 'black')
            ggsave(learn_time_plot, save_name, dpi=300, verbose = False)
            
            save_name = folder_lu_runtimes + f'runtimes-{m}.pdf'
            runtime_plot= plot_time_series(summaries, 'episode', 'steps', 'replay_budget_c', 'Episodes', 'Steps', 'Replay Budget', "Run Time Maze: " + str(m) )
            ggsave(runtime_plot, save_name, dpi=300, verbose = False)

            # Remove data with Replay Budget 0
            replay_summaries = replay_summaries[replay_summaries['replay_budget_c']!=0]

            save_name = folder_lu_replayStats + f'ReplayAverage-{m}.pdf'
            replay_average_plot= plot_box_plot(replay_summaries, 'replay_budget_c', 'mean', 'Replay Budget', 'Average Connection', str(m), [0, 200], 'black')
            ggsave(replay_average_plot, save_name, dpi=300, verbose = False)

            save_name = folder_lu_replayStats + f'ReplaySTD-{m}.pdf'
            replay_std_plot= plot_box_plot(replay_summaries, 'replay_budget_c', 'std', 'Replay Budget', 'STD Connection', str(m), [0, 200], 'black')
            ggsave(replay_std_plot, save_name, dpi=300, verbose = False)

            save_name = folder_lu_replayStats + f'ReplayTotals-{m}.pdf'
            replay_total_plot= plot_box_plot(replay_summaries, 'replay_budget_c', 'total_connection', 'Replay Budget', 'Total Connection', str(m), [0, 200], 'black')
            ggsave(replay_total_plot, save_name, dpi=300, verbose = False)


            maze_folder, pcs_folder = getMazeAndPcsFolder()
            for index, rat in replay_summaries.iterrows():
                fig = plot_replay_matrix(rat,maze_folder,pcs_folder)
                save_name = folder_lu_replayMatrix + f"RM_{m}_rat_{rat['rat']}_budget_{rat['replay_budget_c']}.pdf"
                fig.savefig(save_name,
                    dpi=300,
                    format='pdf',
                    bbox_inches = 'tight')
                plt.close(fig)



                

def format_pc_file(file_name):
    # WARNING: also used for maze, if no longer useful will need separate funcion
    pc_file = ntpath.basename(file_name)[0:-4]
    return f'{pc_file}'


def plot_experiment(folder):
    # get experiment folder
    folder = os.path.join(sys.argv[1], '')

    # load configs and connect to database
    configs = load_config_file(folder)
    db = sqlite3.connect(folder + 'experiment_results.sqlite', detect_types=sqlite3.PARSE_DECLTYPES)

    # create figures folder
    figure_folder = folder + 'figures/'
    make_folder(figure_folder)

    # plot the experiment
    experiment_name = ntpath.basename((ntpath.normpath(folder)))\
                            .split(sep='-')[0][10:]  # all experiments use syntax 'experimentN-...'

    experiment_map = {}
    # experiment_map['1'] = ( plot_experiment_traces_and_scales_per_maze, 5 )
    # experiment_map['2'] = ( plot_scale_experiment                     , 5 )
    # experiment_map['3'] = ( plot_scale_experiment                     , 5 )
    # experiment_map['4'] = ( plot_experiment4_extraAtFeeder            , 5 )
    # experiment_map['5'] = ( plot_experiment_traces_and_nx_per_maze    , 10)
    # experiment_map['6'] = ( plot_experiment4_extraAtFeeder            , 5 )
    # experiment_map['7'] = ( plot_experiment7, 5)
    # experiment_map['8'] = ( plot_experiment_8, 5)
    # experiment_map['9'] = ( plot_experiment_8, 5)
    #experiment_map['11'] = ( plot_experiment_11, 5)
    experiment_map['12'] = ( plot_experiment_12, 1)

    # plot the experiment
    e = experiment_map[experiment_name]
    fun = e[0]
    sample_rate = e[1]
    fun(figure_folder, configs, sample_rate, db)


if __name__ == '__main__':
    folder_arg = sys.argv[1]
    # folder_arg = 'D:/JavaWorkspaceSCS/Multiscale-F2019/experiments/BICY2020_modified/logs/experiment1-traces/'
    plot_experiment(folder_arg)