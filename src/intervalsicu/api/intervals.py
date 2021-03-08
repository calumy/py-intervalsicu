import requests
import datetime

from .error import CredentialError
from .workout import WorkoutDoc
from .activity import Activity
from .wellness import Wellness


class Intervals(object):
    URL = "https://intervals.icu"

    def __init__(self, athlete_id, api_key, session=None):
        self.athlete_id = athlete_id
        self.password = api_key
        self.session = session

    def _get_session(self):
        if self.session is not None:
            return self.session

        self.session = requests.Session()

        self.session.auth = ('API_KEY', self.password)
        return self.session

    def _make_request(self, method, url, params=None, json=None):
        session = self._get_session()
        res = session.request(method, url, params=params)
        if res.status_code == 401:
            raise CredentialError(status=res.status_code, message="Unauthorized", url=res.url)
        if res.status_code == 403:
            raise ClientError(status=res.status_code, message="Error access resource", url=res.url)

        return res

    def activities(self):
        """
        CSV formatted API call

        :return: Text data in CSV format
        """
        url = "{}/api/v1/athlete/{}/activities.csv".format(Intervals.URL, self.athlete_id)
        res = self._make_request("get", url)
        return res.text

    def activity(self, activity_id):
        """
        Activity by ID

        :param: Activity id number
        :return: Activity Object
        """
        url = "{}/api/v1/activity/{}".format(Intervals.URL, activity_id)
        res = self._make_request("get", url)
        return Activity(**res.json())

    def wellness(self, start_date, end_date=None):
        """
        Wellness by date, or range of dates.
        A single date will return a wellness object for that day.
        Specifying two dates (start and end) will return all wellness
        objects within the range.

        :param: Starting date (or single date)
        :param: End date (or omit if only requesting a single date)
        :return: List of Wellness objects
        """
        if type(start_date) is not datetime.date:
            raise TypeError("datetime required")

        params = {}

        if end_date is not None:
            if type(end_date) is not datetime.date:
                raise TypeError("datetime required")

            params['oldest'] = start_date.isoformat()
            params['newest'] = end_date.isoformat()
            url = "{}/api/v1/athlete/{}/wellness".format(Intervals.URL, self.athlete_id)
        else:
            url = "{}/api/v1/athlete/{}/wellness/{}".format(Intervals.URL, self.athlete_id, start_date.isoformat())

        res = self._make_request("get", url, params)
        j = res.json()
        if type(j) is list:
            result = []
            for item in j:
                result.append(Wellness(**item))
            return result

        return Wellness(**j)

    def wellness_put(self, data):
        """
        Update a wellness object.

        :param: Wellness object
        :return: The updated wellness object
        """
        if type(data) is not Wellness:
            raise TypeError("Expected Wellness object")

        date = data['id']
        url = "{}/api/v1/athlete/{}/wellness/{}".format(Intervals.URL, self.athlete_id, date)
        res = self._make_request("put", url, json=data)
        return Wellness(**res.json())

    def folders(self):
        """
        Retrieve a list of workout folders

        :return: List of Folder objects
        """
        url = "{}/api/v1/athlete/{}/folders".format(Intervals.URL, self.athlete_id)
        res = self._make_request("get", url)
        folders = []
        for f in res.json():
            folders.append(Folder(**f))

        return folders


def _recur(o, indent=0):
    for key, val in o.items():
        if type(val) is list:
            for item in val:
                recur(item, indent+1)
        elif type(val) is dict:
            recur(o[key], indent+1)