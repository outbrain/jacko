import logging

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from requests.packages.urllib3.util import Retry


class HistoryServerClient(object):
    """
    Client for History Server
    """

    DEFAULT_PORT = 19888

    def __init__(self, host, port=DEFAULT_PORT, start_time=None, timeout=30):
        """
        :param host: History Server host
        :param port: History Server port
        :param start_time: Get jobs with finish time beginning with this time in ms since epoch
        :param timeout: Timeout for requests
        """
        self.history_server_api_url = 'http://%s:%s/ws/v1/history/mapreduce/jobs' % (host, port)
        self.api_params = {'finishedTimeBegin': str(start_time)} if start_time else {}
        self.timeout = timeout
        self.session = requests.Session()
        retries = Retry(total=5,
                        backoff_factor=0.1,
                        status_forcelist=[500, 502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))

    def get_jobs(self):
        """
        Get the list of jobs from the History Server

        :return: The list of jobs returned from the History Server
        """
        logger = logging.getLogger(__name__)
        jobs_response = self.session.get(self.history_server_api_url, params=self.api_params, timeout=self.timeout)
        jobs_response.raise_for_status()
        jobs_json = jobs_response.json()["jobs"]
        if jobs_json is None:
            logger.warn("No jobs object returned from %s", self.history_server_api_url)
            return []
        return jobs_json["job"]

    def get_job(self, job_id):
        """
        Get an individual job from the History Server

        :param job_id: The job ID
        :return: The job object returned from the History Server
        """
        job_url = "%s/%s" % (self.history_server_api_url, job_id)
        try:
            response = self.session.get(job_url, timeout=self.timeout)
        except RequestException:
            logging.getLogger(__name__).exception("Invalid job returned for id %s", job_id)
            return {}
        json = response.json()
        if "job" in json:
            return json["job"]
        else:
            logging.getLogger(__name__).warn("Invalid job returned for id %s, status code %s: %s",
                                             job_id, response.status_code, response.content)
            return {}

    def __call__(self, job_id):
        return self.get_job(job_id)
