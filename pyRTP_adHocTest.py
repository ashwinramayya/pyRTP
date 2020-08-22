# This script supports flexible, ad-hoc testing at the end of each session that can be paced by the experimenter. It logs a button press and sends a sync pulse. The button press can be used by the experimenter to log a verbal cue. E.g., to perform ad-hoc saccade testing, the experiementer would control the buttons and simultaneously cue the saccade and log the button press ("Left" and press left button)

import psychtoolbox as ptb
import numpy as np
import pandas as pd
import pickle
import os

# import sound
import psychopy
psychopy.prefs.hardware['audioLib'] = ['PTB']

from psychopy import visual,core,sound

# set audio driver to psychtoolbox
#from psychopy import prefs,visual,core # monotonicClock starts when we import this 

# import keyboard
import psychopy.hardware.keyboard as keyboard

# import sync 
from labjack import u3

# params dict 
params = {}
params['numTrials'] = 10


params['SYNC_useDigitalOut'] = True
#params['SYNC_digitalOut_chan'] = 'FI02' # These are hard coded 
#params['SYNC_analogOut_chan'] = 'DAC0'
params['SYNC_volt'] = 1.5 # 1.5 V pulse (only matters for analog out)
# these are populated after getting calibration data
params['SYNC_pulse_val'] = None  
params['SYNC_zero_val'] = None 
params['SYNC_deviceObj'] = None

# initialize labjack
try:
    params['SYNC_deviceObj'] = u3.U3()
    params['SYNC_deviceObj'].getCalibrationData()
    

    if params['SYNC_useDigitalOut'] == True:
        # we are using digital output

        # set FI02 direcection to output
        params['SYNC_deviceObj'].getFeedback(u3.BitDirWrite(2,1))

        print('Sync pulses are sent from the FI02 channel. Connect cathode (red wire) to FI02 and annode (black wire) to ground.')

    else: 
        # we are using analog output 
        params['SYNC_pulse_val'] =  params['SYNC_deviceObj'].voltageToDACBits(params['SYNC_volt'], dacNumber = 0, is16Bits = False)
        params['SYNC_zero_val'] =  params['SYNC_deviceObj'].voltageToDACBits(0, dacNumber = 0, is16Bits = False)

        print('Sync pulses are sent from the DAC0 channel. Connect cathode (red wire) to DAC0 and annode (black wire) to ground.')

except:
    print('Unable to open LABJACK. Check if it is connected. If not using sync pulses, set "options_sendSYNC" to False')
    core.quit()


# button list
# (return, up) are (right and left) for the button box
params['buttonList_R'] = ['rshift','return']
params['buttonList_L'] = ['lshift','up']
params['buttonList_any'] = params['buttonList_R'][:]
params['buttonList_any'].extend(params['buttonList_L'][:])


# Pickle functions courtesy of Daniel Schonhaut
def save_pickle(obj, fpath, verbose=True):
    """Save object as a pickle file."""
    with open(fpath, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
    if verbose:
        print('Saved {}'.format(fpath))

def load_pickle(fpath):
    """Return object."""
    with open(fpath, 'rb') as f:
        obj = pickle.load(f)
    return obj



# Prompt ask for subj and session ID. This will overwrite default subj ID created during initialization
subj = input ("Enter Subject ID :") 
sess = input ("Enter Session number:") 


#  Save directory
params['subj'] = subj
params['sess'] = sess
params['saveDir'] = os.getcwd()+'/data'
# make the save folder if it doesnt exist
if os.path.exists(params['saveDir'])==False:
    os.mkdir(params['saveDir'])

# check if we have a subject directory already, if not, create  a subject directory 
params['subjDir'] = params['saveDir']+'/'+params['subj']
if os.path.exists(params['subjDir'])==False:
    os.mkdir(params['subjDir'])

# check if we have a session directory already, if not, create  a session directory 
params['sessDir'] = params['subjDir']+'/session'+str(params['sess'])
if os.path.exists(params['sessDir'])==False:
    os.mkdir(params['sessDir'])


# initialize trialDict_list
trialDictList = []

# loop through trials

for t in np.arange(0,params['numTrials']):
	print('TRIAL ',t)
	# initialize keyboard buffer
	keys_pressed = []
	keyboardTimeStart = core.monotonicClock.getTime()
	kb = keyboard.Keyboard(device = -1,waitForStart=True)# start clock
	kb.clock.reset()  # when you want to start RT timer from
	kb.clearEvents()
	kb.start() # start polling keyboard

	# Wait for a button press
	while (any(i in keys_pressed for i in params['buttonList_any'])==False):
	    # check if keys have been pressed
	    keys_pressed = kb.getKeys(params['buttonList_any'])


	trialDict = {}
	if (keys_pressed[0] in params['buttonList_R']):
	    trialDict['buttonPress'] = 'right'

	elif (keys_pressed[0] in params['buttonList_L']):
		trialDict['buttonPress'] = 'left'

	trialDict['buttonPress_s'] = keyboardTimeStart+keys_pressed[0].rt

	# send a sync
	trialDict['TTLSent_s'] = core.monotonicClock.getTime()

	if params['SYNC_useDigitalOut'] == True:
	    # We are sending a digital output
	    # Empirically this order seems to lead to a nice positive deflection 
	    params['SYNC_deviceObj'].getFeedback(u3.BitStateWrite(2,0))# FI02 to output low
	    core.wait(0.1)
	    params['SYNC_deviceObj'].getFeedback(u3.BitStateWrite(2,1))# FI02 to output high
	    

	else:
	    # We are sending an analog output
	    params['SYNC_deviceObj'].getFeedback(u3.DAC0_8(params['SYNC_pulse_val']))
	    params['SYNC_deviceObj'].getFeedback(u3.DAC0_8(params['SYNC_zero_val']))


	# append trial
	trialDictList.append(trialDict)

# save csv file
task_df = pd.DataFrame(trialDictList)

# write CSV file
task_df.to_csv(path_or_buf = params['sessDir']+'/data_adHoc.csv')
