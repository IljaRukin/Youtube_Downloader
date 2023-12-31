import sys
import os
import re
import requests
import pytube
from moviepy.editor import AudioFileClip
from pathvalidate import sanitize_filename
import tkinter as tk
import tkinter.filedialog
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
	def downloadFiles(self, newLinksFile, downloadOnlyAudio=True, authenticate=False):
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
							if authenticate:
								vid = pytube.YouTube("http://youtube.com/watch?v="+line,
														 use_oauth=True, allow_oauth_cache=True)
							else:
								vid = pytube.YouTube("http://youtube.com/watch?v="+line)
							if downloadOnlyAudio:
								#stream = vid.streams.filter(only_audio=True).order_by('resolution').desc().first()
								stream = vid.streams.filter(only_audio=True).get_audio_only()
							else:
								#stream = vid.streams.filter(progressive=True).order_by('abr').desc().first()
								stream = vid.streams.filter(progressive=True).get_highest_resolution()
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

### GUI

class Gui(tk.Tk):
	def __init__(self):
		self.session = DownloadHandler()
		
		super().__init__()
		self.title("Youtube Downloader")

		log_frame = tk.Frame(self)#, width=300, height=200
		log_frame.pack(side = tk.TOP, padx='5', pady='5')
		log_frame.rowconfigure(0, weight=1)
		log_frame.columnconfigure(0, weight=1)
		
		#log output
		textbox = tk.Text(log_frame, height=6)
		textbox.pack(side = tk.TOP)
		textbox.insert('1.0', "...")
		textbox.config(state='disabled')
		scrollb = tk.Scrollbar(log_frame, command=textbox.yview)
		textbox.config(yscrollcommand=scrollb.set)
		
		useAuthentication_frame = tk.Frame(self)
		useAuthentication_frame.pack(side = tk.TOP, padx='5', pady='5')

		tk.Label(useAuthentication_frame, text="use authentication when downloading ?").pack(side = tk.TOP)

		#radiobutton video/audio -> filename video/audio
		self.useAuthentication = tk.IntVar()
		tk.Radiobutton(useAuthentication_frame,
					text="yes authenticate",
					padx = 20,
					variable=self.useAuthentication,
					value=True,
					command=self.hideMediaSelectionFrame).pack(side = tk.LEFT)
		tk.Radiobutton(useAuthentication_frame,
					text="no authentication",
					padx = 20,
					variable=self.useAuthentication,
					value=False,
					command=self.showMediaSelectionFrame).pack(side = tk.LEFT)
		self.useAuthentication.set(False)
		
		processingType_frame = tk.Frame(self)
		processingType_frame.pack(side = tk.TOP, padx='5', pady='5')

		tk.Label(processingType_frame, text="link extraction or media download ?").pack(side = tk.TOP)

		#radiobutton video/audio -> filename video/audio
		self.extractOnly = tk.IntVar()
		tk.Radiobutton(processingType_frame,
					text="extract",
					padx = 20,
					variable=self.extractOnly,
					value=True,
					command=self.hideMediaSelectionFrame).pack(side = tk.LEFT)
		tk.Radiobutton(processingType_frame,
					text="download",
					padx = 20,
					variable=self.extractOnly,
					value=False,
					command=self.showMediaSelectionFrame).pack(side = tk.LEFT)
		self.extractOnly.set(False)
		
		self.mediaSelection_frame = tk.Frame(self)
		self.mediaSelection_frame.pack(side = tk.TOP, padx='5', pady='5')

		tk.Label(self.mediaSelection_frame, text="for download select media output format:").pack(side = tk.TOP)

		#radiobutton video/audio -> filename video/audio
		self.audioOnly = tk.IntVar()
		tk.Radiobutton(self.mediaSelection_frame,
					text="audio",
					padx = 20,
					variable=self.audioOnly,
					value=True).pack(side = tk.LEFT)
		tk.Radiobutton(self.mediaSelection_frame,
					text="video",
					padx = 20,
					variable=self.audioOnly,
					value=False).pack(side = tk.LEFT)
		self.audioOnly.set(True)
		
		#link	 -> extract/download
		self.link_frame = tk.Frame(self)
		self.link_frame.pack(side = tk.TOP, padx='5', pady='5')

		self.link = tk.StringVar()
		self.link_entry = tk.Entry(self.link_frame, textvariable = self.link,
								 font=('calibre',10,'normal'), width = 50)
		self.link_entry.pack(side = tk.LEFT, padx='5', pady='5')
		self.link_button = tk.Button(self.link_frame, command=self.processLink,
									 text='one Link', width = 14)
		self.link_button.pack(side = tk.LEFT, padx='5', pady='5')

		#playlist -> extract/download
		self.playlist_frame = tk.Frame(self)
		self.playlist_frame.pack(side = tk.TOP, padx='5', pady='5')

		self.playlist = tk.StringVar()
		self.link_entry = tk.Entry(self.playlist_frame, textvariable = self.playlist,
								 font=('calibre',10,'normal'), width = 50)
		self.link_entry.pack(side = tk.LEFT, padx='5', pady='5')
		self.playlist_button = tk.Button(self.playlist_frame, command=self.processPlaylist,
									 text='full Playlist', width = 14)
		self.playlist_button.pack(side = tk.LEFT, padx='5', pady='5')
		
		#channel	-> extract/download
		self.channel_frame = tk.Frame(self)
		self.channel_frame.pack(side = tk.TOP, padx='5', pady='5')

		self.channel = tk.StringVar()
		self.channel_entry = tk.Entry(self.channel_frame, textvariable = self.channel,
								 font=('calibre',10,'normal'), width = 50)
		self.channel_entry.pack(side = tk.LEFT, padx='5', pady='5')
		self.channel_button = tk.Button(self.channel_frame, command=self.processChannel,
									text='Channel uploads', width = 14)
		self.channel_button.pack(side = tk.LEFT, padx='5', pady='5')
		
		#----------
		
		ttk.Separator(self, orient='horizontal').pack()
		
		#extracted Linklist	 -> download
		self.file_frame = tk.Frame(self)
		self.file_frame.pack(side = tk.TOP, padx='5', pady='5')

		self.file = tk.StringVar()
		self.file_entry = tk.Entry(self.file_frame, textvariable = self.file,
								 font=('calibre',10,'normal'), width = 50)
		self.file_entry.pack(side = tk.LEFT, padx='5', pady='5')
		self.file_entry.bind("<1>", self.browseFiles)
		self.file_button = tk.Button(self.file_frame, command=self.processFile,
									 text='download specific extracted', width = 24)
		self.file_button.pack(side = tk.LEFT, padx='5', pady='5')

		#all Linklists	-> extract/download
		self.allFiles_frame = tk.Frame(self)
		self.allFiles_frame.pack(side = tk.TOP, padx='5', pady='5')

		self.allFiles_button = tk.Button(self.allFiles_frame, command=self.processAllFiles,
									 text='download All extracted', width = 24)
		self.allFiles_button.pack(side = tk.LEFT, padx='5', pady='5')

		#----------

		self.link.set("https://www.youtube.com/watch?v=dOVvmUqmRCk")
		self.playlist.set("https://www.youtube.com/playlist?list=UUwIgPuUJXuf2nY-nKsEvLOg")
		self.channel.set("https://www.youtube.com/channel/UCwIgPuUJXuf2nY-nKsEvLOg")
		self.file.set("C:/Users/User/Downloads/Youtube_Downloader/toDownloadLinks/test.txt")
		
	def hideMediaSelectionFrame(self):
		self.mediaSelection_frame.pack_forget()
			
	def showMediaSelectionFrame(self):
		self.mediaSelection_frame.pack(side = tk.TOP, padx='5', pady='5',
							before=self.file_frame)
		
	def browseFiles(self, event):
		filename = tk.filedialog.askopenfilename(initialdir = "./toDownloadLinks",
					  title = "Select Link file",
					  filetypes = (("Text files",
							"*.txt*"),
							   ("all files",
							"*.*")))
		self.file.set(filename)
		return None
	
	def processFile(self):
		'''
		extractedLinks = session.collectLinks(playlistUrl)
		session.saveLinks(extractedLinks, newLinksFile)
		session.compareOldLinks(newLinksFile)
		audioOnly = self.audioOnly.get()
		authenticate = self.useAuthentication.get()
		session.downloadFiles(newLinksFile, audioOnly, authenticate)
		'''
		
	def processLink(self):
		if self.extractOnly.get():
			print("extracting link: "+str(self.file.get()))
		else:
			print("downloading link: "+str(self.file.get()))
		extractedLinks = session.collectLinks(playlistUrl)
		session.saveLinks(extractedLinks, newLinksFile)
		session.compareOldLinks(newLinksFile)
		audioOnly = self.audioOnly.get()
		authenticate = self.useAuthentication.get()
		session.downloadFiles(newLinksFile, audioOnly, authenticate)
		
	def processPlaylist(self):
		if self.extractOnly.get():
			print("extracting playlist: "+str(self.playlist.get()))
		else:
			print("downloading playlist: "+str(self.playlist.get()))
			#self.audioOnly.get()
		
	def processChannel(self):
		if self.extractOnly.get():
			print("extracting channel: "+str(self.channel.get()))
		else:
			print("downloading channel: "+str(self.channel.get()))
			#self.audioOnly.get()
		
	def processFile(self):
		print("download selected extracted Links")
		
	def processAllFiles(self):
		print("download all extracted Links")
		
	def promptSelection(self):
		print("running")
		title = "my title"
		message = "my message"
		windowPopUp(title, message)

class windowPopUp(tk.Toplevel):
	
	def __init__(self, title, message):
		tk.Toplevel.__init__(self)
		self.title(title)
		self.geometry('350x75')
		self.minsize(350, 75)
		self.maxsize(425, 250)
		self.rowconfigure(0, weight=0)
		self.rowconfigure(1, weight=1)
		self.columnconfigure(0, weight=1)

		button_frame = tk.Frame(self)
		button_frame.grid(row=0, column=0, sticky='nsew')
		button_frame.columnconfigure(0, weight=1)
		button_frame.columnconfigure(1, weight=1)

		ttk.Label(button_frame, text=message).grid(row=0, column=0, columnspan=2, pady=(7, 7))
		ttk.Button(button_frame, text='OK', command=self.destroy).grid(row=1, column=0, sticky='e')
		ttk.Button(button_frame, text='Details', command=self.selectDuplicates).grid(row=1, column=1, sticky='w')
	
	@staticmethod
	def selectDuplicates():
		print("test")

if __name__ == '__main__':
	App = Gui().mainloop()

'''
url = "https://www.youtube.com/@wavemusic"
"browseId":"UCbuK8xxu2P_sqoMnDsoBrrg"
"https://www.youtube.com/playlist?list=UU"+"buK8xxu2P_sqoMnDsoBrrg"

url = "https://www.youtube.com/@AirwaveMusicTV/videos"
"browseId":"UCwIgPuUJXuf2nY-nKsEvLOg"
"https://www.youtube.com/playlist?list=UU"+"wIgPuUJXuf2nY-nKsEvLOg"
'''
