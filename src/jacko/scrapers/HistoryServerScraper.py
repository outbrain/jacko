import logging
from datetime import datetime
from multiprocessing import Pool

from Scraper import Scraper


class JobScraper(object):
    """
    Scraper for individual jobs from History Server
    """

    def __init__(self, history_server_client):
        """
        :param history_server_client: HistoryServerClient initialized with the History Server details
        """
        self.history_server_client = history_server_client

    def scrape(self, job_id):
        """
        Get an individual job from the History Server. A "timestamp" field is added with
        the time of the scrape.

        :param job_id: Job ID
        :return: Job from the History Server
        """
        job = self.history_server_client(job_id)
        job["timestamp"] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        return job

    def __call__(self, job_id):
        return self.scrape(job_id)


class HistoryServerScraper(Scraper):
    """
    Scraper for History Server that requests individual jobs in parallel
    """
    def __init__(self, history_server_client, max_pool_size=16):
        """
        :param history_server_client: HistoryServerClient initialized with the History Server details
        :param max_pool_size: maximum pool size for parallel requests to the History Server
        """
        super(HistoryServerScraper, self).__init__()
        self.history_server_client = history_server_client
        self.job_scraper = JobScraper(self.history_server_client)
        self.max_pool_size = max_pool_size
        self.logger = logging.getLogger(__name__)
        self.logger.debug("HistoryServerScraper created for url %s", self.history_server_client.history_server_api_url)

    def scrape_all_jobs(self, job_ids):
        """
        Scrape each job from a list of job IDs in parallel

        :param job_ids: List of job IDs
        :return: List of job objects from History Server
        """
        pool_size = min(self.max_pool_size, len(job_ids))
        self.logger.debug("Fetching individual jobs, pool size is %d", pool_size)
        pool = Pool(pool_size)
        jobs = pool.map(self.job_scraper, job_ids)
        pool.close()
        pool.join()
        return jobs

    def get_job_ids(self):
        """
        Get a list of jobs from the History Server and return a list of the job IDs

        :return: List of job ids
        """
        jobs = self.history_server_client.get_jobs()
        job_ids = [job["id"] for job in jobs]
        return job_ids

    def scrape(self):
        """
        Return all jobs from the History Server

        :return: List of job objects returned from the History Server
        """
        job_ids = list(self.get_job_ids())
        jobs_count = len(job_ids)
        self.logger.debug("History Server returned %d jobs", jobs_count)
        if jobs_count < 1:
            return []
        jobs = self.scrape_all_jobs(job_ids)
        jobs = [job for job in jobs if "id" in job]
        self.logger.debug("Got %d jobs from History Server", len(jobs))
        return jobs


Scraper.register(HistoryServerScraper)
