import httpx
import json
import configparser
import csv
import asyncio

class TeamSnappier:

    def __init__(self, auth_token=None):
        if auth_token:
            self.access_token = auth_token
        else:
            config = configparser.ConfigParser()
            config.read('config.ini')
            self.access_token = config['api']['access_token']
            
        self.headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

    async def _get(self, url, params=None):
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers, params=params, timeout=15)
            return resp

    async def _post(self, url, json_data):
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=self.headers, json=json_data, timeout=15)
            return resp

    async def _delete(self, url):
        async with httpx.AsyncClient() as client:
            resp = await client.delete(url, headers=self.headers, timeout=15)
            return resp

    async def find_me(self):
        API_HREF = "https://api.teamsnap.com/v3/me"
        response = await self._get(API_HREF)
        
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
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)
            return None

    async def get_url(self, url):
        API_HREF = url
        response = await self._get(API_HREF)
        
        if response.status_code == 200:
            print("get_url() was successful!\n")
            parsed_json = response.json()
            my_list = []
            my_list.append(parsed_json)
            return my_list
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)

    async def list_assignments(self, teamid):
        params = {'team_id': teamid}
        API_HREF = f"https://api.teamsnap.com/v3/assignments/search"
        response = await self._get(API_HREF, params=params)

        if response.status_code == 200:
            print("list_assignments() was successful!\n") 
            parsed_json = response.json()
            list_of_objects = []

            for object_item in parsed_json["collection"]["items"]:
                object_data = object_item["data"]
                obj = {}
                for item in object_data:
                    obj[item["name"]] = item["value"]
                list_of_objects.append(obj)

            return list_of_objects

    async def list_opponents(self, teamid):
        params = {'team_id': teamid}
        API_HREF = f"https://api.teamsnap.com/v3/opponents/search"
        response = await self._get(API_HREF, params=params)

        if response.status_code == 200:
            print("list_opponents() was successful!\n")
            parsed_json = response.json()
            list_of_objects = []

            for object_item in parsed_json["collection"]["items"]:
                object_data = object_item["data"]
                obj = {}
                for item in object_data:
                    obj[item["name"]] = item["value"]
                list_of_objects.append(obj)
            return list_of_objects
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)

    async def list_statistics(self, teamid):
        params = {'team_id': teamid}
        API_HREF = f"https://api.teamsnap.com/v3/statistic_aggregates/search"
        response = await self._get(API_HREF, params=params)

        if response.status_code == 200:
            print("list_statistics() was successful!\n")
            parsed_json = response.json()
            list_of_objects = []
            for object_item in parsed_json["collection"]["items"]:
                object_data = object_item["data"]
                obj = {}
                for item in object_data:
                    obj[item["name"]] = item["value"]
                list_of_objects.append(obj)
            return list_of_objects
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)

    async def list_divisions(self, divisionid):
        params = {'id': divisionid}
        API_HREF = f"https://api.teamsnap.com/v3/divisions/search"
        response = await self._get(API_HREF, params=params)

        if response.status_code == 200:
            print("list_divisions() was successful!\n")
            parsed_json = response.json()
            list_of_objects = []
            for object_item in parsed_json["collection"]["items"]:
                object_data = object_item["data"]
                obj = {}
                for item in object_data:
                    obj[item["name"]] = item["value"]
                list_of_objects.append(obj)
            return list_of_objects
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)

    async def list_members(self, team_id):
        params = {'team_id': team_id}
        API_HREF = f"https://api.teamsnap.com/v3/members/search"
        response = await self._get(API_HREF, params=params)

        if response.status_code == 200:
            print("list_members() was successful!")
            parsed_json = response.json()
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

    async def list_division_locations(self, divisionid):
        params = {'division_id': divisionid}
        API_HREF = f"https://api.teamsnap.com/v3/division_locations/search"
        response = await self._get(API_HREF, params=params)

        if response.status_code == 200:
            print("list_division_locations() was successful!\n")
            parsed_json = response.json()
            list_of_objects = []
            for object_item in parsed_json["collection"]["items"]:
                object_data = object_item["data"]
                obj = {}
                for item in object_data:
                    obj[item["name"]] = item["value"]
                list_of_objects.append(obj)
            return list_of_objects
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)

    async def list_teams(self, userid):
        params = {'user_id': userid}
        API_HREF = f"https://api.teamsnap.com/v3/teams/search"
        response = await self._get(API_HREF, params=params)

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

    async def list_events(self, userid=None, teamid=None):
        params = {
            'user_id': userid,
            'team_id': teamid
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        API_HREF = f"https://api.teamsnap.com/v3/events/search"
        response = await self._get(API_HREF, params=params)

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

    async def search_user(self, userid):
        params = {'id': userid}
        API_HREF = f"https://apiv3.teamsnap.com/users/search"
        response = await self._get(API_HREF, params=params)

        if response.status_code == 200:
            print("search_user() was successful!\n")
            parsed_json = response.json()
            try:
                print(f"id: is {parsed_json['collection']['items'][0]['data'][0]['value']}")
                print(f"email: {parsed_json['collection']['items'][0]['data'][5]['value']}")
                print(f"First Name: {parsed_json['collection']['items'][0]['data'][8]['value']}")
                print(f"Last Name: {parsed_json['collection']['items'][0]['data'][10]['value']}\n")
            except IndexError:
                print("User found but data structure unexpected.")
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)

    async def create_events(self, events_csv):
        list_of_events = self.csv_to_templates(events_csv)
        for event in list_of_events:
            API_HREF = f"https://api.teamsnap.com/v3/events"
            response = await self._post(API_HREF, json_data=event)

            if response.status_code in (200, 201, 204):
                print(f"{response.status_code} request successful!")
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)

    async def create_opponents(self, events_csv):
        list_of_opponents = self.csv_to_templates(events_csv)
        for opponent in list_of_opponents:
            API_HREF = f"https://api.teamsnap.com/v3/opponents"
            response = await self._post(API_HREF, json_data=opponent)

            if response.status_code in (200, 201, 204):
                print(f"{response.status_code} request successful!")
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)

    async def create_team_member(self, csv_file):
        list_of_members = self.csv_to_templates(csv_file)
        for member in list_of_members:
            API_HREF = f"https://api.teamsnap.com/v3/members"
            response = await self._post(API_HREF, json_data=member)

            if response.status_code in (200, 201, 204):
                print(f"{response.status_code} request successful!")
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)

    async def create_assignments(self, assignments_csv):
        list_of_assignments = self.csv_to_templates(assignments_csv)
        for assignment in list_of_assignments:
            API_HREF = f"https://api.teamsnap.com/v3/assignments"
            response = await self._post(API_HREF, json_data=assignment)

            if response.status_code in (200, 201, 204):
                print(f"{response.status_code} request successful!")
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)

    async def delete_opponents_by_ids(self, opponent_list):
        for opponent in opponent_list:
            API_HREF = f"https://api.teamsnap.com/v3/opponents/{opponent}"
            response = await self._delete(API_HREF)

            if response.status_code in (200, 201, 204):
                print(f"{response.status_code} request successful!")
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)

    async def delete_events_by_id(self, event_list):
        for event in event_list:
            API_HREF = f"https://api.teamsnap.com/v3/events/{event}"
            response = await self._delete(API_HREF)

            if response.status_code in (200, 201, 204):
                print(f"{response.status_code} request successful!")
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)

    async def delete_events_by_dict(self, events_dict):
        for event in events_dict:
            API_HREF = f"https://api.teamsnap.com/v3/events/{event['id']}"
            response = await self._delete(API_HREF)

            if response.status_code in (200, 201, 204):
                print(f"{response.status_code} request successful!")
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)

    @staticmethod
    def print_list(items, variables=None):
        if variables is None:
            variables = []
            
        print(f"************************")
        
        if variables:
            for item in items:
                for variable in variables:
                    print(f"{variable}: {item[variable]}")
                print("---------------------------------------------")
        else:
            for dict_item in items:
                for k,v in dict_item.items():
                    print(f"{k}: {v}")
                print("---------------------------------------------")
                    
    @staticmethod
    def json_to_csv(json_data, csv_filename):
        if not isinstance(json_data, list) or not all(isinstance(item, dict) for item in json_data):
            raise ValueError("Input JSON should be a list of dictionaries")
        headers = list(json_data[0].keys())
        with open(csv_filename, 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)
            writer.writeheader()
            for row in json_data:
                writer.writerow(row)
    
    @staticmethod
    def csv_to_templates(filename):
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            try:
                headers = next(reader)
            except StopIteration:
                return {"template": {"data": []}}

            number_of_columns = len(headers)
            data_list = []

            for values in reader:
                if values[0] in ("Mandatory", "Optional"):
                    continue
                row_data = []
                for i in range(number_of_columns):
                    value = values[i]
                    name = headers[i]
                    row_data.append({"name": name, "value": value})
                data_list.append({"template": {"data": row_data}})

        return data_list

    @staticmethod
    def print_members(memberList):
        print(f"Printing Members:")
        print(f"************************")
        for member in memberList:
            print(f"First Name: {member['first_name']}")
            print(f"Last Name: {member['last_name']}")
            email = member.get('email_addresses', 'N/A')
            print(f"Email address: {email}\n")

    @staticmethod
    def write_to_json_file(data, filename="output.json"):
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
