# Project Assignment

Write code to find (if any) anomalies from data in **anomaly_data.csv**. The data contains two columns. The first column is the employee identifier. The second column is the datetime the employee entered/exited the building. You may use any programming language. It's expected this project takes up to 5 hours to complete. Please upload your code to your personal Github account and provide instructions on how to run it. Email us the link to your project when you are done!


To run the code, the following packages are required:
sklearn - 0.19.1
pandas - 0.21.0
numpy - 1.13.3

Then, just place anomaly_data.csv in the same folder as 'Functional Code.py' and execute 
```python
python 'Functional Code.py'
```
Overall, I took two approaches to find anomalies- business rules and machine learning. Each badge swipe is flagged based on these rules and output to anomalies.csv. The final flags for badge swipes are:
Extreme- coming in very early or leaving very late

badadmin- having minute time stamps overwhelmingly ending in 00, 15, 30, or 45. While not present in the data, this could be evidence the data was not genuinely generated and/or generated by an admin

ghosts- coming in on days when extremely few other people are present

cluster_pick- at least one clustering method identified the observation as out of place

forest_pick- isolation forests identified this observation as an outlier

neighbor_pick- local outlier factor identified this observation as an outlier 

Number of Flags- count of flags that a person was marked as 'yes' for

There are also person-level tests for abnormalities. While only one person fails these tests in this dataset, their Person Id is written out to potential_bad_actors.csv. The idea behind these person level tests is that if a person is not swiping their badge both in and out regularly (as occurred in our data) or who are rogue (only coming in a very small number of times), then they should be inspected more closely as individuals. 

Future to-dos:

-Explicitly forecast each swipe timestamp using a neural network

-Form a network representation of workers based on people having close 'second' swipes (likely meaning going to lunch or carpooling together) and identify friendless people (insufficient data in this dataset). Similarly, if one person is a bad actor, you might want to increase your interest in people they seem to be socializing with. 

-Form rolling person-specific thresholds for what is late/early and let those moving averages update themseleves over a longer timeline This would be especially important if the data was long enough to exhibit seasonal weather changes/daylight savings time. 

-Merge badge data with other time series like local weather as that can be a feature that impacts arrival/departure times

