import requests
import json
import configparser
import csv

class TeamSnappier:

    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.access_token = config['api']['access_token']
        self.headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

    def find_me(self):
        API_HREF = "https://api.teamsnap.com/v3/me"
        response = requests.get(API_HREF, headers=self.headers)
        if response.status_code == 200:
            
            print("find_me() was successful!\n")
            parsed_json = response.json()
            list_of_myself = []
            myself = {}
            
            for myself_item in parsed_json["collection"]["items"]:
                myself_data = myself_item["data"]
                for item in myself_data:
                    myself[item["name"]] = item["value"]
            
            list_of_myself.append(myself)
            
            return list_of_myself
            
            
            user_id = parsed_json["collection"]["items"][0]["data"][00]["value"]
            return user_id
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)
            return None

    # ... [Include other methods here in the same manner]
    # ...

    def get_url(self,url):

        # Obtain API specification for an endpoint given URL
        
        API_HREF = url

        response = requests.get(API_HREF, headers=self.headers)

        if response.status_code == 200:

            print("get_url() was successful!\n")

            parsed_json = response.json()

            my_list = []
            my_list.append(parsed_json)

            return my_list

        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)

    def list_assignments(self, teamid):

        params = {
            'team_id': teamid
        }

        API_HREF = f"https://api.teamsnap.com/v3/assignments/search"

        response = requests.get(API_HREF, headers=self.headers, params=params)

        if response.status_code == 200:

            print("list_teams() was successful!\n")
            parsed_json = response.json()

            list_of_objects = []

            for object_item in parsed_json["collection"]["items"]:
                object_data = object_item["data"]
                object = {}
                for item in object_data:
                    object[item["name"]] = item["value"]

                list_of_objects.append(object)

            return list_of_objects

    def list_opponents(self, teamid):

        params = {
            'team_id': teamid
        }

        API_HREF = f"https://api.teamsnap.com/v3/opponents/search"

        response = requests.get(API_HREF, headers=self.headers, params=params)

        if response.status_code == 200:

            print("list_teams() was successful!\n")
            parsed_json = response.json()

            list_of_objects = []

            for object_item in parsed_json["collection"]["items"]:
                object_data = object_item["data"]
                object = {}
                for item in object_data:
                    object[item["name"]] = item["value"]

                list_of_objects.append(object)

            return list_of_objects


        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)

    def list_members(self, teamid):

        params = {
            'team_id': teamid
        }

        API_HREF = f"https://api.teamsnap.com/v3/members/search"

        response = requests.get(API_HREF, headers=self.headers, params=params)

        if response.status_code == 200:

            print("list_teams() was successful!\n")
            parsed_json = response.json()

            list_of_objects = []

            for object_item in parsed_json["collection"]["items"]:
                object_data = object_item["data"]
                object = {}
                for item in object_data:
                    object[item["name"]] = item["value"]

                list_of_objects.append(object)

            return list_of_objects


        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)

    def list_statistics(self, teamid):

        params = {
            'team_id': teamid
        }

        API_HREF = f"https://api.teamsnap.com/v3/statistic_aggregates/search"

        response = requests.get(API_HREF, headers=self.headers, params=params)

        if response.status_code == 200:

            print("list_teams() was successful!\n")
            parsed_json = response.json()

            list_of_objects = []

            for object_item in parsed_json["collection"]["items"]:
                object_data = object_item["data"]
                object = {}
                for item in object_data:
                    object[item["name"]] = item["value"]

                list_of_objects.append(object)

            return list_of_objects


        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)

    def list_divisions(self,divisionid):

        params = {
            'id': divisionid
        }

        API_HREF = f"https://api.teamsnap.com/v3/divisions/search"

        response = requests.get(API_HREF, headers=self.headers, params=params)

        if response.status_code == 200:

            print("list_teams() was successful!\n")
            parsed_json = response.json()

            list_of_objects = []

            for object_item in parsed_json["collection"]["items"]:
                object_data = object_item["data"]
                object = {}
                for item in object_data:
                    object[item["name"]] = item["value"]

                list_of_objects.append(object)

            return list_of_objects


        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)
            
    def list_members(self,team_id):

        params = {
            'team_id': team_id
        }

        API_HREF = f"https://api.teamsnap.com/v3/members/search"  # Replace with your endpoint URL

        response = requests.get(API_HREF, headers=self.headers, params=params)

        if response.status_code == 200:

            print("list_members() was successful!")
            parsed_json = response.json()
            print("n")

            myList = []

            for item in parsed_json["collection"]["items"]:
                data = item["data"]
                team = {}
                for subitem in data:
                    team[subitem["name"]] = subitem["value"]

                myList.append(team)

            return myList

        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)
    def list_division_locations(self,divisionid):

        params = {
            'division_id': divisionid
        }

        API_HREF = f"https://api.teamsnap.com/v3/division_locations/search"

        response = requests.get(API_HREF, headers=self.headers, params=params)

        if response.status_code == 200:

            print("list_teams() was successful!\n")
            parsed_json = response.json()

            list_of_objects = []

            for object_item in parsed_json["collection"]["items"]:
                object_data = object_item["data"]
                object = {}
                for item in object_data:
                    object[item["name"]] = item["value"]

                list_of_objects.append(object)

            return list_of_objects


        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)
    def list_teams(self,userid):

        params = {
            'user_id': userid
        }

        API_HREF = f"https://api.teamsnap.com/v3/teams/search"

        response = requests.get(API_HREF, headers=self.headers, params=params)

        if response.status_code == 200:

            print("list_teams() was successful!\n")
            parsed_json = response.json()

            list_of_teams = []

            for team_item in parsed_json["collection"]["items"]:
                team_data = team_item["data"]
                team = {}
                for item in team_data:
                    team[item["name"]] = item["value"]

                list_of_teams.append(team)

            return list_of_teams


        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)
    
    def list_events(self,userid=None,teamid = None):

        params = {
            'user_id': userid,
            'team_id': teamid
        }

        API_HREF = f"https://api.teamsnap.com/v3/events/search"  # Replace with your endpoint URL

        response = requests.get(API_HREF, headers=self.headers, params=params)

        if response.status_code == 200:

            print("list_events() was successful!")
            parsed_json = response.json()

            list_of_events = []

            for item in parsed_json["collection"]["items"]:
                data = item["data"]
                event = {}
                for subitem in data:
                    event[subitem["name"]] = subitem["value"]

                list_of_events.append(event)

            return list_of_events

        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)
    
    def search_user(self,userid):

        params = {
            'id': userid
        }

        API_HREF = f"https://apiv3.teamsnap.com/users/search"  # Replace with your endpoint URL

        response = requests.get(API_HREF, headers=headers, params=params)

        if response.status_code == 200:

            print("search_user() was successful!\n")

            parsed_json = response.json()

            print(f"id: is {parsed_json['collection']['items'][0]['data'][0]['value']}")
            print(f"email: {parsed_json['collection']['items'][0]['data'][5]['value']}")
            print(f"First Name: {parsed_json['collection']['items'][0]['data'][8]['value']}")
            print(f"Last Name: {parsed_json['collection']['items'][0]['data'][10]['value']}\n")

        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)
            
#TODO Fix creating multiple events Iiteration 
    def create_events(self,events_csv):

        list_of_events = self.csv_to_templates(events_csv)

        for event in list_of_events:
            API_HREF = f"https://api.teamsnap.com/v3/events"  # Replace with your endpoint URL
            response = requests.post(API_HREF, headers=self.headers, json=event)

            if response.status_code in (200, 201, 204):

                print(f"{response.status_code} request successful!")

            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)

    def create_opponents(self, events_csv):

        list_of_opponents = self.csv_to_templates(events_csv)

        for opponent in list_of_opponents:
            API_HREF = f"https://api.teamsnap.com/v3/opponents"  # Replace with your endpoint URL
            response = requests.post(API_HREF, headers=self.headers, json=opponent)

            if response.status_code in (200, 201, 204):

                print(f"{response.status_code} request successful!")

            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)

    def create_team_member(self,csv_file):

        list_of_members = self.csv_to_templates(csv_file)

        for member in list_of_members:
            API_HREF = f"https://api.teamsnap.com/v3/members"  # Replace with your endpoint URL
            response = requests.post(API_HREF, headers=self.headers, json=member)

            if response.status_code in (200, 201, 204):

                print(f"{response.status_code} request successful!")

            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)
    def create_assignments(self,assignments_csv):

        
        list_of_assignments = self.csv_to_templates(assignments_csv)

        for assignment in list_of_assignments:
            API_HREF = f"https://api.teamsnap.com/v3/assignments"  # Replace with your endpoint URL
            response = requests.post(API_HREF, headers=self.headers, json=assignment)

            if response.status_code in (200, 201, 204):

                print(f"{response.status_code} request successful!")

            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)
    def delete_opponents_by_ids(self, opponent_list):

        for opponent in opponent_list:

            API_HREF = f"https://api.teamsnap.com/v3/opponents/{opponent}"  # Replace with your endpoint URL
            response = requests.delete(API_HREF, headers=self.headers)

            if response.status_code in (200, 201, 204):

                print(f"{response.status_code} request successful!")

            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)
                
    def delete_events_by_id(self, event_list):

        for event in event_list:

            API_HREF = f"https://api.teamsnap.com/v3/events/{event}"  # Replace with your endpoint URL
            response = requests.delete(API_HREF, headers=self.headers)

            if response.status_code in (200, 201, 204):

                print(f"{response.status_code} request successful!")

            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)
    def delete_events_by_dict(self,events_dict):
        
        for event in events_dict:
                
            API_HREF = f"https://api.teamsnap.com/v3/events/{event['id']}"  # Replace with your endpoint URL
            response = requests.delete(API_HREF, headers=self.headers)

            if response.status_code in (200, 201, 204):
    
                print(f"{response.status_code} request successful!")
    
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)

    @staticmethod
    def print_list(list,variables=[]):

        print(f"************************")
        
        if variables:
            for item in list:
                for variable in variables:
                    print(f"{variable}: {item[variable]}")
                print("---------------------------------------------")
        else:
            for dict in list:
                for k,v in dict.items():
                    print(f"{k}: {v}")
                print("---------------------------------------------")
                    
                
    @staticmethod
    def json_to_csv(json_data, csv_filename):
        # Ensure input is a list of dictionaries
        if not isinstance(json_data, list) or not all(isinstance(item, dict) for item in json_data):
            raise ValueError("Input JSON should be a list of dictionaries")

        # Extract column headers from the keys of the dictionaries
        headers = list(json_data[0].keys())

        # Write to CSV file
        with open(csv_filename, 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)
            writer.writeheader()
            for row in json_data:
                writer.writerow(row)
    
    
    @staticmethod
    def csv_to_templates(filename):
        """
        Convert a CSV file into a list of template dicts, skipping rows where the first cell is "Mandatory" or "Optional".

        Args:
        - filename (str): Path to the CSV file.

        Returns:
        - list of dicts: The converted JSON format.
        """

        with open(filename, 'r') as file:
            reader = csv.reader(file)

            # Check if the file is empty
            try:
                headers = next(reader)
            except StopIteration:
                return {
                    "template": {
                        "data": []
                    }
                }

            number_of_columns = len(headers)
            # Initialize the data list
            data_list = []

            for values in reader:
                # Skip rows where the first cell is "Mandatory" or "Optional"
                if values[0] in ("Mandatory", "Optional"):
                    continue

                row_data = []

                for i in range(number_of_columns):
                    value = values[i]
                    name = headers[i]
                    row_data.append({
                        "name": name,
                        "value": value
                    })

                data_list.append({"template": {"data": row_data}})  # Append row_data as a dict

        return data_list

    @staticmethod
    def print_members(memberList):

        print(f"Printing Members:")
        print(f"************************")

        for member in memberList:
            print(f"First Name: {member['first_name']}")
            print(f"Last Name: {member['last_name']}")
            print(f"Email address: {member['email_addresses']}\n")

    @staticmethod
    def write_to_json_file(data, filename="output.json"):
        """
        Write a Python dictionary to a JSON file.

        Parameters:
        - data (dict): The dictionary to write to the file.
        - filename (str): The name of the file to which the data should be written. Defaults to "output.json".

        Returns:
        None
        """
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
