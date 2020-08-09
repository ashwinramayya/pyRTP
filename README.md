# pyRTP
Psychopy random tone pitch task as described in Mulder et al 2013.
written by Ashwin Ramayya (ashwinramayya@gmail.com)

Dependencies:
python (version 3.6 recommended) 
psychopy https://www.psychopy.org/ 
psychtoolbox
numpy 
pandas

matplotlib (for report generation)


### To Run experiment:
In terminal, go to experiment folder ('pyRTP')
$ python pyRTP.py

enter subject id and session number when promted. It will auto-generate a unique ID if no subject id is entered. It will automatically generate the next session number if no session id is entered (e.g., it will generate 1 if session0 folder is already created). If the program is closed in the middle of a session, you can resume the session in progress by re-tentering the subject and session id


### To generate a behavioral report:
In terminal, go to experiment folder ('pyRTP')
$ python pyRTP_analysis.py

enter subject ID and session number. Will generate figures using macosx backend, and will save a multi-page PDF
completed session if the subject and session ids are associated with a p prompts. If nothing


References:
Mulder, M. J., Keuken, M. C., van Maanen, L., Boekel, W., Forstmann, B. U., & Wagenmakers, E. J. (2013). The speed and accuracy of perceptual decisions in a random-tone pitch task. Attention, Perception, & Psychophysics, 75(5), 1048-1058.
