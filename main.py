import parselmouth
from parselmouth import praat
import plotly.express as px
from numpy import average
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from itertools import islice
#______________________________________________________________________________________________#

file = '17vowelstest5.wav'
decible_threshold = 55  # given the nature of the words given, the decible of the /h/ sound and /d/ sounds will be far quieter than the nuclear vowel
silence_tolerance = 0.2 # minimum length between two sounds to be considered new words 
vowel_specificity = 5 #how much of the beginning and end of a sound is cut off 

roller = 10
#1-10 how smoothed should the diphthongs be? default 7
points = 3 #how many points should be created from the diphthong tragectories, default 3
schwa_len = 3 #how long the schwa sample is, default 3 
num_reps = 3  #how many times the words are repeated in the file default 3


def acquire_formants(file_path):
  f1_list, f2_list, f3_list = [], [], []

  f0min, f0max = 75, 300
  sound = parselmouth.Sound.extract_part(parselmouth.Sound(file_path))
  pointProcess = praat.call(
      sound, "To PointProcess (periodic, cc)", f0min, f0max)
  numPoints = praat.call(pointProcess, "Get number of points")

  formants = praat.call(sound, "To Formant (burg)", 0, 5, 5500, 0.1, 50)

  for point in range(0, numPoints):
      point += 1
      t = praat.call(pointProcess, "Get time from index", point)
      f1 = praat.call(formants, "Get value at time", 1, t, 'Hertz', 'Linear')
      f2 = praat.call(formants, "Get value at time", 2, t, 'Hertz', 'Linear')
      f3 = praat.call(formants, "Get value at time", 3, t, 'Hertz', 'Linear')
      f1_list.append(f1)
      f2_list.append(f2)
      f3_list.append(f3)

  return f1_list, f2_list, f3_list

def get_words(file_speaker):
    ##using the intensity of the sound, we will find where the words are said,

    snd = parselmouth.Sound(file_speaker)
    intensity = snd.to_intensity(time_step=0.01)
    int_vals = intensity.values.T
    int_t = intensity.xs()
    time_stamps = []

    for i in range(len(int_vals)):  # going through the decible list

        if int_vals[i] >= decible_threshold:  # if the sound is loud enough
            t = int_t[i]  # retrieve the time stamp
            time_stamps.append(t)  # add time stamp to list

    time_stamps.append('stop')
    word_list = []
    word = []

    for i in range(0, len(time_stamps)):
        if (time_stamps[i+1] == 'stop'):  # stops before oob, lists of variable lengths
            word.append(time_stamps[i])
            word_list.append(word)
            break

        # if the diff between a timestamp and the next one is greater than 0.2s, we know silence has occurred
        elif (time_stamps[i+1] - time_stamps[i] >= silence_tolerance):
            word.append(time_stamps[i])

            if (len(word) > 2):  # if it's long enough
                word_list.append(word)  # append it
            word = []  # clear the word

        else:
            word.append(time_stamps[i])

    wl = []
    for words in word_list:
        word = [words[0], words[-1]]
        wl.append(word)
    return wl

def get_word_formants(word_list):
    word_dict = {}
    count = 0

    for word in word_list:
        f1_list, f2_list, f3_list = [], [], []
        count += 1
        sound = parselmouth.Sound.extract_part(
            parselmouth.Sound(file_path), from_time=word[0], to_time=word[1])
        formants = praat.call(sound, "To Formant (burg)", 0, 5, 5500, 0.01, 50)

        f0min, f0max = 75, 310

        pointProcess = praat.call(
            sound, "To PointProcess (periodic, cc)", f0min, f0max)
        numPoints = praat.call(pointProcess, "Get number of points")

        for point in range(0, numPoints):
            point += 1
            t = praat.call(pointProcess, "Get time from index", point)
            f1 = praat.call(formants, "Get value at time",
                            1, t, 'Hertz', 'Linear')
            f2 = praat.call(formants, "Get value at time",
                            2, t, 'Hertz', 'Linear')
            f3 = praat.call(formants, "Get value at time",
                            3, t, 'Hertz', 'Linear')

            f1_list.append(f1)
            f2_list.append(f2)
            f3_list.append(f3)

        word_dict[count] = [np.array(f1_list[vowel_specificity:-vowel_specificity]), 
                            np.array(f2_list[vowel_specificity:-vowel_specificity]), 
                            np.array(f3_list[vowel_specificity:-vowel_specificity]), 
                            np.array(f1_list[:schwa_len]), 
                            np.array(f2_list[:schwa_len]), 
                            np.array(f3_list[:schwa_len])]
        print("analysis", count, "of", len(word_list), "complete!", end = '\r')

    return word_dict

def formant_averager(word_dict):
    mono_dict = {}
    diph_dict = {}
    shwa_dict = {}
    count = 0

    # print(word_dict[1][0]) #this is [f1 arr, f2 arr, f3 arr] for first word
    #gets averages of monophtongs
    for i in range(1, len(word_dict)):  # i is the word elicitations 1-51
        count += 1
        word = word_dict[i]

        wf1, wf2, wf3, sf1, sf2, sf3 = word[0], word[1], word[2], word[3], word[4], word[5]
        awf1, awf2, awf3 = average(wf1), average(wf2), average(wf3)
        schwaf1, schwaf2, schwaf3 = average(sf1), average(sf2), average(sf3)

        shwa_dict[count] = [schwaf1, schwaf2, schwaf3]
        mono_dict[count] = [awf1, awf2, awf3] #average of 
        diph_dict[count] = [wf1, wf2, wf3] #full track of all three formants 

    sound_avgs = {}
    count = 0

    #only useful for the monophtongs
    # goes in chunks of 3 through the avgs_dict to find the average of the three elicitations, 
    for i in range(1, len(mono_dict)-1, num_reps):
        count += 1
        sound_avg = np.mean(np.array([mono_dict[i], mono_dict[i+1], mono_dict[i+2]]), axis=0)
        sound_avgs[count] = sound_avg
        
    #within sound_avgs, this overwrites vowels 10-16 
    for i in range(10, len(sound_avgs)+1): 
        sound_avgs[i] = diph_dict[i]

    #the last sound in the recording is the schwa, so it needs to be processed
    #schwa just adding the last one instead of fixing oob error lmao
    sound_avgs[count+1] = np.mean(np.array([shwa_dict[i-4], shwa_dict[i-3], shwa_dict[i-2]]), axis=0)

    return sound_avgs

def means_of_slices(i, slice_size):
    iterator = iter(i)
    while True:
        slice = list(islice(iterator, slice_size))
        if slice:
            yield sum(slice)/len(slice)
        else:
            return
def plot_vowels(sound_avgs): 
    f1_vals, f2_vals, f3_vals = [], [], []
    vowels = ['ə', 'i', 'ɪ', 'ɛ', 'æ', 'ɑ', 'ɔ', 'ʌ', 'u', 'ʊ', 'aʊ', 'oɪ', 'aɪ', 'oʊ', 'aɪ-t', 'eɪ', 'ɚ']
    monos = np.array(['ə', 'i', 'ɪ', 'ɛ', 'æ', 'ɑ', 'ɔ', 'ʌ', 'u', 'ʊ']) 
    diphs = ['aʊ', 'oɪ', 'aɪ', 'oʊ', 'aɪ-t', 'eɪ', 'ɚ']
    
    #create x,y for monophthongs 
    for i in range(1, len(sound_avgs)+1):
        f1_vals.append(sound_avgs[i][0])
        f2_vals.append(sound_avgs[i][1])
        f3_vals.append(sound_avgs[i][2])
        
    mx, my, mz = np.array(f2_vals[-1:] + f2_vals[:9], dtype=object), np.array(f1_vals[-1:] + f1_vals[:9], dtype=object), np.array(f3_vals[-1:] + f3_vals[:9], dtype=object)
    dx, dy, dz = np.array(f2_vals[9:16], dtype='object'), np.array(f1_vals[9:-1],dtype=object), np.array(f3_vals[9:-1],dtype='object')
    
    #using rolling avgs 
    diph_df = pd.DataFrame({'labels':diphs, 'dx':dx, 'dy':dy, 'dz':dz})
    for i in range(len(dx)):
        roll = round(len(dx[i])/roller)*4
        rollx = pd.Series(dx[i]).rolling(roll).mean()
        rolly = pd.Series(dy[i]).rolling(roll).mean()
        rollz = pd.Series(dz[i]).rolling(roll).mean()

        dx[i], dy[i], dz[i] = list(rollx),list(rolly),list(rollz)
        
        
        
      #uses slice window averages to get n-points to graph 
    # for i in range(len(dx)):
    #     slice_len = round(len(dx[i])/points)
        
    #     meansx = list(means_of_slices(dx[i], slice_len))
    #     meansy = list(means_of_slices(dy[i], slice_len))
    #     meansz = list(means_of_slices(dz[i], slice_len))
        
    #     dx[i], dy[i], dz[i] = meansx, meansy, meansz
        
        # print(len(dx[i]), len(dy[i]))
        
        
    mono_df = pd.DataFrame({'labels':monos, 'mx': mx, 'my':my, 'mz':mz})
   
     #plotting monos
    mono_df["mx"] = mono_df["mx"].astype(float)
    mono_df["my"] = mono_df["my"].astype(float)
    fig = px.scatter(mono_df, 
                     x='mx', 
                     y='my', 
                     color ='my', 
                     text="labels", 
                     size_max=60
                     )
    fig.update(layout_coloraxis_showscale=False)
    #plotting diph trajectories
    for i in range(len(dx)):
        fig.add_trace(go.Scatter(x=dx[i], y=dy[i],
                        mode='lines',
                        opacity=0.5,
                        name=diphs[i],
                        text=diphs[i]))
    
    #adding last point 
    for i in range(len(dx)):
        fig.add_trace(go.Scatter(x=np.array([dx[i][-1]]), y=np.array([dy[i][-1]]),
                        mode='text+markers',
                        name=diphs[i],
                        text=diphs[i]))
    
    fil = file.removesuffix('.wav')
    title = fil + ' Vowel Space'
    fig.update_traces(textposition='top center')
    fig.update_layout(yaxis = dict(autorange="reversed"),
                      xaxis = dict(autorange="reversed"),
                      title=title,
                      xaxis_title="F2",
                      yaxis_title="F1"
                      )
    fig.update_layout(xaxis = {"mirror" : "allticks", 'side': 'top'}, yaxis={"mirror" : "allticks", 'side': 'right'})
    
    


    fig.show()    
    return


file_path = 'c:/Users/bridg/Documents/GitHub/form-a-formant/' + file
# formants = acquire_formants(file_path)
# formants = add_formants(acquire_formants(file_path))

word_list = get_words(file_path)

word_formants = get_word_formants(word_list)

formant_averages = formant_averager(word_formants)

vowels = plot_vowels(formant_averages)


