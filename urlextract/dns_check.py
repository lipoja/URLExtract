from urlextract.cachefile import CacheFile
import socket
from pebble import ProcessPool
from concurrent.futures import TimeoutError


class DNSCheck(CacheFile):
    def __init__(self, timeout=5, accept_on_timeout=False, max_workers=2, max_tasks=2, cache=True, **kwargs):
        super(DNSCheck, self).__init__(**kwargs)
        self._timeout = timeout
        self._accept_on_timeout = accept_on_timeout
        self._max_workers = max_workers
        self._max_tasks = max_tasks
        self._cache = cache
        if self._cache:
            self._cache_install()

    @property
    def timeout(self):
        """
        The timeout for checking DNS by hostname
        :rtype: int
        """
        return self._timeout

    @timeout.setter
    def timeout(self, timeout: int):
        """
        Set the timeout for checking DNS by hostname
        :param int timeout: The max time an operation could use to check DNS
        """
        self._timeout = timeout

    @property
    def accept_on_timeout(self):
        """
        Defines if an url should be considered valid in case of timeout
        :rtype: bool
        """
        return self._accept_on_timeout

    @accept_on_timeout.setter
    def accept_on_timeout(self, accept: bool):
        """
        Set if an url should be considered valid in case of timeout
        :param int accept: True if an url is valid on timeout False otherwise
        """
        self._accept_on_timeout = accept

    @property
    def max_workers(self):
        """
        The max number of workers used for checking DNS by hostname
        :rtype: int
        """
        return self._max_workers

    @max_workers.setter
    def max_workers(self, max_workers: int):
        """
        Set the max number of workers for checking DNS by hostname
        :param int max_workers: The max numbers of workers(operations) DNSCheck could spawn
        """
        self._max_workers = max_workers

    @property
    def max_tasks(self):
        """
        The max number of tasks used for checking DNS by hostname
        :rtype: int
        """
        return self._max_tasks

    @max_tasks.setter
    def max_tasks(self, max_tasks: int):
        """
        Set the max number of tasks for checking DNS by hostname
        :param int max_tasks: The max numbers of tasks(threads) DNSCheck could spawn
        """
        self._max_tasks = max_tasks

    def _get_host(self, host: str):
        """
         Get the IP address from a given host
        :param str host: the host to get IP from
        :return: The IP address (a string of the form '255.255.255.255') for a host.
        """
        try:
            return host, socket.gethostbyname(host)
        except socket.herror as err:
            if err.errno == 0:
                self._logger.info("Unable to resolve address {}: {}".format(host, err))
            else:
                self._logger.info(err)
        except Exception as err:
            self._logger.info(
                "Unknown exception during gethostbyname({}) {!r}".format(host, err))
        return

    def check(self, host=None, hosts=None):
        """
        Tries to get the IP address from a given host or list of hosts
        :param str host: the host to get IP from
        :param list hosts: the list of hosts to get IP from
        :return: True if the IP was retrieved successfully False otherwise.
        """
        results = list()
        invalid_hosts = list()
        if not hosts:
            hosts = [host]
        with ProcessPool(max_workers=self.max_workers, max_tasks=self.max_tasks) as pool:
            future = pool.map(self._get_host, hosts, timeout=self._timeout)

            iterator = future.result()

            while True:
                try:
                    result = next(iterator)
                    if result:
                        results.append(result[0])
                        continue
                    invalid_hosts.append(result[0])
                except StopIteration:
                    break
                except TimeoutError:
                    pass
        if self.accept_on_timeout:
            # if a host is nether valid nor invalid its process timed out
            for host in hosts:
                if host not in results and host not in invalid_hosts:
                    results.append(host)
        return True

    @staticmethod
    def _cache_install():
        try:
            from dns_cache.resolver import ExceptionCachingResolver
            from dns import resolver as dnspython_resolver_module
            if not dnspython_resolver_module.default_resolver:
                dnspython_resolver_module.default_resolver = ExceptionCachingResolver()
            del dnspython_resolver_module
        except ImportError:
            pass

        try:
            from dns.resolver import LRUCache, Resolver, override_system_resolver, _resolver, default_resolver
        except ImportError:
            return

        if default_resolver:
            if not default_resolver.cache:
                default_resolver.cache = LRUCache()
            resolver = default_resolver
        elif _resolver and _resolver.cache:
            resolver = _resolver
        else:
            resolver = Resolver()
            resolver.cache = LRUCache()
        override_system_resolver(resolver)
