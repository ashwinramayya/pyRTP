#pyRTP. Random Tone Pitch Task as described
#Mulder, M. J., Keuken, M. C., van Maanen, L., Boekel, W., Forstmann, B. U., & Wagenmakers, E. J. (2013). The speed and accuracy of perceptual decisions in a random-tone pitch task. Attention, Perception, & Psychophysics, 75(5), 1048-1058.

#written by Ashwin Ramayya (ashwinramayya@gmail.com)
# Random Tone
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



# SET CONFIG PARAMETERS:`
params = {}

# options
params['options_sendSYNC'] = True
if params['options_sendSYNC']==False:
	print('SYNC pulses will NOT be sent...')
else:
	from labjack import u3

params['SYNC_volt'] = 1.5 # 1.5 V pulse
params['SYNC_pulse_val'] = None  # this is populated after getting calibration data
params['SYNC_zero_val'] = None 
params['SYNC_deviceObj'] = None

params['options_playOrientOnEachTrial'] = False # show orientation sound on each trial
params['options_showFixation'] = False # show fixation cross 
params['options_shuffleTrialsAcrossBlocks'] = False # sets whether or not to shuffle trials across blocks. If set to true, it will randomly present trials and lose the block design. Set to FALSE by default

# trial parameters (will create appropriate combinations of these parameters 
params['num_trials'] = 25 #25; this is the number of trials for each condition (total trials is this value x 8 )

# sound cloud parameters
#Base note. #C4 = 261, A4 = 440
#https://pages.mtu.edu/~suits/notefreqs.html
params['baseNote'] = 440 
params['change_range'] = (2,8) # range of change per time step, in half steps. Coherent sounds will change between one and four notes on each step 
params['num_tones'] = 10 # number of tones to play simultaneously (max = 10)
params['toneRange_low'] = -9 # num half steps below baseNote, (-9, with base note of 440 corresponds to C4, 260 Hz)
params['toneRange_high'] = 63 # num half steps above baseNote(63, with base note of 440 corresponds to C10, 16744 Hz)


# timing parameters
params['dur_tonestep'] = 0.05 # time to play each sound cloud in sec (default = 50 ms)
params['dur_orient'] = .5 # time in seconds to play orientation sound
params['dur_fb'] = 1.5 # time in seconds to play feedback
params['dur_waitforsync'] = .5 # time in seconds to wait for sync pulses to send at the end of the trial

# button list
# (return, up) are (right and left) for the button box
params['buttonList_inc'] = ['rshift','return']
params['buttonList_dec'] = ['lshift','up']
params['buttonList_any'] = params['buttonList_inc'][:]
params['buttonList_any'].extend(params['buttonList_dec'] )

# responseTime limit varies by block (as a method to implement SAT)
params['responseTimeLimit_s']={'fast':10, 'slow':10} 

# block list
params['block_list'] = ['fast','slow'] 

params['coherence_list'] = [.8,.4] # [0.1 - 1]; % of tones that change pitch coherently on each time step. Remainder of tones are randomly resampled from the tone range
params['change_tones_together'] = True # if true, on each time step, it randomly draws a change value and applies it to all tones that are changing coherently. If False, it randomly generates a change value for each tone that is changing. 
params['direction_list'] = ['increase','decrease']

# trial dictionary fields (rt is also in sec)
params['trial_fields'] = ['block','trialInBlock','coherence','direction','orientOn_s','orientOff_s','stimOn_s','stimOff_s','buttonPress','choice','correct','error','buttonPress_s','RT','fbOn_s','fbOff_s','wasShown','TTL1sent_s','TTL2sent_s','TTL3sent_s']

# Print instructions
print('Instructions: Guess the Pitch Trajectory.... Press RIGHT button if you think the pitch is increasing, and press LEFT button if you think the pitch is decreasing. In FAST block, make your selection as soon as possible. In SLOW block, take your time and respond as accurately as possible')


### Define functions
def mkDirs(params):
	#  Save directory
	params['saveDir'] = os.getcwd()+'/data'
	# make the save folder if it doesnt exist
	if os.path.exists(params['saveDir'])==False:
		os.mkdir(params['saveDir'])

	# generate unique subj ID - this will be overwritten by prompt
	params['subj'] = str(core.getAbsTime())

	# Prompt ask for subj and session ID. This will overwrite default subj ID created during initialization
	subj = input ("Enter Subject ID :") 
	sess = input ("Enter Session number:") 

	# parse subj id 
	if len(subj) > 0: 
		# this means we entered a new subj ID. If empty, it will use the unique code generated at the beginning of the tast.
		params['subj'] = subj

	# check if we have a subject directory already, if not, create  a subject directory 
	params['subjDir'] = params['saveDir']+'/'+params['subj']
	if os.path.exists(params['subjDir'])==False:
		os.mkdir(params['subjDir'])

	# parse sess id
	if len(sess) > 0: 
		# this means we entered a session ID. If empty, it will create a new session based on the folders already in the subjDir
		params['sess'] = sess
	else:
		# look for folders in the subjDir
		fold_list = os.listdir(params['subjDir'])

		# find session folders
		sess_fold_list = [i for i in fold_list if 'session' in i]

		# infer session id based on folders in the subject directory
		params['sess'] = len(sess_fold_list) # zero indexed

	# sess dir 
	params['sessDir'] = params['subjDir']+'/session'+str(params['sess'])

	# make session directory
	if os.path.exists(params['sessDir'])==False:
		os.mkdir(params['sessDir'])

	# return updated params
	return params

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


# index (-1 to 1) to frequency
def ind2freq(x,baseNote = 440):
	# Generate frequencies of the equal tempered scale based on an index value that corresponds to half notes. 12 half notes is an octave

	#https://pages.mtu.edu/~suits/NoteFreqCalcs.html

	# newNote = baseNote * (a)^x

	#baseNote is the reference note
	#x is the number of halfsteps away from the reference note. Negative notes are lower frequencies and positive ns are higher frequencies
	#a is a constant. a = 2**(1/12) ~ 1.05...

	# Inputs
    #baseNote is the reference note (baseNote = 440 is A note, octave 4)

	# input:
	#x .. number of half notes from the base note (integer, including negative values)

	# Returns:
	# y ... freq value associated with index
	a = 2**(1/12)
	y = baseNote * a**x

	return y 

# play a sound cloud
def playSoundCloud(arr, dur = 0.5,baseNote = 440):
	# Simultaneously plays n tones. n is set by the length of the array thats provided as input. 
	#Inputs
	# arr ... array (of length n integers (positive and negative) selecting tones to play siultaneously. arr = [1] would play a single tone one half step up from the baseNote. arr = -1 woudl play a tone half step lower. Maximum length is 10
	tone_list = []



	for i in np.arange(0,len(arr)):

		# create a sound stimulus
		tone_list.append(sound.Sound(value=ind2freq(arr[i],baseNote=baseNote), secs=dur, volume = 1,hamming = True))

	#get onset time
	onTime_s = core.monotonicClock.getTime()

	# play sound clud
	tone_list[0].play()
	if len(arr)>9:
		tone_list[9].play()
	if len(arr)>8:
		tone_list[8].play()
	if len(arr)>7:
		tone_list[7].play()
	if len(arr)>6:
		tone_list[6].play()
	if len(arr)>5:
		tone_list[5].play()
	if len(arr)>4:
		tone_list[4].play()
	if len(arr)>3:
		tone_list[3].play()
	if len(arr)>2:
		tone_list[2].play()
	if len(arr)>1:
		tone_list[1].play()


	# wait for time step to finish playing
	core.wait(dur, hogCPUperiod=dur)

	# get off time (just sample the first tone)
	offTime_s = onTime_s+tone_list[0].stopTime

	return onTime_s, offTime_s
# adjust pitch for a time step
def changePitch(arr,direction = 'increase',change_range = (0,6),coherence = 0.9):
	# this function takes a array of freq indices (describing a sound cloud) and adds some unit change of pitch to each tone. 1 unit change = 1 half note. 12 half notes is an octave. Coherence sets the number of tones that change pitch coherently on each time step. Remainder of tones are randomly resampled from the tone range. If params['change_tones_together'] == True, n each time step, it randomly draws a change value and applies it to all tones that are changing coherently. If False, it randomly generates a change value for each tone that is changing. 


	# Inputs 
	# arr ... array of freq indices
	# direction ... 'increase' or 'decrease'. Sets the overall direction of change
	# change_range ... tuple, sets range from which to draw values. The sign of both values should be positive (e.g (0,6)). It implements increases and decreases by reading the "direction" input
	# coherence ... proportion of tones that are changing in the concordance with the direction (increase or decrease)

	# Returns
	# arr ... modified array

	# create change_array. Absolute value is to ensure that we only are calculating the size of change, not the direction here.
	if params['change_tones_together'] == True:
		change_array = np.absolute(np.ones(len(arr))*(np.random.randint(low = change_range[0], high = change_range[1],size = 1)))
	else:
		change_array = np.absolute(np.random.randint(low = change_range[0], high = change_range[1],size = len(arr)))

	# select coherent indices
	num_coherent = np.round(coherence*len(arr)).astype('int')


	# change num_coherent indices of the arry based on the direction
	if direction == 'increase':
		arr[:num_coherent] = arr[:num_coherent] + change_array[:num_coherent] 
	elif direction == 'decrease':
		arr[:num_coherent] = arr[:num_coherent] - change_array[:num_coherent] 


	# resample the rest of the elements of the array from a random distribution
	arr[num_coherent:] = np.random.randint(params['toneRange_low'],high=params['toneRange_high'],size = (len(arr)-num_coherent))

	# change the sign of the coherent values to negative 1
	#change_array[:num_coherent] = -1*change_array[:num_coherent]

	# update the array
	#arr = arr + change_array

	# deal with values > toneRange_high or < toneRange_low, by reseting them to random value from -1 to 1
	overflow_idx = (arr > params['toneRange_high']) | (arr < params['toneRange_low'])
	arr[overflow_idx] = np.random.randint(params['toneRange_low'],high=params['toneRange_high'],size = np.count_nonzero(overflow_idx))

	return arr
# Sounds from file
def playOrient(dur = 0.5):
	tone = sound.Sound(value='orient.wav', secs=dur, volume = 1,hamming = True)
	# query clock time for on time
	onTime_s = core.monotonicClock.getTime()
	# play from buffer
	tone.play()
	# wait so sound finishes
	core.wait(dur)
	# get off time
	offTime_s = onTime_s+tone.getDuration()

	return onTime_s,offTime_s



def playCorrect(dur = 0.5):
	tone = sound.Sound(value='correct.wav', secs=dur, volume = 1,hamming = True)
	# query clock time for on time
	onTime_s = core.monotonicClock.getTime()
	# play from buffer
	tone.play()
	core.wait(dur)
	# get off time
	offTime_s = onTime_s+tone.getDuration()

	return onTime_s,offTime_s


def playWrong(dur = 0.5):
	tone = sound.Sound(value='wrong.wav', secs=dur, volume = 0.5,hamming = True)
	# query clock time for on time
	onTime_s = core.monotonicClock.getTime()
	tone.play()
	core.wait(dur)
	# get off time
	offTime_s = onTime_s+tone.getDuration()

	return onTime_s,offTime_s


# Run a Trial
def runTrial(trialDict, params):
	# inputs:
	#t_direction ... trial direction ('increase' or 'decrease'
	#coherence ... ranging from 0.5 to 1

	# output:
	# return updated trialDict

	# parse inputs
	direction = trialDict['direction']
	coherence = trialDict['coherence']

	if params['options_playOrientOnEachTrial'] == True:
		
		#play orient sound
		trialDict['orientOn_s'],trialDict['orientOff_s'] = playOrient(dur = params['dur_orient'])


	# clear container for keys
	keys_pressed = []

	# initialize keyboard buffer
	kb = keyboard.Keyboard(device = -1,waitForStart=True)# start clock
	kb.clock.reset()  # when you want to start RT timer from
	kb.clearEvents()
	kb.start() # start polling keyboard

	# STIM ON: play a random sound cloud (single time step)
	arr = np.random.randint(params['toneRange_low'],high=params['toneRange_high'],size = params['num_tones']) 
	trialDict['stimOn_s'],scratchtime = playSoundCloud(arr=arr, dur = params['dur_tonestep'],baseNote = params['baseNote'])


	# start changing pitch stimuli. Stream sound until a response key is pressed or if we time out (set by params['responseTimeLimit_s'])
	while (any(i in keys_pressed for i in params['buttonList_any'])==False) & (kb.clock.getTime() <= params['responseTimeLimit_s'][trialDict['block']]):
		arr = changePitch(arr,direction = direction,change_range = params['change_range'],coherence = coherence)
		scratchtime,offTime_s = playSoundCloud(arr=arr, dur = params['dur_tonestep'],baseNote = params['baseNote'])
		# check if keys have been pressed
		keys_pressed = kb.getKeys(params['buttonList_any'])

	kb.start() # stop polling keyboard

	# STIM OFF: stimulus has stopped playing, get most recent stimOff time
	trialDict['stimOff_s'] = offTime_s
	trialDict['wasShown'] = 1

	# figure out whether we timed out
	if len(keys_pressed) == 0:
		# this means we timed out as no response was given
		# response related data remain as "nan" ('buttonPress','choice','buttonPress_s','RT')

		trialDict['correct'] = 0 # this is an error trial
		trialDict['error'] = 1 # this is an error trial

		# present incorrect feedback
		trialDict['fbOn_s'],trialDict['fbOff_s'] = playWrong(dur = params['dur_fb'])
		
	elif len(keys_pressed)>0:
		# we made a response, lets process the button press

		# process key_press (first key pressed) in relation to trial type
		if trialDict['direction'] == 'increase':
			if (keys_pressed[0] in params['buttonList_inc']):

				# update trialDict
				# note: we use two independent methods to get RT and buttonPress_s. RT should correlate with buttonPress_s - stimOn_s 
				trialDict['correct'] = 1
				trialDict['error'] = 0
				trialDict['buttonPress'] = keys_pressed[0].name
				trialDict['choice'] = 'increase'
				trialDict['buttonPress_s'] = keys_pressed[0].tDown - kb.clock.getLastResetTime()
				trialDict['RT'] =keys_pressed[0].rt

				print('Correct! pitch is increasing with coherence = ',trialDict['coherence'],' RT = ', keys_pressed[0].rt)

				# play feedback
				trialDict['fbOn_s'],trialDict['fbOff_s'] = playCorrect(dur = params['dur_fb'])

			elif (keys_pressed[0] in params['buttonList_dec']):

				# update trialDict
				trialDict['correct'] = 0
				trialDict['error'] = 1
				trialDict['buttonPress'] = keys_pressed[0].name
				trialDict['choice'] = 'decrease'
				trialDict['buttonPress_s'] = keys_pressed[0].tDown - kb.clock.getLastResetTime()
				trialDict['RT'] =keys_pressed[0].rt

				print('Incorrect! pitch is increasing with coherence = ',trialDict['coherence'],' RT = ', keys_pressed[0].rt)

				# play feedback
				trialDict['fbOn_s'],trialDict['fbOff_s'] = playWrong(dur = params['dur_fb'])

		elif trialDict['direction'] == 'decrease':
			if (keys_pressed[0] in params['buttonList_dec']):

				# update trialDict
				trialDict['correct'] = 1
				trialDict['error'] = 1
				trialDict['buttonPress'] = keys_pressed[0]
				trialDict['choice'] = 'decrease'
				trialDict['buttonPress_s'] = keys_pressed[0].tDown - kb.clock.getLastResetTime()
				trialDict['RT'] =keys_pressed[0].rt


				print('Correct! pitch is decreasing with coherence = ',trialDict['coherence'],' RT = ', keys_pressed[0].rt)

				trialDict['fbOn_s'],trialDict['fbOff_s'] = playCorrect(dur = params['dur_fb'])	

			elif (keys_pressed[0] in params['buttonList_inc']):

				# update trialDict
				trialDict['correct'] = 0
				trialDict['error'] = 1
				trialDict['buttonPress'] = keys_pressed[0]
				trialDict['choice'] = 'increase'
				trialDict['buttonPress_s'] = keys_pressed[0].tDown - kb.clock.getLastResetTime()
				trialDict['RT'] =keys_pressed[0].rt


				print('Incorrect! pitch is decreasing with coherence = ',trialDict['coherence'],' RT = ', keys_pressed[0].rt)
				trialDict['fbOn_s'],trialDict['fbOff_s'] = playWrong(dur = params['dur_fb'])

	# send a SYNC pulse 
	if params['options_sendSYNC'] == True:
		trialDict['TTL1sent_s'] = core.monotonicClock.getTime() 
		params['SYNC_deviceObj'].getFeedback(u3.DAC0_8(params['SYNC_pulse_val']))
		params['SYNC_deviceObj'].getFeedback(u3.DAC0_8(params['SYNC_zero_val']))
	
		trialDict['TTL2sent_s'] = core.monotonicClock.getTime() 
		params['SYNC_deviceObj'].getFeedback(u3.DAC0_8(params['SYNC_pulse_val']))
		params['SYNC_deviceObj'].getFeedback(u3.DAC0_8(params['SYNC_zero_val']))
	
		trialDict['TTL3sent_s'] = core.monotonicClock.getTime() 
		params['SYNC_deviceObj'].getFeedback(u3.DAC0_8(params['SYNC_pulse_val']))
		params['SYNC_deviceObj'].getFeedback(u3.DAC0_8(params['SYNC_zero_val']))

		# wait for sync pulses to finish
		core.wait(0.5)

	# return updated trialDict
	return trialDict

# Trial-related functions
def emptyTrial(params):
	#subfunction to generate a dictionary with empty fields (nans)

	trialDict = {}
	for tf in params['trial_fields']:
		trialDict[tf] = np.nan

	return trialDict 

def fillTrial(params,trialDict,trialInBlock,block,coherence,direction):
	# populate trialDict with basic trial features
	trialDict['block'] = block
	trialDict['coherence'] = coherence
	trialDict['direction'] = direction
	trialDict['trialInBlock'] = trialInBlock

	return trialDict


# subfunction to generate a trial list within a block
def makeBlockTrials(params,block):
	# trial counter (within block)
	trialInBlock = 0

	# create a block list
	block_list = []

	# loop over coherence
	for	c in params['coherence_list']:
		# loop over directions
		for	d in params['direction_list']: 
			# run num trials
			for t in np.arange(0,params['num_trials']):
				# update within block counter
				trialInBlock+=1

				# make an empty trial dictionary
				trialDict = emptyTrial(params)

				# fill in trial
				trialDict = fillTrial(params=params,trialDict=trialDict,trialInBlock=trialInBlock,block=block,coherence=c,direction=d)

				# append to list
				block_list.append(trialDict)

	# shuffle in place within block
	np.random.shuffle(block_list)

	# return block list
	return block_list

def generateTrialList(params):
	# generate trial list - list of dictionaries. Calls above functions (makeBlockTrials, emptyTrial, and fillTrial) This can be converted to a pandas dataframe later. Shuffle block list in place. Shuffle trials within each block.

	# generate empty list that will hold trial data for the session
	trialDict_list = []

	# randomize block list order in place
	np.random.shuffle(params['block_list'])

	# loop through blocks:
	for b in params['block_list']:
		trialDict_list.extend(makeBlockTrials(params,b))


	# shuffle all trials across blocks
	if params['options_shuffleTrialsAcrossBlocks'] == True:
		np.random.shuffle(trialDict_list)

	# return list of dictionaries
	return trialDict_list

def initializeLabjack(params):
	# Initialize labjack device object and get calibration data. 
	if params['options_sendSYNC'] == True:
		try:
			params['SYNC_deviceObj'] = u3.U3()
			params['SYNC_deviceObj'].getCalibrationData()
			
			params['SYNC_pulse_val'] =  params['SYNC_deviceObj'].voltageToDACBits(params['SYNC_volt'], dacNumber = 0, is16Bits = False)
			params['SYNC_zero_val'] =  params['SYNC_deviceObj'].voltageToDACBits(0, dacNumber = 0, is16Bits = False)


			print('Sync pulses are sent from the DAC0 channel. Connect cathode (red wire) to DAC0 and annode (black wire) to ground.')

		except:
			print('Unable to open LABJACK. Check if it is connected. If not using sync pulses, set "options_sendSYNC" to False')
			core.quit()

	# returns updated params
	return params

#### RUN TASK
# GENERATE SUBJECT AND SESSION ID AND MAKE DIRECTORIEs
params = mkDirs(params)

# try this

# INITIALIZE LABJACK
params = initializeLabjack(params)


# DISPLAY FIXATION CROSS
if params['options_showFixation'] == True:
	#open a window and display a fixation cross
	# open window
	win = visual.Window()

	# create a text Object
	msg = visual.TextStim(win, text="Hello World!")

	# draw the message in the draw buffer
	msg.draw()

	# display it on the screen
	params['fixOn_s'] = win.flip() # this records when the fixation cross was displayed at the beginning of the session


# RUN THROUGH TRIALS. Will pick up from last shown trial if we have already run this subject/session before. 

# check for a saved trialDict_list
params['savefilepath'] = params['sessDir']+'/'+'taskData'
if os.path.exists(params['savefilepath']) == True:
	# load task data
	trialDict_list = load_pickle(params['savefilepath'])

	# find tStart based on how many trials have been presented
	# read 'wasShown' attribute to see which trials were shown
	wasShown = pd.DataFrame(trialDict_list)['wasShown'].to_numpy()

	# identify last trial that was shown, we will pick up from here
	tStart = np.nonzero(np.isnan(wasShown)==False)[0][-1] 

else:
	# There is no saved task data
	# create a fresh list of trials and set tStart to 0
	trialDict_list = generateTrialList(params)
	tStart = 0

# loop through trial list
for t in np.arange(tStart,len(trialDict_list)):

	# print block
	print(trialDict_list[t]['block'])

	# check if we are in a block design, so we can cue each block
	if params['options_shuffleTrialsAcrossBlocks'] == False:

		# we are in a block design, cue each block start
		if t == 0:
			#this is the first trial, ask if we can start block
			trialDict_list[t]['orientOn_s'],trialDict_list[t]['orientOff_s'] = playOrient(dur = params['dur_orient'])
			input('Press ENTER to start '+trialDict_list[t]['block']+' block')

		elif trialDict_list[t]['block']!=trialDict_list[t-1]['block']:
			trialDict_list[t]['orientOn_s'],trialDict_list[t]['orientOff_s'] = playOrient(dur = params['dur_orient'])
			#this is the first trial, ask if we can start block
			playOrient()
			input('Press ENTER to start '+trialDict_list[t]['block']+' block')


	# run a trial
	trialDict_list[t] = runTrial(trialDict_list[t],params)

	# save a pickle here
	save_pickle(obj = trialDict_list, fpath = params['savefilepath'])


# once we are done running trials,
# convert to dataframe
task_df = pd.DataFrame(trialDict_list)
task_df.index.name = 'trial'

# write CSV file
task_df.to_csv(path_or_buf = params['sessDir']+'/data.csv')

# write config file
config_df = pd.Series(params)
config_df.index.name = 'parameter'
config_df.name = 'value'
config_df.to_csv(path_or_buf = params['sessDir']+'/config.csv')

# wait for clean up
core.wait(3)


if params['options_showFixation'] == True:
	#close window
	win.close()

