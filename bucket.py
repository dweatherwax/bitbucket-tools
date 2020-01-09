import requests
import sys
import time
from optparse import OptionParser
import datetime

from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth


def getProjectList(baseUrl, auth):
    ''' Return list of project names '''
    r = requests.get(baseUrl+'projects/', auth=auth)
    print baseUrl
    print r
    projectList = []
    for project in r.json()['values']:
        projectList.append(project['key'])

    return projectList

def getRepoList(baseUrl, auth, projectList):
    ''' Given a set of projects, return the set of repo slug names within 
        those projects 
    '''
    repoList = []
    
    for project in projectList:
        start = 0
        lastPage = False

        while not lastPage:
            url = baseUrl+'projects/'+project+'/repos/'+'?start=' + str(start)
            r = requests.get(url, auth=auth)
            response = r.json()

            lastPage = response['isLastPage']
            if response.has_key('nextPageStart'):
                start = response['nextPageStart']
        
            for repo in response['values']:
                print "adding repo ", repo['slug']
                repoList.append((project, repo['slug']))

    return repoList


def getPullRequests(baseUrl, auth, slugList):
    ''' Given a set of project/slug names, return the list of active pull requests '''

    prList = []
    #prState = 'MERGED'
    prState = 'OPEN'

    for (projectName, repoName) in slugList:
        print ".",
        sys.stdout.flush()

        start = 0
        lastPage = False

        while not lastPage:
            url = baseUrl+'projects/'+projectName+'/repos/'+repoName+'/pull-requests?state='+prState+'&start=' + str(start)
            r = requests.get(url, auth=auth)

            response = r.json()
            lastPage = response['isLastPage']
            if response.has_key('nextPageStart'):
                start = response['nextPageStart']

            for pr in response['values']:
                #closedDate = pr['closedDate'] / 1000.0
                prList.append(pr)
                #print time.ctime(closedDate), "     ", pr['author']['user']['displayName'], "     ", pr['title']
                
    return prList

def printPRTable(pullRequests):
    ''' Pretty print a list of pull requests '''

    print '%10s' % "Author",
    print '( c,  o,  r)',
    print '%-20s' % "Updated",
    print '%-50s' % "Title",
    print '%-20s' % "Link"
    
    for pr in pullRequests:
        author = pr['author']['user']['name']
        title = pr['title']

        link = pr['links']['self'][0]['href']
        updated = time.strftime('%b %d %H:%M', time.localtime(pr['updatedDate']/1000.0))

        props = pr['properties']
        
        if props.has_key('commentCount'):
            comments = props['commentCount']
        else:
            comments = 0

        openTaskCount = props['openTaskCount']
        resolvedTaskCount = props['resolvedTaskCount']
            
        
        print '%10s' % author,
        print '(%2s, %2s, %2s) ' % (comments, openTaskCount, resolvedTaskCount),
        print updated, 
        print '%-50s' % title[0:40],
        print link

def sortPRList(prList):
    ''' Given a list of pull request objects, sort by date '''
    return sorted(prList, key= lambda pr : pr['updatedDate'], reverse=True)
     

if __name__ == "__main__":
    auth_user = None
    auth_password = None
    
    parser = OptionParser()
    parser.add_option("-u", "--user", dest='auth_user', help="user name")
    parser.add_option("-p", "--pass", dest='auth_password', help="password")
    parser.add_option("-a", "--address", dest='url', help='stash base url')
    (options, args) = parser.parse_args()

    auth = HTTPBasicAuth(options.auth_user, options.auth_password)
    base = 'https://'+options.url+'/rest/api/1.0/'

    print "Gathering data from the heavens. . .",
    sys.stdout.flush()
    
    projects = getProjectList(base, auth)
    print ".",
    sys.stdout.flush()
    
    repos = getRepoList(base, auth, projects)
    print ".",
    sys.stdout.flush()
    
    pullRequests = getPullRequests(base, auth, repos)
    print "."
    sys.stdout.flush()

    sortedPullRequests = sortPRList(pullRequests)
    printPRTable(sortedPullRequests)

    
    
