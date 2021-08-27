import ipaddress
import socket
from concurrent.futures import TimeoutError

import uritools
from pebble import ProcessPool

from urlextract.cachefile import CacheFile


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
        :return: A tuple with the given host and its IP address
            (a string of the form '255.255.255.255') if found (e.g: host.com, '255.255.255.255')
        :rtype: tuple
        """
        tmp_url = host
        scheme_pos = host.find('://')
        if scheme_pos == -1:
            tmp_url = 'http://' + host

        url_parts = uritools.urisplit(tmp_url)
        tmp_host = url_parts.gethost()

        if isinstance(tmp_host, ipaddress.IPv4Address):
            return host, tmp_host

        try:
            return host, socket.gethostbyname(tmp_host)
        except socket.herror as err:
            if err.errno == 0:
                self._logger.info("Unable to resolve address {}: {}".format(tmp_host, err))
            else:
                self._logger.info(err)
        except Exception as err:
            self._logger.info(
                "Unknown exception during gethostbyname({}) {!r}".format(tmp_host, err))
        return host, ""

    def check(self, hosts):
        """
        Tries to get the IP address from a given host or list of hosts
        :param list hosts: the list of hosts to get IP from
        :return: a list of valid hosts.
        :rtype: list
        """
        results = list()
        invalid_hosts = list()
        with ProcessPool(max_workers=self.max_workers, max_tasks=self.max_tasks) as pool:
            future = pool.map(self._get_host, hosts, timeout=self._timeout)

            iterator = future.result()

            while True:
                try:
                    result = next(iterator)
                    if result[1]:
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
        return results

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
