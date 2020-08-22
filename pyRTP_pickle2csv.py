# This function will convert an incomplete session to a csv file by loading the task data dataframe and writing a csv file

import numpy as np
import pandas as pd
import pickle
import os

def load_pickle(fpath):
    """Return object."""
    with open(fpath, 'rb') as f:
        obj = pickle.load(f)
    return obj


# Prompt ask for subj and session ID. This will overwrite default subj ID created during initialization
subj = input ("Enter Subject ID :") 
sess = input ("Enter Session number:") 

#  Sess directory
sessdir = os.getcwd()+'/data/'+subj+'/session'+str(sess)
filepath = sessdir+'/taskData'

trialDict_list = load_pickle(filepath)

# convert to dataframe
task_df = pd.DataFrame(trialDict_list)
task_df.index.name = 'trial'

# write CSV file
task_df.to_csv(path_or_buf = sessdir+'/data.csv')