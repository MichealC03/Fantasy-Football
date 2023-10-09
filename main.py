import numpy as np
from pyarrow import string
import requests
from variables import *
import pandas as pd
import json
import streamlit as st

#Pulling from sources:
#  https://www.fantasylife.com/tools/nfl-rankings
#  https://fantasy.espn.com/football/players/projections
#  https://www.freedraftguide.com/fantasy-football/average-draft-position?STYLE=0&CHANGE=3
#  https://fantasyfootballfromupnorth.com/draft-rankings
#  https://www.draftsharks.com/rankings/ppr

######################################################################################
#Helper methods
######################################################################################


def getTeamName(row : str, position, name, defense):
  """
  Get the name of the team

  Some longer description

  Arguments:
     row (str): The description of blank

  """
  if row[position] == defense:
    return row[name].split()[-1]
  else:
    return row[name]

#Highlight columns where the difference is greater than 5 between espn
def highlightESPN(row, col):
  #Find the difference between picks
  pickDifference = row['ESPN Pick'] - row[col]

  #For value picks
  if (pickDifference < 5 and pickDifference > 0):
    return ['background-color: #d6f5d6'] * len(row)
  elif (pickDifference >= 5 and pickDifference < 10):
    return ['background-color: #8bfc9c'] * len(row)
  elif (pickDifference >= 10 and pickDifference < 20):
    return ['background-color: #3abd4e'] * len(row)
  elif (pickDifference >= 20):
    return ['background-color: #e699ff'] * len(row)
  #For not value picks
  elif (pickDifference < 0 and pickDifference > -5):
    return ['background-color: #ffe0cc'] * len(row)
  elif (pickDifference > -10 and pickDifference <= -5):
    return ['background-color: #ffc299'] * len(row)
  elif (pickDifference > -20 and pickDifference <= -10):
    return ['background-color: #ffa366'] * len(row)
  elif(row[col] == 9999):
    return ['color: #FFFFFF'] * len(row)
  elif (pickDifference <= -20):
    return ['background-color: #ff4d4d'] * len(row)
  else:
    return ['background-color: #1C00ff00'] * len(row)


#Set up a function to highlight rows
def highlightPicksESPN(df):
  #Keep project totals at two decimal places
  f = {'Projected Totals': '{:.2f}'}

  #.apply(highlightESPN, axis=1, args=("WazRanks",), subset=["WazRanks", "ESPN Pick"])\
  #Highlight for each column compared to ESPN PICKS
  style_df = df.style.format(f)\
             .apply(highlightESPN, axis=1, args=("RT Pick",), subset=["RT Pick", "ESPN Pick"])\
             .apply(highlightESPN, axis=1, args=("ClaytonRanks",), subset=["ClaytonRanks", "ESPN Pick"])\
             .apply(highlightESPN, axis=1, args=("SharkRanks",), subset=["SharkRanks", "ESPN Pick"])

  return style_df.hide("ESPN Pick", axis=1)

#Highlight columns where the difference is greater than 5 between espn
def highlightNFL(row, col):
  #Find the difference between picks
  pickDifference = row['NFL Pick'] - row[col]

  #For value picks
  if (pickDifference < 5 and pickDifference > 0):
    return ['background-color: #d6f5d6'] * len(row)
  elif (pickDifference >= 5 and pickDifference < 10):
    return ['background-color: #8bfc9c'] * len(row)
  elif (pickDifference >= 10 and pickDifference < 20):
    return ['background-color: #3abd4e'] * len(row)
  elif (pickDifference >= 20):
    return ['background-color: #e699ff'] * len(row)
  #For not value picks
  elif (pickDifference < 0 and pickDifference > -5):
    return ['background-color: #ffe0cc'] * len(row)
  elif (pickDifference > -10 and pickDifference <= -5):
    return ['background-color: #ffc299'] * len(row)
  elif (pickDifference > -20 and pickDifference <= -10):
    return ['background-color: #ffa366'] * len(row)
  elif(row[col] == 9999):
    return ['color: #FFFFFF'] * len(row)
  elif (pickDifference <= -20):
    return ['background-color: #ff4d4d'] * len(row)
  else:
    return ['background-color: #1C00ff00'] * len(row)


#Set up a function to highlight rows
def highlightPicksNFL(df):
  #Keep project totals at two decimal places
  f = {'Projected Totals': '{:.2f}'}

  #.apply(highlightNFL, axis=1, args=("WazRanks",), subset=["WazRanks", "NFL Pick"])\
  #Highlight for each column compared to NFL PICKS
  style_df = df.style.format(f)\
             .apply(highlightNFL, axis=1, args=("RT Pick",), subset=["RT Pick", "NFL Pick"])\
             .apply(highlightNFL, axis=1, args=("ClaytonRanks",), subset=["ClaytonRanks", "NFL Pick"])\
             .apply(highlightNFL, axis=1, args=("SharkRanks",), subset=["SharkRanks", "NFL Pick"])

  return style_df.hide("NFL Pick", axis=1)


#Apply this function to if Name has NaN bring in the name from RTSPORTS
def bringName(row, mergeTo, mergeFrom):
  if row[mergeTo] == 0:
    newName = row[mergeFrom]
    #print(newName)
    return newName
  else:
    return row[mergeTo]


#Merge two dataframes together
def mergeDfs(df1, df2, name):
  df1 = df1.merge(df2, left_on='Name', right_on=name, how="left")

  df1['Name'] = df1.apply(bringName, args=(
      'Name',
      name,
  ), axis=1)
  df1 = df1.drop([name], axis=1)

  return df1


def cleanUp(df, name):
  df[name] = df[name].apply(lambda x: str(x).replace(".", ""))
  df[name] = df[name].apply(lambda x: str(x).replace("'", ""))
  df[name] = df[name].apply(lambda x: str(x).replace(" Jr", ""))
  df[name] = df[name].apply(lambda x: str(x).replace(" III", ""))
  df[name] = df[name].apply(lambda x: str(x).replace(" II", ""))

  return df[name]


######################################################################################
# Pulling in data
######################################################################################


#Get the rows for ESPN (they are split into 50)
def getRowsESPN(cookies, headers, params, start):

  response = requests.get(
      'https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2023/segments/0/leaguedefaults/3',
      params=params,
      cookies=cookies,
      headers=headers,
  )

  #Turn the response into a json and get the players out of it
  players_dict = response.json()['players']

  playerList = []
  statsList = []

  #For each player add the player key into the empty list
  for row in players_dict:
    #Get everything about the player info
    inner_player = row['player']

    #Get the team name only for D/ST which is the second to last before end
    if (inner_player['defaultPositionId'] == 16):
      defense = str(inner_player['fullName']).split()
      inner_player['fullName'] = defense[-2]

    playerList.append(inner_player)

    # Get the projected Total for the year and round to 2 decimals
    inner_stat = inner_player['stats']
    stats = str(inner_stat).split()
    projectedTotal = float((stats[3])[:-1])
    statsList.append("{:.2f}".format(projectedTotal))

  # Change the list of players to a dataframe
  df = pd.DataFrame(playerList)

  #Choose and import to display final project
  df = df[['fullName', "defaultPositionId"]]
  df.rename(columns={"fullName": "Name"}, inplace=True)
  df["Projected Totals"] = statsList

  #Drop kickers
  if variation != 'NORMAL':
    kickers = df[df['defaultPositionId'] == 5].index
    df.drop(kickers, inplace=True)
    df.reset_index(drop=True, inplace=True)

  #Adjust the indecies
  df.index += start

  #Set espn picks = to the index
  df["ESPN Pick"] = df.index

  return df

#Call the getRows based on the format
def formatRowsRT(scoring, variation):
    #PPR 2FLEX
    df = pd.DataFrame()
    
    if(scoring == 'PPR' and variation == '2FLEX'):
      df = df._append(getRowsRT(cookiesRT, headersRT, paramsRT))
    elif(scoring == 'PPR' and variation == 'SUPERFLEX'):
      df = df._append(getRowsRT(cookiesSuperFlexRT, headersSuperFlexRT, paramsSuperFlexRT))
    else:
      df = df._append(getRowsRT(cookiesRT, headersRT, paramsRT))

    return df

#Get the rows from RT SPORTS
def getRowsRT(cookies, headers, params):
  #Get the JS reesponse from the server
  response = requests.get(
      'https://www.freedraftguide.com/football/adp-aav-provider.php',
      params=params,
      cookies=cookies,
      headers=headers,
  )

  #Get the json and turn it into a df with player_list as key
  players_df = response.json()['player_list']
  df = pd.DataFrame(players_df)

  #Drop kickers and reset the index
  if variation != 'NORMAL':
    kickers = df[df['position'] == "K"].index
    df.drop(kickers, inplace=True)
    df.reset_index(drop=True, inplace=True)

  #Get defenses to only say name
  df['name'] = df.apply(getTeamName,
                        args=(
                            'position',
                            'name',
                            "DEF",
                        ),
                        axis=1)

  df.index += 1

  #Only select a few values from this df
  df = df[['team', 'position', 'name']]

  df["RT Pick"] = df.index

  df['name'] = cleanUp(df, 'name')

  return df

def formatRowsUpNorth(scoring, variation):
    #PPR 2FLEX
    df = pd.DataFrame()
    
    if(scoring == 'PPR' and variation == '2FLEX'):
      df = df._append(getRowsUpNorth(headersUpNorth, paramsUpNorth, requestsUpNorth))
    elif(scoring == 'PPR' and variation == 'SUPERFLEX'):
      df = df._append(getRowsUpNorth(headersSuperFlexUpNorth, paramsSuperFlexUpNorth, requestsSuperFlexUpNorth))
    elif(scoring == '.5 PPR' and variation == 'NORMAL'):
      df = df._append(getRowsUpNorth(headersHalfPPRUpNorth, paramsHalfPPRUpNorth, requestsHalfPPRUpNorth))

    return df

def getRowsUpNorth(headers, params, requestURL):
  response = response = requests.get(
      requestURL,
      params=params,
      headers=headers,
  )

  # Extract the substring containing the relevant data
  start_index = response.text.find('"players":')  #Start at players key
  end_index = response.text.find(
      ']',
      start_index) + 1  #Find the end bracket in the file after the start index
  relevant_data = response.text[start_index:
                                end_index]  #only get the players field

  # Parse the extracted data as JSON and add brackets to the end of the data received from above
  players_data = json.loads('{' + relevant_data + '}')['players']

  expertRankings = []
  players = []

  for row in players_data:
    try:
      players.append(row)
      expert_ranking = row['experts']
      clayton_rank = expert_ranking['2709']
      
      expertRankings.append(clayton_rank)
    except:
      players.pop()
      break

  df = pd.DataFrame(players)
  df['ClaytonRanks'] = expertRankings

  #Drop kickers and reset the index
  if variation != 'NORMAL':
    kickers = df[df['player_position_id'] == "K"].index
    df.drop(kickers, inplace=True)
    df.reset_index(drop=True, inplace=True)

  df['player_name'] = cleanUp(df, 'player_name')
  #Get defenses to only say name
  df['player_name'] = df.apply(getTeamName,
                               args=(
                                   'player_position_id',
                                   'player_name',
                                   "DST",
                               ),
                               axis=1)

  return df[["player_name", "ClaytonRanks"]]

def getRowsSharks(cookies, headers, requestURL, scoring, variation):
  response = response = requests.get(
      requestURL,
      cookies=cookies,
      headers=headers,
  )

  # Extract the substring containing the relevant data
  start_index = response.text.find('"projections":')  #Start at players key
  end_index = response.text.find(
      '],"teams":',
      start_index) + 1  #Find the end bracket in the file after the start index
  relevant_data = response.text[start_index:
                                end_index]  #only get the players field

  # Parse the extracted data as JSON and add brackets to the end of the data received from above
  players_data = json.loads('{' + relevant_data + '}')['projections']

  players =[]
  expertRankings = []
  positions = []

  for row in players_data:
    player_row = row['player']
    firstName = player_row['first_name']
    lastName = player_row['last_name']
    positions.append(player_row['position'])
    players.append(firstName + " " + lastName)

    if variation == '2FLEX':
      expertRankings.append(row['dmvpPPROverallRank'])     #dmvpPPRSuperflex
    elif variation == 'SUPERFLEX':
      expertRankings.append(row['dmvpPPRSuperflexOverallRank'])     #dmvpPPRSuperflex
    elif scoring ==  '.5 PPR' and variation == 'NORMAL':
      expertRankings.append(row['dmvpHalfPPROverallRank'])     #dmvpHalfPPR

  df = pd.DataFrame({'name' : players})
  df['SharkRanks'] = expertRankings
  df['Positions'] = positions

  #Drop kickers and reset the index
  if variation != 'NORMAL':
    kickers = df[df['Positions'] == "K"].index
    df.drop(kickers, inplace=True)
    df.reset_index(drop=True, inplace=True)

  #Drop DE and reset the index
  kickers = df[df['Positions'] == "DE"].index
  df.drop(kickers, inplace=True)
  df.reset_index(drop=True, inplace=True)

  df['name'] = cleanUp(df, 'name')
  #Get defenses to only say name
  df['name'] = df.apply(getTeamName,
                               args=(
                                   'Positions',
                                   'name',
                                   "DEF",
                               ),
                               axis=1)

  return df

#Add all of the 50 players per screen
def espn(df):
  df = df._append(getRowsESPN(cookies50, headers50, params50, 1))
  df = df._append(
      getRowsESPN(cookies100, headers100, params100, df.index[-1] + 1))
  df = df._append(
      getRowsESPN(cookies150, headers150, params150, df.index[-1] + 1))
  df = df._append(
      getRowsESPN(cookies200, headers200, params200, df.index[-1] + 1))
  df = df._append(
      getRowsESPN(cookies250, headers250, params250, df.index[-1] + 1))
  df = df._append(
      getRowsESPN(cookies300, headers300, params300, df.index[-1] + 1))

  df['Name'] = cleanUp(df, 'Name')

  return df

def getRowsFantasyLife(cookies, headers, requestURL, count):
  response = requests.get(
      requestURL,
      cookies=cookies,
      headers=headers,
  )

  #Get the json and turn it into a df with player_list as key
  players_dict = response.json()['items']

  playerList = []
  positions = []
  wazRanks = []

  #For each player add the player key into the empty list
  for row in players_dict:
    #Get everything about the player info
    inner_player = row['740']
    playerList.append(inner_player['formatted'])

    #Get positions
    inner_positions = row['746']
    positions.append(inner_positions)

    #Get waz ranks
    inner_rankings = row['752']
    wazRanks.append(inner_rankings)

  df = pd.DataFrame({'name': playerList})
  df['WazRanks'] = wazRanks
  df['Postions'] = positions

  df.index += count

  return df[["name", "WazRanks"]]

#Call the getRows based on the format
def formatRowsFantasyLife(scoring, variation):
    #PPR 2FLEX
    df = pd.DataFrame()
    if(scoring == 'PPR' and variation == '2FLEX'):
        df = df._append(getRowsFantasyLife(cookiesFantasyLife50, headersFantasyLife50, requestsFantasyLife50, 1))
        df = df._append(getRowsFantasyLife(cookiesFantasyLife100, headersFantasyLife100, requestsFantasyLife100, df.index[-1] + 1))
        df = df._append(getRowsFantasyLife(cookiesFantasyLife150, headersFantasyLife150, requestsFantasyLife150, df.index[-1] + 1))
        df = df._append(getRowsFantasyLife(cookiesFantasyLife200, headersFantasyLife200, requestsFantasyLife200, df.index[-1] + 1))
        df = df._append(getRowsFantasyLife(cookiesFantasyLife250, headersFantasyLife250, requestsFantasyLife250, df.index[-1] + 1))
        df = df._append(getRowsFantasyLife(cookiesFantasyLife300, headersFantasyLife300, requestsFantasyLife300, df.index[-1] + 1))
    elif(scoring == 'PPR' and variation == 'SUPERFLEX'):
        df = df._append(getRowsFantasyLife(cookiesSuperFlexFantasyLife50, headersSuperFlexFantasyLife50, requestsSuperFlexFantasyLife50, 1))
        df = df._append(getRowsFantasyLife(cookiesSuperFlexFantasyLife100, headersSuperFlexFantasyLife100, requestsSuperFlexFantasyLife100, df.index[-1] + 1))
        df = df._append(getRowsFantasyLife(cookiesSuperFlexFantasyLife150, headersSuperFlexFantasyLife150, requestsSuperFlexFantasyLife150, df.index[-1] + 1))
        df = df._append(getRowsFantasyLife(cookiesSuperFlexFantasyLife200, headersSuperFlexFantasyLife200, requestsSuperFlexFantasyLife200, df.index[-1] + 1))
    elif(scoring == '.5 PPR' and variation == 'NORMAL'):
        df = df._append(getRowsFantasyLife(cookiesHalfPPRFantasyLife50, headersHalfPPRFantasyLife50, requestsHalfPPRFantasyLife50, 1))
        df = df._append(getRowsFantasyLife(cookiesHalfPPRFantasyLife100, headersHalfPPRFantasyLife100, requestsHalfPPRFantasyLife100, df.index[-1] + 1))
        df = df._append(getRowsFantasyLife(cookiesHalfPPRFantasyLife150, headersHalfPPRFantasyLife150, requestsHalfPPRFantasyLife150, df.index[-1] + 1))
        df = df._append(getRowsFantasyLife(cookiesHalfPPRFantasyLife200, headersHalfPPRFantasyLife200, requestsHalfPPRFantasyLife200, df.index[-1] + 1))

    return df
       
#Expert Rob Waziak's ranks
def wazRanks(scoring, variation):
  df = pd.DataFrame()
  
  df = formatRowsFantasyLife(scoring, variation)

  df['name'] = cleanUp(df, 'name')

  return df

#Get the rows for NFL
def getNFLRows(df):
  table = pd.read_html('https://fantasy.nfl.com/research/rankings?leagueId=0&statType=draftStats')
  table2 = pd.read_html('https://fantasy.nfl.com/research/rankings?offset=101&sort=average&statType=draftStats')
  df = table[0]
  df['Player'] = df['Player'].apply(lambda x: ' '.join(str(x).split()[:2]))
  df2 = table2[0]
  df2.index += 100
  df2['Player'] = df2['Player'].apply(lambda x: ' '.join(str(x).split()[:2]))
  wholeDf = df._append(df2)

  wholeDf = wholeDf.rename(columns={"Player": "Name"})
  wholeDf['Name'] = cleanUp(wholeDf, 'Name')
  wholeDf["NFL Pick"] = wholeDf.index + 1


  return wholeDf[['NFL Pick', 'Name']]


def main(website, scoring, variation):
  df = pd.DataFrame()

  #Merge espn and Fantasy Life
  if website == 'ESPN':
    df = mergeDfs(espn(df), wazRanks(scoring, variation), 'name')
  else:
    df = mergeDfs(getNFLRows(df), wazRanks(scoring, variation), 'name')

  #Merge ESPN and RTSports
  df = mergeDfs(df, formatRowsRT(scoring, variation), 'name')

  #Merge ESPN and UpNorth
  df = mergeDfs(df, formatRowsUpNorth(scoring, variation), 'player_name')

  df = mergeDfs(df,
                getRowsSharks(cookiesSharks, headersSharks, requestsShark, scoring, variation),
                'name')

  if website == 'NFL':
    df['Projected Totals'] = 0
    df['ESPN Pick'] = 9999
  else:
    df['NFL Pick'] = 9999

  #Adjust the columns
  df = df[[
      "Name", "team", "position", "Projected Totals", "ESPN Pick", "NFL Pick", "RT Pick",
      "WazRanks", "ClaytonRanks", "SharkRanks"
  ]]

  df.index += 1

  df[["ESPN Pick", "NFL Pick", "RT Pick", "WazRanks", "ClaytonRanks", "SharkRanks"]] = df[["ESPN Pick", "NFL Pick", "RT Pick", "WazRanks", "ClaytonRanks", "SharkRanks"]].fillna(9999)
  df[["Name", "team", "position", "Projected Totals"]] = df[["Name", "team", "position", "Projected Totals"]].fillna("-")

  # using dictionary to convert specific columns
  convert_dict = {
      'Name': str,
      'team': str,
      'position': str,
      'Projected Totals': float,
      'ESPN Pick': int,
      'NFL Pick': int,
      'ClaytonRanks': int,
      'WazRanks': int,
      'SharkRanks': int,
      'RT Pick': int
  }

  df = df.astype(convert_dict)

  #Waz is now onto main season so it messed up
  df.drop(columns=["WazRanks"], inplace=True)

  #Highlight to point out differences
  if website == 'NFL':
    df.drop(columns=["ESPN Pick"], inplace=True)
    style_df = highlightPicksNFL(df)
  else:
    df.drop(columns=["NFL Pick"], inplace=True)
    style_df = highlightPicksESPN(df)
  

  #Print out df
  st.dataframe(style_df)

  # Use a text_input to get the keywords to filter the dataframe
  text_search = st.text_input("Search for player", value="")
  m1 = df["Name"].str.contains(text_search)
  df_search = df[m1]
  if text_search:
    st.write(df_search)

#Main code
website = st.selectbox(
    'What platform are you using?',
    ('', 'ESPN', 'NFL'))
scoring = st.selectbox(
    'What scoring are you using?',
    ('', 'PPR', '.5 PPR'))
variation = st.selectbox(
    'What variation are you using?',
    ('', 'NORMAL', '2FLEX', 'SUPERFLEX'))
if (website != '' and scoring != '' and variation != ''):
  main(website, scoring, variation)