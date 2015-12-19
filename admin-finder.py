#!/usr/bin/env python

import Queue
import threading
import time
import urllib
import os
import re


stateLock = threading.Lock()


class website:
    """
    This class handles URL formatting
    And checking if the website is online
    """

    def __init__(self, data):
        site = data
        if not data.startswith("http"):
            site = "http://" + site
        if not site.endswith("/"):
            site = site + "/"
        self.address = site

        print("[?] Checking if is website online")
        statusCode = self.checkStatus(self.address)
        if statusCode == 200:
            print("[+] Website seem online!")
        elif statusCode == 404:
            print("[-] Website seem down")
            exit()
        else:
            print("[?] Received HTTP Code : ", statusCode)
            exit()

        self.checkRobot(self.address)

    def checkStatus(self, address):
        """ This function returns the status of the website """
        try:
            return urllib.urlopen(address).getcode()
        except IOError:
            print("[!] Something wrong with your address")
            exit()


    def checkRobot(self,address):
        """
        This function is to check if robots.txt/robot.txt exist and see if the
        Admin path is already in there
        """
        print("[?] Checking for robot file")
        path = ["robot.txt","robots.txt"]
        urls = [address + i for i in path]

        for url in urls:
            statusCode = self.checkStatus(url)
            if statusCode == 200:
                print("\n[+] %s \n[+] Exists, reading content" % url)
                info = self.parseDir(url)
                if info:
                    print("[=] Interesting Information found in robot file")
                    print("="*80)
                    for line in info:
                        print "\t"+line
                    print("="*80)
                else:
                    print("[-] Nothing useful found in robot file")

    def getPage(self,address):
        return urllib.urlopen(address).readlines()

    def parseDir(self,address):
        DirPattern = re.compile(r".+: (.+)\n")
        interestingInfo = []
        dirs = []
        keyword = ["admin","Administrator","login","user","controlpanel",
                   "wp-admin","cpanel","userpanel","client","account"]
        """
        Disallow: /edu/cs4hs/
        Disallow: /trustedstores/s/
        Disallow: /trustedstores/tm2
        Disallow: /trustedstores/verify
        Disallow: /adwords/proposal
        """
        page = self.getPage(address)
        for line in page:
            if DirPattern.findall(line):
                dirs.append(DirPattern.findall(line)[0])

        for key in keyword:
            for directory in dirs:
                if key in directory:
                    interestingInfo.append(directory)
        return interestingInfo

class wordlist:
    """ This function loads the wordlsit """
    def __init__(self):
        try:
            self.load = [i.replace('\n', '') for i in open('wordlist.txt').readlines()]
        except IOError:
            print("[!] I/O Error, wordlist.txt not found")


class scanThread(threading.Thread):
    """ This class is the blueprint used to generate threads """
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.queue = q
        #self.run()

    def run(self):
        while not self.queue.empty():
        # While queue is not empty, which means there is work to do
            stateLock.acquire()
            url = self.queue.get()
            stateLock.release()
            if self.online(url):
                stateLock.acquire()
                print("\n\n[+] Admin page found in %.2f seconds" % (time.time() - starttime))
                print("[=] %s" % url)
                raw_input("[+] Press Enter ")
                print("[+] Exiting Program")
                os._exit(1)

            else:
                stateLock.acquire()
                print("[-] Tried : %s" % url)
                stateLock.release()
            self.queue.task_done()
            # Release task completed status

    def online(self, url):
        """ Returns True if the url is online AKA HTTP status code == 200 """
        try:
            return urllib.urlopen(url).getcode() == 200
        except IOError:
            stateLock.acquire()
            print("[!] Name Resolution Error")
            stateLock.release()


def main():
    try:
        pathlist = wordlist().load
        # loads the wordlist
        address = website(raw_input("[+] Website to scan : ")).address
        mainApp(address, pathlist)
        # Runs the main Application
    except KeyboardInterrupt:
        print("\n[~] Ctrl + C Detected!")
        print("[~] Exiting")
        exit()


class mainApp:
    def __init__(self,address,plist):
        self.address = address
        self.wordlist = plist
        self.createJobs()
        self.run()

    def createJobs(self):
        """
        Joins website address with the admin paths from wordlist
        and add it to queue
        """
        self.queue = Queue.Queue()
        stateLock.acquire()
        for path in self.wordlist:
            self.queue.put(self.address + path)
        stateLock.release()

    def run(self):
        threadCount = raw_input("[+] Enter number of threads [10]: ")
        if not threadCount:
            print("[=] Number of threads = 10")
            threadCount = 20
        else:
            print("[=] Number of threads = %d" % int(threadCount))
        threadList = []
        global starttime
        starttime = time.time()

        for i in range(0, int(threadCount)):
            thread = scanThread(self.queue)
            thread.setDaemon(True)
            thread.start()
            threadList.append(thread)

        # Waiting for all threads to finish
        self.queue.join()
        print("\n\n[-] Admin page not found!")
        for thread in threadList:
            thread.join()
        exit()

if __name__ == "__main__":
    main()
