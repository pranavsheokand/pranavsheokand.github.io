import requests
import pandas as pd

leagueid = 183102718
swid = "{E08F2F9A-1BC6-4FBB-8484-B7C5E9C2B305}"
espn_s2 = "AECywot37qTilIsMxOvEOaXKuB624v6X%2BFV8BqdS1jj9oaz7c2Ka%2FOia4KDbbT%2FD3DFhei7wveI3C2qLTGzryVbpE2LBJgPMMYBSqLPNHh730SmSssB8zsHTqFENXh6zlekBwhit37E4NEz0LUlDejEL8QDBshyIMqQW0ZyosrDVHJK2iGMj16PtVSk9aYvE6QIJAMYJP63a5QREcI4tm0GbPeSDJsb4eyS2brrRXvI5LH8SOrgAyGCMvqh%2F9xoNfFku5Ucssl763%2Bq66W9inwRdmMxYJVtDJZHjG45HY%2BT0Ww%3D%3D"

class FantasyLeague:
    '''
    ESPN Fantasy Football League class for pulling data from the ESPN API
    '''
    BASE_URL = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{year}/segments/0/leagues/{league_id}"
    POSITION_MAPPING = {
        0: 'QB',
        4: 'WR',
        2: 'RB',
        23: 'FLEX',
        6: 'TE',
        16: 'D/ST',
        17: 'K',
        20: 'Bench',
        21: 'IR',
        '': 'NA'
    }

    def __init__(self, league_id, year, espn_s2, swid):
        self.league_id = league_id
        self.year = year
        self.espn_s2 = espn_s2
        self.swid = swid
        self.base_url = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{self.year}/segments/0/leagues/{self.league_id}"
        self.cookies = {
            "swid": self.swid,
            "espn_s2": self.espn_s2
        }
        self.matchup_df = None
        self.team_df = None

    def make_request(self, url, params, view):
        '''
        Initiate a request to the ESPN API
        '''
        params['view'] = view
        return requests.get\
            (url, params=params, cookies={"SWID": self.swid, "espn_s2": self.espn_s2}, timeout=30).json()

    def load_league(self, week):
        '''
        Load the league JSON from the ESPN API
        '''
        url = self.BASE_URL.format(year=self.year, league_id=self.league_id)
        return self.make_request(url + '?view=mMatchup&view=mMatchupScore',
                                 params={'scoringPeriodId': week, 'matchupPeriodId': week}, view='mMatchup')

    def load_player_data(self, league_json, week):
        '''
        Load the player data from the league JSON
        '''
        player_name = []
        player_score_act = []
        player_score_proj = []
        player_roster_slot = []
        player_fantasy_team = []
        weeks = []


        # Loop through each team
        for team in range(0, len(league_json['teams'])):

            # Loop through each roster slot in each team
            for slot in range(0, len(league_json['teams'][team]['roster']['entries'])):
                # Append the week number to a list for each entry for each team
                weeks.append(week)
                # Append player name, player fantasy team, and player ro
                player_name.append(league_json['teams'][team]['roster']
                                ['entries'][slot]['playerPoolEntry']['player']['fullName'])
                player_fantasy_team.append(league_json['teams'][team]['id'])
                player_roster_slot.append(
                    league_json['teams'][team]['roster']['entries'][slot]['lineupSlotId'])

                # Initialize the variables before using them
                act = 0
                proj = 0

                # Loop through each statistic set for each roster slot for each team
                # to get projected and actual scores
                for stat in league_json['teams'][team]['roster']['entries'][slot]['playerPoolEntry']['player']['stats']:
                    if stat['scoringPeriodId'] != week:
                        continue
                    if stat['statSourceId'] == 0:
                        act = stat['appliedTotal']
                    elif stat['statSourceId'] == 1:
                        proj = stat['appliedTotal']
                    else:
                        print('Error')

                player_score_act.append(act)
                player_score_proj.append(proj)

        # Put the lists into a dictionary
        player_dict = {
            'Week': weeks,
            'PlayerName': player_name,
            'PlayerScoreActual': player_score_act,
            'PlayerScoreProjected': player_score_proj,
            'PlayerRosterSlotId': player_roster_slot,
            'PlayerFantasyTeam': player_fantasy_team
        }

        # Transform the dictionary into a DataFrame
        df = pd.DataFrame.from_dict(player_dict)

        # Initialize empty column for PlayerRosterSlot
        df['PlayerRosterSlot'] = ""

        # Ignore chained assignment warnings
        pd.options.mode.chained_assignment = None

        # Replace the PlayerRosterSlot integers with position indicators
        df['PlayerRosterSlot'] = df['PlayerRosterSlotId'].apply(
            lambda x: self.POSITION_MAPPING.get(x, 'NA'))

        df.drop(columns=['PlayerRosterSlotId'], inplace=True)
        self.df = df

    def load_team_names(self, week):
        '''
        Load the team names from the league JSON
        '''
        # Define the URL with our parameters
        url = self.BASE_URL.format(year=self.year, league_id=self.league_id)

        team_json = self.make_request(url,
                                      params={"leagueId": self.league_id,
                                              "seasonId": self.year,
                                              "matchupPeriodId": week},
                                      view="mTeam")

        # Initialize empty list for team names and team ids
        team_id = []
        team_primary_owner = []
        team_location = []
        team_nickname = []
        owner_first_name = []
        owner_last_name = []
        team_cookie = []

        # Loop through each team in the JSON
        for team in range(0, len(team_json['teams'])):
            # Append the team id and team name to the list
            team_id.append(team_json['teams'][team]['id'])
            team_primary_owner.append(team_json['teams'][team]['primaryOwner'])
            team_location.append("NA")
            team_nickname.append("NA")
            owner_first_name.append(team_json['members'][team]['firstName'])
            owner_last_name.append(team_json['members'][team]['lastName'])
            team_cookie.append(team_json['members'][team]['id'])

        # Create team DataFrame
        team_df = pd.DataFrame({
            'PlayerFantasyTeam': team_id,
            'TeamPrimaryOwner': team_primary_owner,
            'Location': team_location,
            'Nickname': team_nickname,
        })

        # Create owner DataFrame
        owner_df = pd.DataFrame({
            'OwnerFirstName': owner_first_name,
            'OwnerLastName': owner_last_name,
            'TeamPrimaryOwner': team_cookie
        })

        # Merge the team and owner DataFrames on the TeamPrimaryOwner column
        team_df = pd.merge(team_df, owner_df, on='TeamPrimaryOwner', how='left')

        # Filter team_df to only include PlayerFantasyTeam, Location, Nickname, OwnerFirstName, and OwnerLastName
        team_df = team_df[['PlayerFantasyTeam', 
                           'Location',
                        'Nickname', 
                        'OwnerFirstName', 'OwnerLastName']]

        # Concatenate the two name columns
        team_df['TeamName'] = team_df['Location'] + ' ' + team_df['Nickname']

        # Create a column for full name
        team_df['FullName'] = team_df['OwnerFirstName'] + \
            ' ' + team_df['OwnerLastName']

        # Drop all columns except id and Name
        team_df = team_df.filter(['PlayerFantasyTeam', 'TeamName', 'FullName'])

        self.df = self.df.merge(team_df, on=['PlayerFantasyTeam'], how='left')
        self.df = self.df.rename(columns={'Name': 'PlayerFantasyTeamName'})

    def get_league_data(self, week=None):
        '''
        Create the league DataFrame
        '''
        if week is None:  # If no specific week is provided, load data for all weeks.
            weeks = list(range(1, 18))  # Assuming 17 weeks in a season.
        else:
            weeks = [week]

        # Instead of appending to self.df directly, we're going to store each week's DataFrame in a list.
        dataframes = []

        for week in weeks:
            league_json = self.load_league(week)
            self.load_player_data(league_json, week)
            self.load_team_names(week)

            # After loading the data for the week, add a copy of the DataFrame to the list.
            dataframes.append(self.df.copy())

        # Concatenate all weekly dataframes into one.
        self.df = pd.concat(dataframes)

        return self.df
    
    def get_matchup_data(self, week=None):
        if week is None:
            weeks = list(range(1, 18))  # Weeks 1 through 17
        else:
            weeks = [week]

        all_matchup_data = []

        for week in weeks:
            # Pull team and matchup data from the URL
            matchup_response = requests.get(self.base_url,
                                            params={"leagueId": self.league_id,
                                                    "seasonId": self.year,
                                                    "matchupPeriodId": week,
                                                    "view": "mMatchup"},
                                            cookies=self.cookies)

            team_response = requests.get(self.base_url,
                                         params={"leagueId": self.league_id,
                                                 "seasonId": self.year,
                                                 "matchupPeriodId": week,
                                                 "view": "mTeam"},
                                         cookies=self.cookies)

            # Transform the response into a json
            matchup_json = matchup_response.json()
            team_json = team_response.json()

            # Transform both of the json outputs into DataFrames
            matchup_df = pd.json_normalize(matchup_json['schedule'])
            team_df = pd.json_normalize(team_json['teams'])

            # Define the column names needed
            matchup_column_names = {
                'matchupPeriodId': 'Week',
                'away.teamId': 'Team1',
                'away.totalPoints': 'Score1',
                'home.teamId': 'Team2',
                'home.totalPoints': 'Score2',
            }

            team_column_names = {
                'id': 'id',
                'location': 'Name1',
                'nickname': 'Name2'
            }

           # Reindex based on column names defined above
            matchup_df = matchup_df.reindex(columns=matchup_column_names).rename(
                columns=matchup_column_names)
            team_df = team_df.reindex(columns=team_column_names).rename(
                columns=team_column_names)

            # Add a new column for regular/playoff game based on week number
            matchup_df['Type'] = ['Regular' if week <=
                                  13 else 'Playoff' for week in matchup_df['Week']]

            # Concatenate the two name columns
            team_df['Name'] = team_df['Name1'] + ' ' + team_df['Name2']

            # Drop all columns except id and Name
            team_df = team_df.filter(['id', 'Name'])

            # (1) Rename Team1 column to id
            matchup_df = matchup_df.rename(columns={"Team1": "id"})

            # (1) Merge DataFrames to get team names instead of ids and rename Name column to Name1
            matchup_df = matchup_df.merge(team_df, on=['id'], how='left')
            matchup_df = matchup_df.rename(columns={'Name': 'Name1'})

            # (1) Drop the id column and reorder columns
            matchup_df = matchup_df[['Week', 'Name1',
                                     'Score1', 'Team2', 'Score2', 'Type']]

            # (2) Rename Team1 column to id
            matchup_df = matchup_df.rename(columns={"Team2": "id"})

            # (2) Merge DataFrames to get team names instead of ids and rename Name column to Name2
            matchup_df = matchup_df.merge(team_df, on=['id'], how='left')
            matchup_df = matchup_df.rename(columns={'Name': 'Name2'})

            # (2) Drop the id column and reorder columns
            matchup_df = matchup_df[['Week', 'Name1',
                                     'Score1', 'Name2', 'Score2', 'Type']]

            all_matchup_data.append(matchup_df)

        self.matchup_df = pd.concat(all_matchup_data, ignore_index=True)

        return self.matchup_df
    
class FantasyCalculator:
    def __init__(self):
        self.leagueid = 183102718
        self.swid = "{E08F2F9A-1BC6-4FBB-8484-B7C5E9C2B305}"
        self.espn_s2 = "AECywot37qTilIsMxOvEOaXKuB624v6X%2BFV8BqdS1jj9oaz7c2Ka%2FOia4KDbbT%2FD3DFhei7wveI3C2qLTGzryVbpE2LBJgPMMYBSqLPNHh730SmSssB8zsHTqFENXh6zlekBwhit37E4NEz0LUlDejEL8QDBshyIMqQW0ZyosrDVHJK2iGMj16PtVSk9aYvE6QIJAMYJP63a5QREcI4tm0GbPeSDJsb4eyS2brrRXvI5LH8SOrgAyGCMvqh%2F9xoNfFku5Ucssl763%2Bq66W9inwRdmMxYJVtDJZHjG45HY%2BT0Ww%3D%3D"
        self.league = FantasyLeague(league_id=leagueid,year = 2024, espn_s2=espn_s2,swid = swid)
        self.league_data = self.league.get_league_data()
        self.nolan_players = ['Patrick Mahomes', 'Jared Goff', 'DeVonta Smith', 
                              'Jameson Williams', 'Puka Nacua', 'Saquon Barkley', 
                             'James Cook', 'Bucky Irving', 'Mark Andrews', 
                             'Travis Kelce', 'Justin Tucker', 'Ravens D/ST']
        
        self.pranav_players = ['Lamar Jackson', 'Justin Herbert', 'Ladd McConkey', 
                               'Mike Evans', 'Terry McLaurin', 'Derrick Henry', 
                               'Jahmyr Gibbs', 'David Montgomery', 'Sam LaPorta', 
                               'Zach Ertz', 'Tyler Bass', 'Bills D/ST']
        
        self.vidy_players = ['Josh Allen', 'Jalen Hurts', 'Amon-Ra St. Brown', 
                             'A. J. Brown', 'Justin Jefferson', 'Aaron Jones', 
                             'Josh Jacobs', 'Kyren Williams', 'Dallas Goedert', 
                             'Dalton Kincaid', 'Jake Bates', 'Eagles D/ST']
        

    def calculate_scores_for_player_list(self, players_to_check, week):
        league = espnlocal.FantasyLeague(
            league_id=self.leagueid, 
            year=2024, 
            espn_s2=self.espn_s2, 
            swid=self.swid
        )
        league_data = league.get_league_data()
        
        scores = 0
        player_scores = {}
        
        # First, initialize all players with 0 to maintain order
        for player in players_to_check:
            player_scores[player] = 0
        
        # Then update scores for players found in the data
        for player in players_to_check:
            try:
                score = league_data[
                    (league_data['PlayerName'] == player) & 
                    (league_data['Week'] == int(week))
                ]['PlayerScoreActual'].values[0]
                scores += score
                player_scores[player] = score
            except:
                continue
        
        # Convert to ordered dictionary to maintain order
        from collections import OrderedDict
        ordered_scores = OrderedDict()
        for player in players_to_check:
            ordered_scores[player] = player_scores[player]
            
        return {
            'total': float(scores),
            'individual_scores': ordered_scores
        }

    def get_nolan_scores(self,week):
        return self.calculate_scores_for_player_list(self.nolan_players,week)
        
    def get_pranav_scores(self,week):
        return self.calculate_scores_for_player_list(self.pranav_players,week)
        
    def get_vidy_scores(self,week):
        return self.calculate_scores_for_player_list(self.vidy_players,week)

class SleeperFantasyAPI:
    def __init__(self):
       """Initialize the Sleeper API client"""
       self.base_url = "https://api.sleeper.app/v1"
       self.current_nfl_season = 2024
       self.headers = {
           'User-Agent': 'Mozilla/5.0',
           'Accept': 'application/json'
       }
       # Create player mapping when initialized
       self.player_map = self.create_player_name_map()
    
    def get_players_info(self) -> dict:
       """Get all players information"""
       endpoint = f"{self.base_url}/players/nfl"
       response = requests.get(
           endpoint,
           headers=self.headers,
           verify=False
       )
       response.raise_for_status()
       return response.json()
    
    def create_player_name_map(self) -> dict:
       """Create mapping of player names to IDs"""
       print("Creating player name to ID mapping...")
       players = self.get_players_info()
       name_to_id = {}
       for player_id, player_info in players.items():
           if player_info:
               full_name = f"{player_info.get('first_name', '')} {player_info.get('last_name', '')}".strip().lower()
               name_to_id[full_name] = player_id
       print(f"Mapped {len(name_to_id)} players")
       return name_to_id

    def get_player_stats(self, week: int) -> dict:
       """Fetch stats for a specific week using Sleeper's PPR scoring"""
       ##TODO need to change to pose not regular
       endpoint = f"{self.base_url}/stats/nfl/regular/{self.current_nfl_season}/{week}"
       print(f"Fetching stats from: {endpoint}")
       
       response = requests.get(
           endpoint, 
           headers=self.headers,
           verify=False
       )
       
       print(f"Response status: {response.status_code}")
       
       if response.status_code != 200:
           print(f"Error content: {response.text}")
           response.raise_for_status()
           
       return response.json()
   
    def get_weekly_stats_for_player(self, player_name: str, week: int) -> float:
        """Get weekly PPR points for a specific player"""
        player_id = self.player_map.get(player_name.lower())
        # if not player_id:
        #    print(f"WARNING: Could not find player ID for {player_name}")
        #    return 0.0
       
        stats = self.get_player_stats(week)
        special_cases = {"Lamar Jackson":"4881", 
                         "A. J. Brown":"5859",
                        "Ravens D/ST": "BAL",
                        "Bills D/ST": "BUF",
                        "Eagles D/ST": "PHI"}
        if player_name in special_cases:
            player_id = special_cases[player_name]

        player_stats = stats.get(player_id, {})
       
        print(f"\nLooking up stats for {player_name} (ID: {player_id})")
        print(f"Full stats received: {player_stats}")
        # Try to find fantasy points in the stats
        if 'pts_ppr' in player_stats:
           return float(player_stats['pts_ppr'])
    #    elif 'fantasy_points_ppr' in player_stats:
    #        return float(player_stats['fantasy_points_ppr'])
    #    elif 'fantasy_points' in player_stats:
    #        return float(player_stats['fantasy_points'])
       
        # If no points found, show what data we did get
        print(f"Available stat keys: {list(player_stats.keys())}")
        return 0.0

class FantasyCalculatorSleeper:
    def __init__(self):
        self.nolan_players = ['Patrick Mahomes', 'Jared Goff', 'DeVonta Smith', 
                              'Jameson Williams', 'Puka Nacua', 'Saquon Barkley', 
                             'James Cook', 'Bucky Irving', 'Mark Andrews', 
                             'Travis Kelce', 'Justin Tucker', 'Ravens D/ST']
        
        self.pranav_players = ['Lamar Jackson', 'Justin Herbert', 'Ladd McConkey', 
                               'Mike Evans', 'Terry McLaurin', 'Derrick Henry', 
                               'Jahmyr Gibbs', 'David Montgomery', 'Sam LaPorta', 
                               'Zach Ertz', 'Tyler Bass', 'Bills D/ST']
        
        self.vidy_players = ['Josh Allen', 'Jalen Hurts', 'Amon-Ra St. Brown', 
                             'A. J. Brown', 'Justin Jefferson', 'Aaron Jones', 
                             'Josh Jacobs', 'Kyren Williams', 'Dallas Goedert', 
                             'Dalton Kincaid', 'Jake Bates', 'Eagles D/ST']
        self.sleeper = SleeperFantasyAPI()
    
    def calculate_scores_for_player_list(self, players_to_check, week):        
        scores = 0
        player_scores_list = []
        
        for player in players_to_check:
            try:
                score = self.sleeper.get_weekly_stats_for_player(player, week)
                scores += score
                player_scores_list.append({"name": player, "score": float(score)})
            except:
                player_scores_list.append({"name": player, "score": 0.0})
                continue
                
        return {
        'total': float(scores),
        'individual_scores': player_scores_list  # Return as list instead of dict
    }

    def get_nolan_scores(self,week):
        return self.calculate_scores_for_player_list(self.nolan_players,week)
        
    def get_pranav_scores(self,week):
        return self.calculate_scores_for_player_list(self.pranav_players,week)
        
    def get_vidy_scores(self,week):
        return self.calculate_scores_for_player_list(self.vidy_players,week)