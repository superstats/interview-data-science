
# coding: utf-8

#import needed packages
import sklearn
from sklearn.cluster import DBSCAN
from sklearn import metrics
from sklearn.cluster import Birch
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt

#take in the data 
df_raw = pd.read_csv('./anomaly_data.csv')

#generating consistent output for random seeds 
rng = 45

#give the date a datetime data type
df_raw['Door Access DateTime'] = pd.to_datetime(df_raw['Door Access DateTime'])

#create features for future use 

df_features = df_raw.copy(deep=True)

df_features['Month'] = df_features['Door Access DateTime'].dt.month 
df_features['Day'] = df_features['Door Access DateTime'].dt.day
df_features['MonthDay'] = df_features['Month'].map(str)+ "/" + df_features['Day'].map(str)
df_features['Hour'] = df_features['Door Access DateTime'].dt.hour
df_features['DayofWeek'] = df_raw['Door Access DateTime'].dt.dayofweek
df_features['Minute'] = df_features['Door Access DateTime'].dt.minute

#get the first and last time there was a login or out for the day
df_startend = df_features.groupby(['MonthDay', 'Person Id']).agg(['min', 'max'])['Door Access DateTime'].reset_index()
df_features = pd.merge(df_features, df_startend , on = ['MonthDay', 'Person Id'])

#create a normalized dataset for clustering purposes
#chose to drop person ID but alternative would be to use person level information as part of the clustering
#but at scale, this would produce a very wide dataframe so decided not to 
df_cluster = df_features.drop(['MonthDay', 'min', 'max', 'Person Id',  'Door Access DateTime'], axis=1).copy(deep=True)
df_cluster = pd.merge(df_cluster, pd.get_dummies(df_cluster.DayofWeek), left_index = True, right_index=True)
df_cluster = df_cluster.drop(['DayofWeek'], axis=1)
X = StandardScaler().fit_transform(df_cluster)

#User IDs tend to be sequential so print an error message if the digits are non-consecutive
#This may warrant additional follow-up with the data owner or could be fine (such as our test data case)
missing_IDs = (df_raw['Person Id'].nunique() - (df_raw['Person Id'].max() - df_raw['Person Id'].min()+1))
if missing_IDs != 0:
    print('If the userIDs passed were consecutive, we would espect to see ' + str(missing_IDs) + ' more/fewer than we see here.')

def rogue (df_raw, min_visit):
    """Returns a list of people who have come less than a minimum number of times."""
    rogue = pd.DataFrame
    rogue = pd.DataFrame(df_raw['Person Id'].value_counts()<10)
    rogue = rogue[rogue['Person Id']==True]
    return rogue

def badadmin(df_features, multiple):
    """Looks for observations that seem like they could have been generated by an admin because the minutes
    are disproportionately 'easy' ones like 0, 15, 30, or 45 for a particular person"""
    pct_0 = pd.DataFrame()
    pct_0 = df_features[df_features['Minute'].isin(['0','15','30','45'])].groupby('Person Id').count()/df_features.groupby('Person Id').count()
    pct_0 = pct_0[pct_0.iloc[:,0]>(4*multiple)/60]
    return pct_0

#flags the entire day as strange if either you come to work before 7 or leave after 8
def extreme_timestamp(df_features, min_quantile, max_quantile):
    """Returns a list of people who have come extremely early or late."""
    extremes = pd.DataFrame()
    early = df_features['Door Access DateTime'].dt.hour.quantile(min_quantile)
    late = df_features['Door Access DateTime'].dt.hour.quantile(max_quantile)
    extremes = df_features[(df_features['min'].dt.hour<early) | (df_features['max'].dt.hour>late)]
    return extremes

def ghost_town(df_features, multiple):
    ghost_town = pd.DataFrame()
    """Returns a list of people who come when very few other people are in the office
    with the date they came as the index."""
    daily_attendance = df_features.groupby('MonthDay').count()['Person Id']
    df_attendance = pd.DataFrame(daily_attendance)
    df_attendance = pd.merge(df_attendance,df_features, left_index=True, right_on='MonthDay') 
    cutoff = df_attendance['Person Id_x'].mean()/10
    ghost_town = df_attendance[df_attendance['Person Id_x']<cutoff]
    return ghost_town

def missed_swipe(df_features, multiple):
    """Returns a list of people who have days with odd numbers of swipes more than X
    multiple times the average among missed swipers"""
    df_miss = pd.DataFrame()
    final = []
    missed_swipe = df_features.groupby(['MonthDay', 'Person Id']).count()['Door Access DateTime']%2
    missed_swipe = missed_swipe[missed_swipe>0]
    miss_list = missed_swipe.groupby('Person Id').sum()
    miss_list = miss_list[miss_list>(multiple*miss_list.mean())]
    missing = pd.DataFrame(miss_list).index[0]
    final.append(missing)
    return final

def cluster(X, skCluster, pct):
    """Iterates through clustering methods and returns a list of odd timestamps"""
    cluster_outlier = []
    for method in skCluster:
        clf = method.fit(X)
        labels = clf.labels_
        labels_unique = np.unique(labels)
        n_clusters_ = len(labels_unique)
        for i in labels_unique:
            if np.where(clf.labels_ == i)[0].shape[0] < X.shape[0]*pct:
                cluster_outlier = set(list(cluster_outlier)) | set(list(np.where(clf.labels_ == i)[0]))
    return cluster_outlier

def outlier_forest(X, IForest):
    """Uses an isolation forest to identify anomalous badge swipes"""
    iforest_outlier = []
    IForest.fit( X)
    I_Pred = IForest.predict(X)
    df_ipred = pd.DataFrame(I_Pred, columns={'Outlier'})
    iforest_outlier = set(df_ipred[df_ipred['Outlier']==-1].index) | set(iforest_outlier)
    return iforest_outlier

#make final dataframe
df_final = df_raw.copy(deep=True)

#final function calls at the end of the script
#rules based methods
#return individual persons rather than swipes in/out
rogue_obs = rogue(df_raw, min_visit = 10)
non_swipers = missed_swipe(df_features, multiple = 1)

#compiled list of individually suspicious people  
bad_actors = set(rogue_obs.values.tolist()) | set(non_swipers)

#returns a list of timestamps 
extremes = extreme_timestamp(df_features, min_quantile =.005, max_quantile=.995)
badadmin = badadmin(df_features, 4)
ghosts = ghost_town(df_features, multiple = 10)

#adding to final dataframe
df_final['Extreme'] = df_final.index.isin(extremes.index)*1
df_final['badadmin'] = df_final.index.isin(badadmin.index)*1
df_final['ghosts'] = df_final.index.isin(ghosts.index)*1

#compiled list of worrisome swipes in/out of the building 
worrisome_swipes = set(list(extremes.index)) | set(list(badadmin.index)) | set(list(ghosts.index))

#clusering methods
brc = Birch(branching_factor=50, n_clusters=None, threshold=1.5,compute_labels=True)
db = DBSCAN(eps=.3, min_samples=2)

skCluster = { db, brc}
cluster_picks = cluster(X, skCluster, pct=.001)

df_final['cluster_pick'] = df_final.index.isin(cluster_picks)*1

IForest = IsolationForest( contamination=.001, random_state =rng)
forest_pick = outlier_forest(X, IForest)

df_final['forest_pick'] = df_final.index.isin(forest_pick)*1

#one liner for local outlier detection so a function is gratiutous here
X_outliers  = LocalOutlierFactor(n_neighbors=100, contamination =.001)
df_outlier = pd.DataFrame(X_outliers.fit_predict(X), columns={'Local Outlier'}) 

neighbor_pick = df_outlier[df_outlier['Local Outlier']==-1].shape

df_final['neighbor_pick'] = df_final.index.isin(neighbor_pick)*1

#combine all of the results of the functions to get good stuff
ml_picks = set(forest_pick) | set(neighbor_pick) | set(cluster_picks)

all_anomaly = set(ml_picks) | set(worrisome_swipes)
print(str(len(all_anomaly)) + ' uniquely anomalous swipes detected. CSVs written to this folder with full history and reasons.')

#create total flags for prioritization 
df_final['Number of Flags'] = df_final.iloc[:,2:8].sum(axis=1) 

#writes questionable timestamp of swipes to CSV sorted by descending number of flags
df_final.loc[all_anomaly].sort_values(by = 'Number of Flags', ascending=False).to_csv('anomalous_swipes.csv', index=False)

#writes potentially, but not necessarily, overlapping list of bad actors
#list to CSV that focuses on person-level behavior rather than their individual
#swipes
df_bad = pd.DataFrame(np.array(list((bad_actors))))
df_bad.to_csv('potential_bad_actors.csv', index=False, header=False)

