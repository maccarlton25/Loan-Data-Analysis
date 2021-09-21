# -*- coding: utf-8 -*-
"""TeamAssignment2_MattCURRENT.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1MPyoUZtFQpwzdbLtleEZ8MjLWp1xMdJz

# Team Mu Assignment 2
### Matt Simcox, Mayson Snavely, Mac Carlton, Abdier Guadalupe, Ujesh Regmi, Fehmi Zengince

# Our Question: 
## By examining the accepted loan data from P2P lending company Lending Club, can we generate a competetive advantage for our client by finding specific variables to target to lower risk and increase capital gains?

## Imports and Initial Import of Data
"""

# Commented out IPython magic to ensure Python compatibility.
# %ls

# imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
import seaborn as sns

"""We're only going to import the accepted files for analysis, as those are going to be the ones we can invest in.
 - pd.read_csv() has a paramter usecols that we can use to import more less columns (reduce dimensionality). We will use this after discovering which columns we want to focus on
 - We need to limit the size and scope of the data in order to analyze it well/more efficiently
"""

# importing data, this cell will take a while to import all the data
df = pd.read_csv("accepted_2007_to_2018Q4.csv")
print(df.shape)
df.head()

"""Initial thoughts:
 * Grade and sub_grade may be useful, but it's based on Lending Club's analysis not ours - can be used to verify what we think of risk/reward.
   - These variables also encode the interest rate, lower grades means higher interest rate.
   - To find competetive advantage, see what isn't represented and see if the risk/reward may be higher in some cases (ex low grade loans with high payoffs vs high grade loans with low payoffs)
   - https://www.lendingclub.com/foliofn/rateDetail.action
 * member_id may not matter unless calculating per person risk - one person can have multiple loans
 * columns about hardships/settlements are NaN unless hardship or settlement is present in the loan

## Data Cleaning

First we will address the mixed types DtypeWarning presented by the kernel for columns 0, 19, 49, 59, 118, 129, 130, 131, 134, 135, 136, 139, 145, 146 and 147
"""

warningCols = df.iloc[:, [0, 19, 49, 59, 118, 129, 130, 131, 134, 135, 136, 139, 145, 146, 147]]
warningCols

"""Observations:
 - id has some string data in it (total amount funded in policy code 1, 2: there is also a policy_code var)
 - the rest are categorical, int or float with NaN values
 - The last two rows seem like summaries
"""

# Checking for more ids with string data (summary rows like the last two) and removing them
df['id'] = df['id'].astype('str').str.upper()
idAlphaMask = df['id'].str.isupper()
df = df[~idAlphaMask]
df['id'] = df['id'].astype('int')

# Find object (mixed) type dtypes and set them to the correct data type. Also, drop columns that we won't need to analyze
objectTypes = df.dtypes == 'object'
df.dtypes[objectTypes]

# Dropping columns useless to analysis (url doesn't matter, policy code is irrelevant and 
# desc only has what the loan is for, purpose is better. addr_state and zip are redundant)
df.drop(columns = ['url', 'policy_code', 'desc', 'addr_state'], inplace = True)

# Assigning new data types as appropriate (from variable description spreadsheet)
df['term'] = df['term'].astype('category')
df['grade'] = df['grade'].astype('category')
df['sub_grade'] = df['sub_grade'].astype('category')
df['emp_title'] = df['emp_title'].astype('str')
df['home_ownership'] = df['home_ownership'].astype('category')
df['verification_status'] = df['verification_status'].astype('category')
df['loan_status'] = df['loan_status'].astype('category')
df['pymnt_plan'] = df['pymnt_plan'].astype('category')
df['purpose'] = df['purpose'].astype('category')
df['title'] = df['title'].astype('category')
df['initial_list_status'] = df['initial_list_status'].astype('category')
df['application_type'] = df['application_type'].astype('category')
df['verification_status_joint'] = df['verification_status_joint'].astype('category')
df['hardship_flag'] = df['hardship_flag'].astype('category')
df['hardship_type'] = df['hardship_type'].astype('category')
df['hardship_reason'] = df['hardship_reason'].astype('category')
df['hardship_status'] = df['hardship_status'].astype('category')
df['hardship_loan_status'] = df['hardship_loan_status'].astype('category')
df['disbursement_method'] = df['disbursement_method'].astype('category')
df['debt_settlement_flag'] = df['debt_settlement_flag'].astype('category')
df['settlement_status'] = df['settlement_status'].astype('category')
df['zip_code'] = df['zip_code'].astype('str')

# Datetime objects
dateCols = ['issue_d','earliest_cr_line', 'last_pymnt_d', 'next_pymnt_d', 'last_credit_pull_d', 'sec_app_earliest_cr_line',
           'hardship_start_date', 'hardship_end_date', 'payment_plan_start_date', 'debt_settlement_flag_date', 'settlement_date']
df[dateCols] = df[dateCols].apply(pd.to_datetime)

# For emp_length, could change it to int but it is easier to encode it as a category
df['emp_length'] = df['emp_length'].astype('category')

"""Next we will also investigate NaN values for fields like member_id which seem empty and remove them if so"""

# Find columns where all values are NaN
naSeries = df.isna().sum()
naSeriesMask = naSeries == len(df)
dropList = naSeries[naSeriesMask].index.values
dropList

"""Right off the bat we can get rid of member_ids since there is no data available for us to use. **We won't be able to calculate extended risk for those applying for multiple loans.** Other fields may be sparce but there is data available for us to use"""

df.drop(dropList, axis = 1, inplace = True)
# df.shape

"""I also noticed sub_grade had redundant data to grade, will drop the grade column"""

df.drop(columns = ['grade'], inplace = True)
# df.shape

"""Our data should be clean from here but not yet one-hot encoded due to the sheer size of the dataset. **We will attempt dimensionality reduction to select important feature variables before one-hot encoding.** This will be completed by only keeping response variables with a high correlation to the target variable rather than through machine learning in order to better answer the question with a "white box" process

## Defining Risk vs Reward: our target variable
We can determine risk by examining these accepted loans and seeing which fields can predict hardships, late payments, or defaults. While you can still make money on defaulting loans, they are inherantly more risky and therefore may not provide a competative advantage for us to invest in.\
**Loan Status will be our response/target variable.** Negative outcomes are those such as charged off, default, late, etc. Positive outcomes are fully paid and current. We want to invest in the type of loans that are consistently fully paid and current so we know our money gets back to us; if we find loans with high return that fall into this category, we have found our competetive advantage
"""

df['loan_status'].value_counts()

"""Note: very few loans are in default, but many are charged off. There is also two categories that include data before the current credit policy. We will merge that data as it is still valid, even if it is older"""

stringStatus = df['loan_status'].astype('str')

notMeetPaidMask = stringStatus.str.contains("Status:Fully")
notMeetChargedMask = stringStatus.str.contains("Status:Charged")

stringStatus[notMeetPaidMask] = "Fully Paid"
stringStatus[notMeetChargedMask] = "Charged Off"

df['loan_status'] = stringStatus.astype('category')
df['loan_status'].value_counts()

"""## Which Feature Variables Actually Matter (Correlation Matrix)

Our x values (feature variables) are everything that is not loan status, our y value is the loan status itself. Split dataframe df into these two sets. As a note, if there is a hardship or settlement we will keep the flag but none of the details for simplicity. We will also drop all datetime variables as they should not have any correlation to the loan status.

**Additionally: we want to focus on larger categories such as employment length, home ownership, LC's grades, verification status, and application type.** Other categories seem less relevant, so we will hone in on these as well as numerical data
"""

floatFeatures = df.dtypes[df.dtypes == 'float64'].index.values
categoriesInQuestion = ['emp_length', 'home_ownership', 'sub_grade', 'verification_status', 'application_type', 'loan_status']
subset = np.append(floatFeatures, categoriesInQuestion).tolist()

simpleDF = df[subset]

x = simpleDF.loc[:, simpleDF.columns != 'loan_status']

# Y value/Resposne Variable
y = simpleDF['loan_status']

print(x.head())
print(y.head())

# Need to encode good vs bad outcome for y values.
# Good outcomes are "Current" and "Fully Paid" --> 1
# The rest are bad --> 0
remap={'Current': 1, 'Fully Paid': 1, 'Charged Off': 0, 'Default': 0, 'In Grace Period': 0,
       'Late (16-30 days)': 0, 'Late (31-120 days)': 0}
y.replace(remap, inplace=True)
y.head()

"""So that none of our numerical data outshines the categorical data, we will also need to min-max scale (0-1) all of the numerical data before generating our correlation matrix. Min-Max Scaling does not affect one-hot encoded data since those values are already between 0 and 1. Due to the size of the x dataframe and its limits on one-hot encoding, we will do a random sample of 1,000 tuples"""

xPt1 = x.sample(n = 1000, random_state = 24)

intFeatures = xPt1.dtypes[xPt1.dtypes == 'int'].index.values
floatFeatures = xPt1.dtypes[xPt1.dtypes == 'float64'].index.values

scaler = MinMaxScaler()

for col in intFeatures:
    xPt1[col] = scaler.fit_transform(xPt1[col].values.reshape(-1,1))
for col in floatFeatures:
    xPt1[col] = scaler.fit_transform(xPt1[col].values.reshape(-1,1))

scaledX = xPt1.copy()
scaledX

# Get dummies on scaledX to make the categories machine readable
scaledX = pd.get_dummies(scaledX)

# Generate correlation matrix

correlationDF = scaledX.copy()
correlationDF['loan_status'] = y.copy()

corr = correlationDF.corr()
#corr.style.background_gradient(cmap='coolwarm').set_precision(2) --> this line generates heatmap (huge)

# Better appraoch is to show a bar graph with correlations to loan status itself

# Take absolute value of loan_status column
# Show variables with more than 0.1 correlation (head and tail)
# Take those variables on x axis, correlation on y axis, make bar graph (positive and negative, not absolute)

loanStatus = corr['loan_status']
loanStatusAbs = abs(loanStatus)
highCorr = loanStatus[loanStatusAbs > 0.1]
highCorrS = highCorr.sort_values()
highCorrS

fig = plt.figure()
ax = fig.add_axes([0,0,2,2])
x = highCorrS.index.values
y = highCorrS
ax.barh(x, y, height = 0.5)
plt.xlabel("Correlation")
plt.ylabel("Variable")
plt.title("Correlation to Loan Status Variable")
plt.show()

"""### Section Findings:
* Positive loan status (low risk) has an expected correlation to FICO scores, with the high range being a better predictor.
* Joint applications have lower risk than individual applicants, unless the second application had a large collection recently
* Income verification status is a poor predictor for risk
* A and B grades given by Lending Club are good bets/predictors for low risk but not the best
* Home owners and mortagers rather than renters represent better investments
* Higher income means lower risk in general
* As loan amount and interest rate goes up, so does the risk
* Hardship is a great predictor, but we can't see hardship on a loan when investing (that happens after investments are made)


**Variables to focus on: FICO scores (last fico high range, not current), secondary applicant number of revolving accounts (if available), joint applicant (application type), home ownership status and income (debt to income/dti variable)**
"""

