'''
FAZ.NET Video Addon

Created on Oct 12, 2013

@author: ianusmagnus
'''

import json
import socket
import re
import sys
import urllib2
import xbmc
import xml.etree.ElementTree as ET
import os 


#addon id - name of addon directory
_id = 'plugin.video.faznet'

#add our library to python search path
sys.path.append (xbmc.translatePath( "special://home/addons/" + _id + "/resources/lib"))

# import utitily module
import util

WEB_PAGE_BASE = "http://www.faz.net"

def playVideo(params):
    util.playMedia(params['title'], params['image'], params['video'], 'Video')
   
def fetchFromUrl(url):
    try:
        response = urllib2.urlopen(url, timeout = 30)
        if response and response.getcode() == 200:
            return response.read() 
        else:
            util.showError(_id, 'Could not open URL %s to create menu' % (url))
    except socket.timeout, e:
        log("got timeout error: %r" % e)
        util.showError(_id, 'Could not open URL %s to create menu' % (url))
        
def buildMenu():
    url = WEB_PAGE_BASE + "/multimedia/videos/"
    content = fetchFromUrl(url)
    if content is not None:             
        parseRessorts(content)
   

def buildSubMenu(inputParams):    
    ressort = inputParams['ressort'].replace(".", "-")
    offset = int(inputParams['offset'])
    fetchsize = int(inputParams['fetchsize'])
    
    videoCount = 0
    
    for x in range(0, fetchsize):
        url = "{0}/multimedia/videos/ressort-{1}/?ot=de.faz.ot.www.teaser.more.mmo&type=VIDEO&offset={2}".format(WEB_PAGE_BASE, ressort, str(offset + x)) 
        log("fetch ressorts: {0}".format(url))
        content = fetchFromUrl(url)
        
        if content is not None:
            videoCount = videoCount + parseVideos(content)
       
    # add 'next' menu item if more videos available
    if videoCount > 0:
        params = {'title':'Next Page', 'ressort':inputParams['ressort'], 'fetchsize':inputParams['fetchsize']}
        params['offset'] = offset + fetchsize
        link = util.makeLink(params)
        util.addMenuItem(params['title'], link)
    
    # add 'main menu' item
    params = {'title':'Main Menu'}
    link = util.makeLink(params)
    util.addMenuItem(params['title'], link)
      
    util.endListing()
   
    
def parseRessorts(content):
    for x in re.findall(r"<a.*fazAjaxContentChanger.*ressort=(\d\.\d*).*>(.*)</a>", content):
        params = {}
        params['title'] = x[1]
        params['ressort'] = x[0]
        params['offset'] = 0
        params['fetchsize'] = 3
        
        link = util.makeLink(params)
        util.addMenuItem(params['title'], link)
    util.endListing()
     
def parseVideos(content):
    matchList = re.findall(r"-(\d{8}).html", content)
    videoCount = 0
    
    for videoId in set(matchList):
        videoCount = videoCount + 1
        url = WEB_PAGE_BASE + "/videoxml?id=" + videoId[0] + "." + videoId[1:]
        log('fetch mediaXml: {}'.format(url)) 
       
        response = urllib2.urlopen(url)
        if response and response.getcode() == 200:
            content = response.read()       
            params = parseMediaXML(content)
            params['play'] = 1
        
            link = util.makeLink(params)
            util.addVideoMenuItem(params['title'], params['duration'], link, 'DefaultVideo.png', params['image'], False)
        else:
            util.showError(_id, 'Could not open URL %s to create menu' % (url))
        
    return videoCount
    
def parseMediaXML(content):
    params = {}
    root = ET.fromstring(content)
    
    # parse video link and duration
    for enc in ('HQ', 'HIGH', 'LOW'):
        child = root.find('./ENCODINGS/' + enc)
        if child is not None:
            for item in child.findall('./FILENAME'):
                params['video'] = item.text
            
            for item in child.findall('./DURATION'):
                m, s = divmod(int(item.text), 60)
                params['duration'] = "%d:%02d" % (m, s)
        if 'video' in params:
            break
    
    # parse image
    image = root.find('./STILL/STILL_BIG')
    if image is not None:
        params['image'] = image.text
        
    #parse title
    title =  root.find('./VIDEO_COUNT_URL')
    if title is not None:
        try:
            info = json.loads(title.text)
            params['title'] = info['cn']
        except (ValueError, TypeError):
            # raise if json string is invalid
            params['title'] = 'Unknown'
        
    return params   

def log(msg):
    xbmc.log(_id + ': ' + msg, level=xbmc.LOGDEBUG)    

if __name__ == '__main__':
    parameters = util.parseParameters()
    if 'play' in parameters:
        playVideo(parameters)
    elif 'ressort' in parameters:
        buildSubMenu(parameters)
    else:
        buildMenu()

