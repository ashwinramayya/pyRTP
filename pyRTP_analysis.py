# RTP_analysis (Random Tone Pitch Analysis). Performs basic RT analysis on behavioral data

import numpy as np
import pandas as pd
import pickle
import os
from scipy import stats

# plot in separate windows, interactive
import matplotlib
matplotlib.use('macosx')

matplotlib.rcParams['interactive'] = True
matplotlib.rcParams['axes.autolimit_mode'] = 'round_numbers'
matplotlib.rcParams['axes.xmargin'] = 0
matplotlib.rcParams['axes.ymargin'] = 0

# plotting
from pylab import *
close('all') 

# Define Functions

# load task_df and config
def loadData(subj,sessNum):
    sesspath_data = os.getcwd()+'/data/'+subj+'/session'+str(sessNum)+'/data.csv'
    sesspath_config = os.getcwd()+'/data/'+subj+'/session'+str(sessNum)+'/config.csv'
    task_df = pd.read_csv(sesspath_data,index_col ='trial')
    config_df = pd.read_csv(sesspath_config,index_col ='parameter')
    return task_df,config_df


# getRTs
def getRTs(task_df,evQuery = None,rt_dist_type = 'standard'):

    # This function returns rt values for all trials from a subject. It has the option to filter out particular trials, and apply various transforms on the rt distribution

    #evQuery .. how to filter events

    #rt_dist_type
    #            'standard' ... no transform       
    #            'reciprocal'... 1/rt
    #            'zrrt'...z-score (-1/RT) (as used in later analyses,
    #             no need to invert axes as high RTs are on the right
    #            'reciprobit'...cum probability vs. 1/rt

    # filter by trial type (e.g., error = 0)
    if evQuery != None:
    	task_df = task_df.query(evQuery)


    # parse rt dist type
    if rt_dist_type == 'standard':
        rts = task_df['RT'].to_numpy()
    elif rt_dist_type == 'reciprocal':
        rts = -1./task_df['RT'].to_numpy().astype('float')
    elif rt_dist_type == 'zrrt':
        rts = stats.zscore(-1./task_df['RT'].to_numpy().astype('float'))
    elif rt_dist_type == 'reciprobit':
    	# SORTED RTs
    	rts = np.sort(task_df['RT'].to_numpy().astype('float'))

    return rts
#basic function to plot RT
def plotRT(task_df, evQuery = None, ax = None,plot_type = 'standard', bins = 40, alpha = 1,label = None,plot_median = False):
    # Note: this funciton doesnt set the axes for the RT plot. Run set_axes_rt afterwards
    # Inputs:
    #evQuery .. how to filter events
    #ax .. axes to plot on
    #plot_type ..'standard'... plots standard rts
    #            'reciprocal'...-1/rt
    #            'zrrt'...z-score (-1/RT) (as used in later analyses)
    #            for reciprocal and zrrt, no need to invert axes as high RTs are on the right
    #            'reciprobit'...cum probability vs. 1/rt
    #bins......  number of bins for hist plots
    #alpha.....transperency of histrogram
    #label..... label of distribution

    # parse fig,ax
    if ax==None:
        fig = figure(figsize=(5,5))
        ax = subplot(111)

    # plot RT dist for various formats
    if plot_type == 'reciprobit': # plot reciprobit plot -SPECIAL CASE
        # plot empirical cumulative distribution function of RT dist
        # x values are sorted RT data
        rt_sort = getRTs(task_df,evQuery = evQuery,rt_dist_type = plot_type)


        # y values are cumulative probabilities (cumulative sum of x values that are normalized)
        cum_prob = np.cumsum(rt_sort)/np.sum(rt_sort)

        # convert cum_prob to probit scale (inverse of CDF)
        cum_prob_probit = stats.norm.ppf(cum_prob);

        # plot cumulative probabilities
        l = ax.plot(-1/rt_sort,cum_prob_probit,marker = '.',linestyle='',alpha=0.5,label = label)
        col = l[0].get_color()
        med_rt = np.median(-1/rt_sort)

    else: # plot standard,reciprocal or zrrt RT
        rts = getRTs(task_df,evQuery = evQuery,rt_dist_type = plot_type)
        h = ax.hist(rts, bins = bins, alpha = alpha,label = label)
        col = h[2][0].get_facecolor()
        med_rt = np.median(rts)

    #if plot_median== True:
        #yl = ylim()
        #ax.vlines(x = med_rt,ymin = yl[0]*10, ymax = ylim()[1]*10,linestyles = 'dashed',alpha = 0.7,color = col)
        #ylim(yl)


# set axes for RT plot
def set_axes_rt(ax, plot_type = 'standard',legend_fontsize = 10):
    # Input:
    #ax... axis on which RT distributions are plotted
    #plot_type ..'standard'... plots standard rts
    #            'reciprocal'...1/rt
    #            'reciprobit'...cum probability vs. 1/rt


    # invert x-axis and label xticks with RT values
    if plot_type in ['reciprocal','reciprobit']:

        # set xtick labels as 1/xtick values so that RT values are shown
        ax.set_xticklabels(labels = -1*np.round(1/ax.get_xticks(),1))

    if plot_type in ['standard','reciprocal']:
        # set labels
        ax.set_xlabel('RT (ms)')
        ax.set_ylabel('Count')
    elif plot_type == 'zrrt':
        ax.set_xlabel('z(-1/RT)')
        ax.set_ylabel('Count')
    elif plot_type == 'reciprobit':
        # set labels
        ax.set_xlabel('RT (ms)')
        ax.set_ylabel('z-score Cumulative probability')

    # set label
    ax.legend(fontsize = legend_fontsize)


# plot RT distributions by condition
# run function
def plot_RT_by_condition(task_df,condition = 'coherence',bins = 20, evQuery=None,label = None, plot_type = 'standard',fig_params_dict=None,ax = None,plot_median = True):
    # Inputs
    # ax ... must be of length two (left is full RT dist, right is by delay)
    # default fig_params
    fig_params={'figsize':(10,5),'label':evQuery,'title':'RT '+plot_type,'title_fontsize':15}

    # update fig_params
    if fig_params_dict!=None:
        fig_params.update(fig_params_dict)

    if ax == None:
        fig = figure(figsize=(fig_params['figsize'][0],fig_params['figsize'][1]))

    # set title
    fig.suptitle(fig_params['title'],fontsize=fig_params['title_fontsize'])

    # plot full RT
    # create axes
    if ax == None:
        ax_list = [] 
        ax_list.append(subplot(1,2,1))
        ax_list.append(subplot(1,2,2))


    # plot RT
    plotRT(task_df,evQuery = evQuery,bins=bins, ax = ax_list[0],plot_type = plot_type,label=fig_params['label'],alpha =0.5, plot_median = plot_median)
    set_axes_rt(ax= ax_list[0],plot_type = plot_type)

    # plot RT by delay

    # plot RT dist for delay trials
    condition_list = np.unique(task_df[condition].to_numpy())

    # filter trials based on inputted evQuery
    if evQuery!=None:
        task_df = task_df.query(evQuery)

    # loop through delay conditions
    for i in np.arange(0,len(condition_list)):

        # store thisDelay in self
        thisCondition = condition_list[i]

        # plot RTs based on filtered events with additional delay filter
        task_df_filt = task_df[task_df[condition].to_numpy()==thisCondition]
        plotRT(task_df_filt,evQuery = None,bins=bins, ax = ax_list[1],plot_type = plot_type,alpha = 0.5,label = (condition +str(thisCondition)),plot_median=plot_median)

    # set axes
    set_axes_rt(ax=ax_list[1],plot_type = plot_type)

##### RUN SCRIPT
subj = input ("Enter Subject ID :") 
sessNum = input ("Enter Session number:") 

# load data
task_df,config_df = loadData(subj,sessNum)


# plot RTs

#plotRT(task_df,bins = 10,evQuery = 'RT>0',plot_type = 'standard')
#plotRT(task_df,bins = 10,evQuery = 'RT>0',plot_type = 'reciprocal')
#plotRT(task_df,bins = 10,evQuery = 'RT>0',plot_type = 'reciprobit')

# plot it
plot_RT_by_condition(task_df,condition = 'coherence',bins = 10,evQuery = 'RT>0',plot_type = 'standard')
plot_RT_by_condition(task_df,condition = 'coherence',bins = 10,evQuery = 'RT>0',plot_type = 'reciprocal')
plot_RT_by_condition(task_df,condition = 'coherence',bins = 10,evQuery = 'RT>0',plot_type = 'reciprobit')

plot_RT_by_condition(task_df,condition = 'block',bins = 10,evQuery = 'RT>0',plot_type = 'standard')
plot_RT_by_condition(task_df,condition = 'block',bins = 10,evQuery = 'RT>0',plot_type = 'reciprocal')
plot_RT_by_condition(task_df,condition = 'block',bins = 10,evQuery = 'RT>0',plot_type = 'reciprobit')



input ("CLOSE FIGURES?") 
