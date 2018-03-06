#!/usr/bin/env python3

from os import listdir
from requests import get, post
from datetime import datetime
from operator import itemgetter
from agavepy.actors import get_context

# global variables
default_d2s = 'Mb0L6kVeR60pQ'
biocontainers_url = 'https://quay.io/api/v1/repository?public=true&namespace=biocontainers'
storage_dir = '/work/projects/singularity/TACC/biocontainers/'

def get_most_recent_tag(repo):
    url = 'https://quay.io/api/v1/repository/biocontainers/' + repo
    r = get(url)
    assert r.status_code == 200, 'Status code for {} is {} != 200'.format(repo, r.status_code)

    tags = r.json()['tags']
    try:
        assert len(tags.keys()) > 0, 'No tags for {}'.format(repo)
    except:
        return

    tag_datetime_list = []
    for i in tags:
        datetime_str = tags[i]['last_modified'][5:-6]
        datetime_obj = datetime.strptime(datetime_str, '%d %b %Y %H:%M:%S')
        tag_datetime_list.append( (i, datetime_obj) )
    tag_datetime_list.sort(key=itemgetter(1), reverse=True)

    return tag_datetime_list[0][0]

def get_resync_info():
    '''Returns a list of tuples (repo, tag) of containers to resync'''

    # get Docker containers
    r = get(biocontainers_url)
    assert r.status_code == 200, 'Pulling biocontainers list failed: status code {}'.format(r.status_code)
    r = r.json()
    available = [ str(x['name']) for x in r['repositories'] ]

    # list Singularity images
    current = [ x[:-4] if x[-4:] == '.img' 
                       else x[:-8] if x[-8:] == '.img.bz2' 
                       else x 
                       for x in listdir(storage_dir) 
                     ]

    # get name, version of containers to be updated
    resync = [] # entries formatted as (repo, version)
    for i in available:
        most_recent_tag = get_most_recent_tag(i)
        if most_recent_tag is not None and '{}_{}'.format(i, most_recent_tag) not in current:
            resync.append( '{}:{}'.format(i, most_recent_tag) )
    return resync

def submit_jobs(containers, token, actorid=default_d2s, baseurl='https://api.sd2e.org'):
    '''Takes list of name:tag strings and submits them to provided d2s actor. Returns list of tuples formatted (name:tag, actorid, executionid)'''
    # init job submission variables
    headers = {'Authorization': 'Bearer {}'.format(token)}
    url = '{}/actors/v2/{}/messages'.format(baseurl, actorid)
    l = []

    # submit jobs
    for i in containers:
        data = [ ('message', '\'quay.io/biocontainers/{}\''.format(i)) ]
        r = post(url, headers=headers, data=data)
        r.raise_for_status()
        executionid = r.json()['result']['executionId']
        l.append( (i, actorid, executionid) )
    return l

if __name__ == '__main__':

    context = get_context()
    msg = context.message_dict
    d2s_actor = (msg.get('d2s_actor') if type(msg) is dict and msg.get('d2s_actor') is not None else default_d2s)

    # if msg.get_containers is set, only print names of containers to be updated
    if type(msg) is dict and msg.get('get_containers'):
        # get containers and print
        resync_containers = get_resync_info()
        print('\n'.join(resync_containers))

    # else if msg.make_containers is list, only update containers provided in list
    elif type(msg) is dict and type(msg.get('make_containers')) is list:
        job_info = submit_jobs(msg['make_containers'], context._abaco_access_token, actorid=d2s_actor, baseurl=context._abaco_api_server)
        print('\n'.join([' '.join(i) for i in job_info]))

    # else, do the full process
    else:
        resync_containers = get_resync_info()
        job_info = submit_jobs(resync_containers, context._abaco_access_token, actorid=d2s_actor, baseurl=context._abaco_api_server)
        print('\n'.join([' '.join(i) for i in job_info]))