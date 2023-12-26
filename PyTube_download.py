import sys
import os
import re
import requests
import pytube
from moviepy.editor import AudioFileClip
from pathvalidate import sanitize_filename
import tkinter as tk
import tkinter.ttk as ttk
import traceback
#print(traceback.format_exc())

class DownloadHandler():
	toDownloadLinksFolder = 'toDownloadLinks'
	downloadedLinksFolder = 'downloadedLinks'
	downloadedFilesFolder = 'downloadedFiles'

	def __init__(self) -> None:
		pass

	def filterId(self, link):
		'''extract video id\n
		used for collecting urls from playlist'''
		#link = link.strip('\n')
		#pos = link.find("?v=")
		#return link[pos+3:pos+13+1]
		return re.search("(?:v=|\/)([0-9A-Za-z_-]{11})", link)[0][2:]

	def filterName(self, filename):
		'''make filename valid for windows\n
		used for dowloading'''
		filename = filename.replace('\n','')
		filename = sanitize_filename(filename)
#		filename = filename.lower()
		return filename

	def saveLinks(self, extractedLinks, newLinksFile):
		'''save inks to file in toDownloadLinksFolder'''
		newLinksPath = os.path.join(self.toDownloadLinksFolder,newLinksFile)
		with open(newLinksPath,"w",encoding='utf-8') as f:
			while extractedLinks:
				link = extractedLinks.pop()
				f.write('%s\n' % link)
		return None

	def loadLinks(self, linkPath):
		"""list links from linkPath"""
		links = list()
		with open(linkPath,"r",encoding='utf-8') as f:
			for line in f:
				line = line.strip('\n')
				links.append(line)
		return links

	def ListFiles(self, folder, fileEnding=None):
		"""list all files saved in folder\n
		(optionally with sspecific ending)"""
		fileList = list()
		for (dirpath, dirnames, filenames) in os.walk(folder):
			fileList.extend([os.path.join(dirpath,filename) for filename in filenames])
		
		if fileEnding==None:
			return fileList
		else:
			files = list()
			for file in fileList:
				for ending in fileEnding:
					if file[len(file)-len(ending):]==ending:
						files.append(file)
						break
			return files

	def listOfAllLinks(self, folder, fileEnding):
		"""list all links saved in folder in Dict"""
		links = list()
		for file in self.ListFiles(folder, fileEnding):
			links[file] = self.loadLinks(file)
		return links
	
	def dictOfAllLinks(self, folder, fileEnding):
		"""list all links saved in folder/files in List"""
		links = dict()
		for file in self.ListFiles(folder, fileEnding):
			links[file] = self.loadLinks(file)
		return links

	def collectLinks(self, playlistUrl):
		"""get all links from playlist"""
		playlist = pytube.Playlist(playlistUrl)
		links = playlist.video_urls
		return [self.filterId(link) for link in links]

	### get channel upload list
	def channelLinks(self, channelLink):
		
		#request channel page
		response = requests.get(channelLink)
		response.raise_for_status()
		body = response.text
		
		#extract playlist id
		keyword = "\"browseId\":\"UC"
		pos1 = body.find(keyword)+len(keyword)
		pos2 = body.find("\"",pos1)
		channelPlaylistUrl = "https://www.youtube.com/playlist?list=UU"
		channelPlaylistUrl += body[pos1:pos2]
		
		#extract channel name
		keyword = "\"name\": \""
		pos1 = body.find(keyword)+len(keyword)
		pos2 = body.find("\"",pos1)
		channelName = body[pos1:pos2]
		
		#load links
		linkFile = channelName+'.txt','w'
		channelLinks = self.collectLinks(channelPlaylistUrl)
		with open(linkFile,encoding='utf-8') as f:
			while channelLinks:
				link = channelLinks.pop()
				f.write('%s\n' % link)
		return linkFile
	
	#--- save execution

	def compareOldLinks(self, newLinksFile):
		"""compare links from newLinksFile to oldLinks"""
		newLinksPath = os.path.join(self.toDownloadLinksFolder,newLinksFile)
		oldLinks = self.dictOfAllLinks(self.downloadedLinksFolder,[".txt"])
		checkedLinks = list()
		duplicates = dict()
		
		#read all links
		newLinks = self.loadLinks(newLinksPath)
		newLinks = list(set(newLinks))
		
		#check all files on duplicates
		while newLinks:
			link = newLinks.pop()
			linkIsOld = False
			for oldLinksFile,oldLinksList in oldLinks.items():
				if link in oldLinksList:
					linkIsOld = True
					if link not in duplicates:
						duplicates[link] = [newLinksPath]
					duplicates[link].append(oldLinksFile)
			if not linkIsOld:
				checkedLinks.append(link)
		del newLinks

		#list all filePaths with duplicates
		allDuplicateFiles = set()
		for link,filePaths in duplicates.items():
			for filePath in filePaths:
				allDuplicateFiles.add(filePath)
		allDuplicateFiles = list(allDuplicateFiles)
		if newLinksPath in allDuplicateFiles:
			allDuplicateFiles.remove(newLinksPath)
		
		#decide what to do with duplicates
		keepLink = dict() #list of filePaths where to keep link
		deleteLink = dict() #list of filePaths where to delete link from
		for link,presentFiles in duplicates.items():
			keepLink[link] = presentFiles.pop(0)#keep them for now
			deleteLink[link] = presentFiles
		#keepLink["NFBP9nJkec8"] = 'downloadedLinks\\test2.txt'
		#deleteLink["NFBP9nJkec8"][0] = 'toDownloadLinks\\test.txt'
		del duplicates

		#edit files
		try:
			#add links to current file
			failed = list()
			try:
				with open(newLinksPath,'w',encoding='utf-8') as f:
					while checkedLinks:
						link = checkedLinks.pop()
						f.write('%s\n' % link)
			except Exception as ex:
				print('error on: ',link)
				print(ex)
				failed.append([link]+checkedLinks)
				raise
			del checkedLinks

			try:
				with open(newLinksPath,'a',encoding='utf-8') as f:
					for link,filePath in keepLink.copy().items():
						if filePath == newLinksPath:
							f.write('%s\n' % link)
							del keepLink[link]
			except Exception as ex:
				print('error on: ',link)
				print(ex)
				failed.append(list(keepLink.values()))
				raise
			
			#keepLink
				
			#remove links from all other files
			for duplicateFile in allDuplicateFiles: #choose one file
				print(duplicateFile)
				toRemove = list()
				for link,filePaths in deleteLink.items(): #loop over all links
					print(link)
					if duplicateFile in filePaths: #check if link is in choosen file
						toRemove.append(link)
				if toRemove:
					linkList = list() #read all links from file skippin links in roRemove
					with open(duplicateFile,'r',encoding='utf-8') as f: #read all links except toRemove
						for link in f:
							link = link.strip("\n")
							if link not in toRemove:
								linkList.append(link)
					for link,filePath in keepLink.copy().items(): #add keepLink links if not present already
						if filePath == duplicateFile:
							if link not in linkList:
								linkList.append(link)
							del keepLink[link]
					with open(duplicateFile+".temp",'w',encoding='utf-8') as f: #save links to temp
						for link in linkList:
							f.write('%s\n' % link)
					#if successful: replace duplicateFile with duplicateFile+".temp"
					os.replace(duplicateFile+".temp",duplicateFile)
		except KeyboardInterrupt:
			print('Interrupted')
			with open(newLinksPath,'w',encoding='utf-8') as ff:
				for item in failed:
					item = item.strip('\n')
					ff.write('%s\n' % item)
			sys.exit(0)

		return None

	### download loop
	def downloadFiles(self, newLinksFile, downloadOnlyAudio=True):
		newLinksPath = os.path.join(self.toDownloadLinksFolder,newLinksFile)
		failed = list()
		try:
			with open(newLinksPath,'r',encoding='utf-8') as f:
				with open(os.path.join(self.downloadedLinksFolder,newLinksFile),'w',encoding='utf-8') as ff:
					url_list = f.readlines()
					numElements = len(url_list)
					for iter in range(numElements):
						print('-----'+str(iter+1)+'/'+str(numElements)+'-----')
						line = url_list.pop()
						line = line.strip('\n')
						try:
							print('downloading: ',line)
							vid = pytube.YouTube( "http://youtube.com/watch?v="+line )
							if downloadOnlyAudio:
								stream = vid.streams.get_audio_only() #also possible method: .filterName(only_audio=True)[0]
							else:
								stream = vid.streams.filter(progressive=True).get_highest_resolution() #legacy: audio & video combined -> lower quality
								#for highest video quality download video and audio separate [.filterName(adaptive=True)] and recombine (e.g. with ffmpeg)
								'''
								import ffmpeg
								input_video = ffmpeg.input('./test/test_video.webm')
								input_audio = ffmpeg.input('./test/test_audio.webm')
								ffmpeg.concat(input_video, input_audio, v=1, a=1).output('./processed_folder/finished_video.mp4').run()
								'''
							#download
							#stream.download(self.downloadedFilesFolder)
							pos = stream.default_filename.rindex(".")
							filename = self.filterName( stream.default_filename[:pos] )
							filename += "("+str(line)+")"
							filename += stream.default_filename[pos:]
							stream.download( filename = os.path.join(self.downloadedFilesFolder,filename) )
							ff.write('%s\n' % line)
						except Exception as ex:
							print('error on: ',line)
							print(ex)
							failed.append(line)
							raise
		except KeyboardInterrupt:
			print('Interrupted')
			with open(newLinksPath,'w',encoding='utf-8') as fff:
				for item in (url_list+failed):
					item = item.strip('\n')
					fff.write('%s\n' % item)
			sys.exit(0)
	
	def mp4TOmp3(self):
		#find all mp4 files
		arr = os.listdir()
		if len(arr) > 0:
			for n in range(len(arr)-1,-1,-1):
				if arr[n][-4:]!='.mp4':
					arr.pop(n)

			#convert to mp3
			while len(arr)>0:
				filename = arr.pop(0)
				audioclip = AudioFileClip(filename)
				audioclip.write_audiofile(filename[:-4]+'.mp3')
				print('---removing: ',filename)
				os.remove(filename)

			audioclip.close()
		else:
			print('no .pm4 files left !')


def doStuff():
	return None

### GUI

#empty window
root = tk()

#download all links -> loop over all toDownloadFiles
#-----
#list downloaded playlists/channels
#extract new links from playlists/channels
#file -> remove downloaded links

#content: frame2 (login)
frame2= tk.Frame(root, width=400, height=200)
#frame2.pack_propagate(0)
frame2.grid_propagate(0)
frame2.pack()
label5 = tk.Label(frame2, text='Name')
label6 = tk.Label(frame2, text='Password')
entry1 = tk.Entry(frame2)
entry2 = tk.Entry(frame2)
submitb = tk.Button(frame2, text='submit', command=print("test"))

label5.grid(row=0,column=0, sticky=tk.E) #NESW
label6.grid(row=1,column=0, sticky=tk.E)
entry1.grid(row=0,column=1)
entry2.grid(row=1,column=1)
submitb.grid(row=4,columnspan=2)

'''
response = Label(frame2, text=' ')
response.grid(row=5,columnspan=2)

if answer=='yes':
	print('you said yes')
else:
	print('you said no')

#keep window open
root.mainloop()

url = "https://www.youtube.com/@wavemusic"
"browseId":"UCbuK8xxu2P_sqoMnDsoBrrg"
"https://www.youtube.com/playlist?list=UU"+"buK8xxu2P_sqoMnDsoBrrg"

url = "https://www.youtube.com/@AirwaveMusicTV/videos"
"browseId":"UCwIgPuUJXuf2nY-nKsEvLOg"
"https://www.youtube.com/playlist?list=UU"+"wIgPuUJXuf2nY-nKsEvLOg"
'''


'''
#if __name__ == "__main__":
session = DownloadHandler()
newLinksFile = "test.txt"#input("path to new links file")
playlistUrl = "https://www.youtube.com/playlist?list=PLndEULTswG5aTuZ4gGTCZ-PWx3JUCFjyk"#input("url to youtube playlist")#

extractedLinks = session.collectLinks(playlistUrl)
session.saveLinks(extractedLinks, newLinksFile)
session.compareOldLinks(newLinksFile)
audioOnly = True
session.downloadFiles(newLinksFile,audioOnly)
'''

